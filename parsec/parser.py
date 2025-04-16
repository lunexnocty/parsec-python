from dataclasses import dataclass
from typing import Callable, cast, Any, Iterable, Unpack, overload
from functools import reduce

from parsec.context import Context
from parsec.err import ParseErr, AlterErr, Expected, UnExpected, EOS


@dataclass
class Okay[R]:
    value: R


@dataclass
class Fail:
    error: ParseErr


@dataclass
class Result[I, R]:
    context: Context[I]
    outcome: Okay[R] | Fail
    consumed: int

    @classmethod
    def okay(cls, ctx: Context[I], value: R, consumed: int):
        return cls(ctx, Okay(value), consumed)

    @classmethod
    def fail(cls, ctx: Context[I], error: ParseErr, consumed: int):
        return cls(ctx, Fail(error), consumed)


class Parser[I, R]:
    def __init__(self, fn: Callable[[Context[I]], Result[I, R]] | None = None):
        self._fn = fn

    def define(self, parser: "Parser[I, R]"):
        self._fn = lambda ctx: parser.run(ctx)

    def run(self, ctx: Context[I]) -> Result[I, R]:
        if self._fn is None:
            raise RuntimeError("UnDefined Parser")
        return self._fn(ctx)

    def __rshift__[S](self, fn: Callable[[R], "Parser[I, S]"]) -> "Parser[I, S]":
        return self.bind(fn)

    def __or__[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        return self.otherwise(p)

    @overload
    def __and__[S, *TS](
        self: "Parser[I, tuple[Unpack[TS]]]", p: "Parser[I, S]"
    ) -> "Parser[I, tuple[Unpack[TS], S]]": ...

    @overload
    def __and__[S](self, p: "Parser[I, S]") -> "Parser[I, tuple[R, S]]": ...

    def __and__[S](self, p: "Parser[I, S]"):
        def flatten(
            t: tuple[Any, S],
        ) -> tuple[Any, ...]:
            left, right = t
            if isinstance(left, tuple):
                return (*left, right)
            else:
                return (left, right)

        return self.pair(p).map(flatten)

    def __lshift__[S](
        self, fn: Callable[["Parser[I, R]"], "Parser[I, S]"]
    ) -> "Parser[I, S]":
        return fn(self)

    @classmethod
    def okay(cls, value: R) -> "Parser[I, R]":
        return cls(lambda ctx: Result[I, R].okay(ctx, value, 0))

    @classmethod
    def fail(cls, error: ParseErr) -> "Parser[I, R]":
        return cls(lambda ctx: Result[I, R].fail(ctx, error, 0))

    def bind[S](self, fn: Callable[[R], "Parser[I, S]"]) -> "Parser[I, S]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, S]:
            r1 = self.run(ctx)
            match r1.outcome:
                case Okay(value=v1):
                    r2 = fn(v1).run(r1.context)
                    consumed = r1.consumed + r2.consumed
                    match r2.outcome:
                        case Okay(value=v2):
                            return Result[I, S].okay(r2.context, v2, consumed)
                        case Fail(error=err):
                            return Result[I, S].fail(r2.context, err, consumed)
                case Fail(error=err):
                    return Result[I, S].fail(r1.context, err, r1.consumed)

        return parse

    def map[S](self, fn: Callable[[R], S]) -> "Parser[I, S]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, S]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Okay):
                return Result(ret.context, Okay(fn(ret.outcome.value)), ret.consumed)
            return Result(ret.context, ret.outcome, ret.consumed)

        return parse

    def apply[S](self, pfn: "Parser[I, Callable[[R], S]]") -> "Parser[I, S]":
        return pfn.bind(self.map)

    def alter(self, parser: "Parser[I, R]", backtrace: bool = True) -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]):
            r1 = self.run(ctx)
            if isinstance(r1.outcome, Okay):
                return r1
            if not backtrace:
                return r1 if r1.consumed > 0 else parser.run(r1.context)
            ctx = r1.context.backtrack(r1.consumed, ctx.state)
            r2 = parser.run(ctx)
            if isinstance(r2.outcome, Okay):
                return r2
            ctx = r2.context.backtrack(r2.consumed, ctx.state)
            children = [r1.outcome.error, r2.outcome.error]
            return Result[I, R].fail(ctx, AlterErr(children), 0)

        return parse

    def pair[S](self, parser: "Parser[I, S]") -> "Parser[I, tuple[R, S]]":
        return self.bind(lambda x: parser.map(lambda y: (x, y)))

    def otherwise[S](self, parser: "Parser[I, S]") -> "Parser[I, R | S]":
        p1 = self.as_type(type[R | S])
        p2 = parser.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.alter(p2))

    def maybe(self) -> "Parser[I, R | None]":
        return self.default(None)

    def default[U](self, value: U) -> "Parser[I, R | U]":
        return self.otherwise(Parser[I, R | U].okay(value))

    def prefix(self, _prefix: "Parser[I, Any]") -> "Parser[I, R]":
        return _prefix.pair(self).map(lambda x: x[1])

    def suffix(self, _suffix: "Parser[I, Any]") -> "Parser[I, R]":
        return self.pair(_suffix).map(lambda x: x[0])

    def between(
        self, left: "Parser[I, Any]", right: "Parser[I, Any]"
    ) -> "Parser[I, R]":
        return self.prefix(left).suffix(right)

    def ltrim(self, ignores: Iterable["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.prefix(sel(*ignores).many())

    def rtrim(self, ignores: Iterable["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.suffix(sel(*ignores).many())

    def trim(self, ignores: Iterable["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.ltrim(ignores).rtrim(ignores)

    def sep_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        remains = self.prefix(sep).many()
        return self.bind(lambda x: remains.map(lambda xs: [x, *xs]))

    def end_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return self.suffix(sep).many()

    def many_till(self, end: "Parser[I, Any]") -> "Parser[I, list[R]]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, list[R]]:
            return (
                end.map(lambda _: [])
                .alter(parse.apply(self.map(lambda x: lambda xs: [x, *xs])))
                .run(ctx)
            )

        return parse

    def repeat(self, n: int) -> "Parser[I, list[R]]":
        if n == 0:
            return Parser[I, list[R]].okay([])
        return self.bind(lambda x: self.repeat(n - 1).map(lambda xs: [x, *xs]))

    def where(self, fn: Callable[[R], bool]) -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Fail):
                return ret
            if fn(ret.outcome.value):
                return ret
            return Result[I, R].fail(ctx, UnExpected(ret.outcome.value), ret.consumed)

        return parse

    def eq(self, value: R) -> "Parser[I, R]":
        return self.where(lambda v: v == value).expected(f"{value}")

    def neq(self, value: R) -> "Parser[I, R]":
        return self.where(lambda v: v != value)

    def range(self, ranges: Iterable[R]) -> "Parser[I, R]":
        return self.where(lambda v: v in ranges)

    def some(self) -> "Parser[I, list[R]]":
        return self.bind(lambda x: self.many().map(lambda xs: [x, *xs]))

    def many(self) -> "Parser[I, list[R]]":
        return self.some().alter(Parser[I, list[R]].okay([]))

    def chainl1(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]"
    ) -> "Parser[I, R]":
        return self.bind(lambda x: self.chainl(op, x))

    def chainr1(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]"
    ) -> "Parser[I, R]":
        return self.bind(lambda x: self.chainr(op, x))

    def chainl(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        def rest(x: R) -> Parser[I, R]:
            return op.bind(lambda f: self.bind(lambda y: rest(f(x)(y)))).alter(
                Parser[I, R].okay(initial)
            )

        return self.bind(lambda x: rest(x))

    def chainr(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        scan = self.bind(lambda x: rest(x))

        def rest(x: R) -> Parser[I, R]:
            return op.bind(lambda f: scan.map(lambda y: f(x)(y))).alter(
                Parser[I, R].okay(initial)
            )

        return scan

    def as_type[S](self, tp: type[S]) -> "Parser[I, S]":
        return cast(Parser[I, S], self)

    def expected[S](self, value: S) -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Okay):
                return ret
            return Result[I, R].fail(
                ctx, Expected(value, [ret.outcome.error]), ret.consumed
            )

        return parse


@Parser
def item[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, EOS(), 0)
    return Result[I, I].okay(
        ctx.update(ctx.stream.peek().pop()), ctx.stream.read().pop(), 1
    )


token = item.eq


def tokens[I](values: Iterable[I]) -> Parser[I, list[I]]:
    return seq(*map(token, values))


def sel[I, R](*parsers: Parser[I, R]) -> Parser[I, R]:
    return reduce(Parser[I, R].alter, parsers)


def seq[I, R](*parsers: Parser[I, R]) -> Parser[I, list[R]]:
    return reduce(
        lambda ps, p: ps.pair(p).map(lambda x: [*x[0], x[1]]),
        parsers,
        Parser[I, list[R]].okay([]),
    )
