from typing import Callable, Any, Unpack, overload

from parsec.context import Context, Result, Okay, Fail
from parsec.err import ParseErr
from parsec import combinator as C
from parsec.utils import flatten


class Parser[I, R]:
    def __init__(self, fn: Callable[[Context[I]], Result[I, R]] | None = None):
        self._fn = fn

    @classmethod
    def okay(cls, value: R) -> "Parser[I, R]":
        return cls(lambda ctx: Result[I, R].okay(ctx, value, 0))

    @classmethod
    def fail(cls, error: ParseErr) -> "Parser[I, R]":
        return cls(lambda ctx: Result[I, R].fail(ctx, error, 0))

    def define(self, p: "Parser[I, R]"):
        self._fn = lambda ctx: p.run(ctx)

    def run(self, ctx: Context[I]) -> Result[I, R]:
        if self._fn is None:
            raise RuntimeError("UnDefined Parser")
        return self._fn(ctx)

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
            ret = C.run_parser(ctx)(self)
            match ret.outcome:
                case Okay(value=v):
                    return Result[I, S].okay(ret.context, fn(v), ret.consumed)
                case Fail(error=err):
                    return Result[I, S].fail(ret.context, err, ret.consumed)

        return parse

    def apply[S](
        self: "Parser[I, Callable[[R], S]]", p: "Parser[I, R]"
    ) -> "Parser[I, S]":
        return C.fapply(self)(p)

    # 解析器运算符
    def __rshift__[S](self, fn: Callable[[R], "Parser[I, S]"]) -> "Parser[I, S]":
        return self.bind(fn)

    def __lshift__[S](
        self, fn: Callable[["Parser[I, R]"], "Parser[I, S]"]
    ) -> "Parser[I, S]":
        """管道运算符，连续的将组合子应用在解析器上"""
        return fn(self)

    def __matmul__[S](self, fn: Callable[[R], S]) -> "Parser[I, S]":
        return self.map(fn)

    def __truediv__[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        return C.fast_otherwise(self)(p)

    def __or__[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        return C.otherwise(self)(p)

    @overload
    def __and__[S, *TS](
        self: "Parser[I, tuple[Unpack[TS]]]", p: "Parser[I, S]"
    ) -> "Parser[I, tuple[Unpack[TS], S]]": ...

    @overload
    def __and__[S](self, p: "Parser[I, S]") -> "Parser[I, tuple[R, S]]": ...

    def __and__[S](self, p: "Parser[I, S]"):
        return C.pair(self)(p).map(flatten)

    # 链式调用接口，在combinator中实现
    def alter(self, p: "Parser[I, R]") -> "Parser[I, R]":
        return C.alter(self)(p)

    def fast_alter(self, p: "Parser[I, R]") -> "Parser[I, R]":
        return C.fast_alter(self)(p)

    def pair[S](self, p: "Parser[I, S]") -> "Parser[I, tuple[R, S]]":
        return C.pair(self)(p)

    def otherwise[S](self, p: "Parser[I, S]") -> "Parser[I, R | S]":
        return C.otherwise(self)(p)

    def maybe(self) -> "Parser[I, R | None]":
        return C.maybe(self)

    def default[S](self, value: S) -> "Parser[I, R | S]":
        return C.default(value)(self)

    def prefix(self, _prefix: "Parser[I, Any]") -> "Parser[I, R]":
        return C.prefix(_prefix)(self)

    def suffix(self, _suffix: "Parser[I, Any]") -> "Parser[I, R]":
        return C.suffix(_suffix)(self)

    def between(
        self, left: "Parser[I, Any]", right: "Parser[I, Any]"
    ) -> "Parser[I, R]":
        return C.between(left)(right)(self)

    def ltrim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return C.ltrim(ignores)(self)

    def rtrim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return C.rtrim(ignores)(self)

    def trim(self, ignores: set["Parser[I, Any]"]) -> "Parser[I, R]":
        return C.trim(ignores)(self)

    def sep_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return C.sep_by(sep)(self)

    def end_by(self, sep: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return C.end_by(sep)(self)

    def many_till(self, end: "Parser[I, Any]") -> "Parser[I, list[R]]":
        return C.many_till(end)(self)

    def repeat(self, n: int) -> "Parser[I, list[R]]":
        return C.repeat(n)(self)

    def where(self, fn: Callable[[R], bool]) -> "Parser[I, R]":
        return C.where(fn)(self)

    def eq(self, value: R) -> "Parser[I, R]":
        return C.eq(value)(self)

    def neq(self, value: R) -> "Parser[I, R]":
        return C.neq(value)(self)

    def range(self, ranges: set[R]) -> "Parser[I, R]":
        return C.range(ranges)(self)

    def some(self) -> "Parser[I, list[R]]":
        return C.some(self)

    def many(self) -> "Parser[I, list[R]]":
        return C.many(self)

    def chainl1(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]"
    ) -> "Parser[I, R]":
        return C.chainl1(op)(self)

    def chainr1(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]"
    ) -> "Parser[I, R]":
        return C.chainr1(op)(self)

    def chainl(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        return C.chainl(op)(initial)(self)

    def chainr(
        self, op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R
    ) -> "Parser[I, R]":
        return C.chainr(op)(initial)(self)

    def as_type[S](self, tp: type[S]) -> "Parser[I, S]":
        return C.as_type(tp)(self)

    def with_error(self, error: ParseErr) -> "Parser[I, R]":
        return C.with_error(error)(self)
