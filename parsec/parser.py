from dataclasses import dataclass
from typing import Callable, cast, Any, Iterable, Unpack, overload
from functools import reduce

from parsec.context import Context
from parsec.err import ParseErr, Expected, UnExpected, EOSErr
from parsec.utils import true, false, cons


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

    def define(self, p: "Parser[I, R]"):
        self._fn: Callable[[Context[I]], Result[I, R]] | None = lambda ctx: p.run(ctx)

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

    def __and__[S, *TS](self, p: "Parser[I, S]"):
        def _flat_(t: tuple[Any, Any]) -> tuple[Any, ...]:
            if isinstance(t[0], tuple):
                return (*cast(tuple[Any, ...], t[0]), t[1])
            return t

        return self.pair(p).map(_flat_)

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
                case Okay(value=v):
                    r2 = fn(v).run(r1.context)
                    r2.consumed += r1.consumed
                    return r2
                case Fail(error=e):
                    return Result[I, S].fail(r1.context, e, r1.consumed)

        return parse

    def map[S](self, fn: Callable[[R], S]) -> "Parser[I, S]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, S]:
            r = self.run(ctx)
            match r.outcome:
                case Okay(value=v):
                    return Result[I, S].okay(r.context, fn(v), r.consumed)
                case Fail(error=e):
                    return Result[I, S].fail(r.context, e, r.consumed)

        return parse

    def apply[S](self, pfn: "Parser[I, Callable[[R], S]]") -> "Parser[I, S]":
        return pfn.bind(self.map)

    def alter(self, p: "Parser[I, R]") -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]):
            r1 = self.run(ctx)
            if isinstance(r1.outcome, Okay):
                return r1
            ctx = r1.context.backtrack(r1.consumed, ctx.state)
            r2 = p.run(ctx)
            if isinstance(r2.outcome, Okay):
                return r2
            ctx = r2.context.backtrack(r2.consumed, ctx.state)
            children = [r1.outcome.error, r2.outcome.error]
            return Result[I, R].fail(ctx, ParseErr(children), 0)

        return parse

    def fast_alter(self, p: "Parser[I, R]") -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]):
            r = self.run(ctx)
            if r.consumed > 0 or isinstance(r.outcome, Okay):
                return r
            return p.run(r.context)

        return parse

    def pair[S](self, p: "Parser[I, S]") -> "Parser[I, tuple[R, S]]":
        return p.apply(self.map(lambda x: lambda y: (x, y)))

    def otherwise[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        p1 = self.as_type(type[R | S])
        p2 = p.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.alter(p2))

    def fast_otherwise[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        p1 = self.as_type(type[R | S])
        p2 = p.as_type(type[R | S])
        return cast(Parser[I, R | S], p1.fast_alter(p2))

    def maybe(self) -> "Parser[I, R | None]":
        return self.default(None)

    def default[U](self, value: U) -> "Parser[I, R | U]":
        return self.otherwise(Parser[I, R | U].okay(value))

    def prefix(self, _prefix: "Parser[I, Any]") -> "Parser[I, R]":
        return self.apply(_prefix.map(false))

    def suffix(self, _suffix: "Parser[I, Any]") -> "Parser[I, R]":
        return _suffix.apply(self.map(true))

    def between(
        self, _prefix: "Parser[I, Any]", _suffix: "Parser[I, Any]"
    ) -> "Parser[I, R]":
        return self.prefix(_prefix).suffix(_suffix)

    def ltrim(self, ignore: "Parser[I, Any]") -> "Parser[I, R]":
        return self.prefix(ignore.many())

    def rtrim(self, ignore: "Parser[I, Any]") -> "Parser[I, R]":
        return self.suffix(ignore.many())

    def trim(self, ignore: "Parser[I, Any]") -> "Parser[I, R]":
        return self.ltrim(ignore).rtrim(ignore)

    def sep_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        remains = self.prefix(sep).many()
        return remains.apply(self.map(cons))

    def end_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return self.suffix(sep).many()

    def many_till(self, end: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return self.many().suffix(end)

    def repeat(self, n: int) -> "Parser[I, list[R]]":
        if n == 0:
            return Parser[I, list[R]].okay([])
        return self.repeat(n - 1).apply(self.map(cons))

    def where(self, fn: Callable[[R], bool]) -> "Parser[I, R]":
        return self.bind(
            lambda v: Parser[I, R].okay(v)
            if fn(v)
            else Parser[I, R].fail(UnExpected(v))
        )

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
        def rest(x: R) -> Parser[I, R]:
            return op.bind(lambda f: self.bind(lambda y: rest(f(x)(y)))).alter(
                Parser[I, R].okay(x)
            )

        scan = self.bind(lambda x: rest(x))
        return scan

    def chainr1(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]"
    ) -> "Parser[I, R]":
        def scan() -> Parser[I, R]:
            return self.bind(
                lambda x: op.bind(lambda f: scan().map(lambda y: f(x)(y))).alter(
                    Parser[I, R].okay(x)
                )
            )

        return scan()

    def chainl(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        return self.chainl1(op).alter(Parser[I, R].okay(initial))

    def chainr(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        return self.chainr1(op).alter(Parser[I, R].okay(initial))

    def as_type[S](self, _: type[S]) -> "Parser[I, S]":
        return cast(Parser[I, S], self)

    def with_err(self, err: ParseErr) -> "Parser[I, R]":
        @Parser
        def parse(ctx: Context[I]) -> Result[I, R]:
            ret = self.run(ctx)
            if isinstance(ret.outcome, Okay):
                return ret
            err.add(ret.outcome.error)
            return Result[I, R].fail(ctx, err, ret.consumed)

        return parse


@Parser
def item[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, EOSErr(), 0)
    return Result[I, I].okay(
        ctx.update(ctx.stream.peek().pop()), ctx.stream.read().pop(), 1
    )


@Parser
def look[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, EOSErr(), 0)
    return Result[I, I].okay(ctx, ctx.stream.peek().pop(), 0)


token = item.eq


def tokens[I](values: Iterable[I]):
    ps = [token(v) for v in values]
    return reduce(
        lambda p1, p2: p1.pair(p2).map(lambda x: [*x[0], x[1]]),
        ps,
        Parser[I, list[I]].okay([]),
    )
