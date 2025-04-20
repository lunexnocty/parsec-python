from dataclasses import dataclass
from typing import Callable, cast, Any, Iterable, Unpack, overload
from functools import reduce

from parsec.context import Context
from parsec.err import ParseErr, Expected, UnExpected, EOSErr
from parsec.utils import true, false, fst, snd, cons, identity, const


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
    
    def __truediv__[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        return self.fast_otherwise(p)

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
            if isinstance(r1.outcome, Fail):
                return r1
            r2 = fn(r1.outcome.value).run(r1.context)
            r2.consumed += r1.consumed
            return r2

        return parse

    def map[S](self, fn: Callable[[R], S]) -> "Parser[I, S]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, S]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Fail):
                return ret
            return Result[I, S].okay(ret.context, fn(ret.outcome.value), ret.consumed)

        return parse

    def apply[S](self, pfn: "Parser[I, Callable[[R], S]]") -> "Parser[I, S]":
        return pfn.bind(self.map)

    def alter(self, parser: "Parser[I, R]") -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]):
            r1 = self.run(ctx)
            if isinstance(r1.outcome, Okay):
                return r1
            ctx = r1.context.backtrack(r1.consumed, ctx.state)
            r2 = parser.run(ctx)
            if isinstance(r2.outcome, Okay):
                return r2
            ctx = r2.context.backtrack(r2.consumed, ctx.state)
            children = [r1.outcome.error, r2.outcome.error]
            return Result[I, R].fail(ctx, ParseErr(children), 0)

        return parse
    
    def fast_alter(self, parser: "Parser[I, R]") -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]):
            r1 = self.run(ctx)
            if isinstance(r1.outcome, Okay):
                return r1
            return r1 if r1.consumed > 0 else parser.run(r1.context)
        return parse

    def pair[S](self, parser: "Parser[I, S]") -> "Parser[I, tuple[R, S]]":
        return self.map(lambda x: lambda y: (x, y)).apply(parser)

    def otherwise[S](self, parser: "Parser[I, S]") -> "Parser[I, R | S]":
        p1 = self.as_type(type[R | S])
        p2 = parser.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.alter(p2))
    
    def fast_otherwise[S](self, parser: "Parser[I, S]") -> "Parser[I, R | S]":
        p1 = self.as_type(type[R | S])
        p2 = parser.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.fast_alter(p2))

    def maybe(self) -> "Parser[I, R | None]":
        return self.default(None)

    def default[U](self, value: U) -> "Parser[I, R | U]":
        return self.otherwise(Parser[I, R | U].okay(value))

    def prefix(self, _prefix: "Parser[I, Any]") -> "Parser[I, R]":
        return _prefix.map(false).apply(self)
    
    def suffix(self, _suffix: "Parser[I, Any]") -> "Parser[I, R]":
        return self.map(true).apply(_suffix)

    def between(
        self, _prefix: "Parser[I, Any]", _suffix: "Parser[I, Any]"
    ) -> "Parser[I, R]":
        return self.prefix(_prefix).suffix(_suffix)

    def ltrim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.prefix(sel(*ignores).many())

    def rtrim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.suffix(sel(*ignores).many())

    def trim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return self.ltrim(ignores).rtrim(ignores)

    def sep_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        remains = self.prefix(sep).many()
        return self.map(cons).apply(remains)

    def end_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return self.suffix(sep).many()

    def many_till(self, end: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return self.many().suffix(end)

    def repeat(self, n: int) -> "Parser[I, list[R]]":
        if n == 0:
            return Parser[I, list[R]].okay([])
        return self.map(cons).apply(self.repeat(n - 1))

    def where(self, fn: Callable[[R], bool]) -> "Parser[I, R]":
        return self.bind(lambda v: Parser[I, R].okay(v) if fn(v) else Parser[I, R].fail(UnExpected(v)))

    def eq(self, value: R) -> "Parser[I, R]":
        return self.where(lambda v: v == value).with_err(Expected(f"{value}"))

    def neq(self, value: R) -> "Parser[I, R]":
        return self.where(lambda v: v != value).with_err(UnExpected(f"{value}"))

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
            return op.bind(lambda f: self.map(lambda y: rest(f(x)(y)))).alter(
                Parser[I, R].okay(initial)
            )

        return self.bind(rest)

    def chainr(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        def rest(x: R) -> Parser[I, R]:
            return op.bind(lambda f: scan.bind(lambda y: rest(f(x)(y)))).alter(
                Parser[I, R].okay(initial)
            )

        scan = self.bind(rest)
        return scan

    def as_type[S](self, tp: type[S]) -> "Parser[I, S]":
        return cast(Parser[I, S], self)

    def with_err[S](self, err: ParseErr) -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Okay):
                return ret
            err.add(ret.outcome.error)
            return Result[I, R].fail(
                ctx, err, ret.consumed
            )

        return parse


@Parser
def item[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, EOSErr(), 0)
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
