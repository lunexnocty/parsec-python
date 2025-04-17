from functools import reduce
from typing import Iterable, overload, Any, Callable, cast
import typing

from parsec.utils import const, curry, make_pair, true, false
from parsec.context import Context, Result, Okay, Fail
from parsec.err import ParseErr, UnExpected, Expected, EOSError

if typing.TYPE_CHECKING:
    from parsec.parser import Parser, Result


@curry
def run_parser[I, R](ctx: Context[I], p: Parser[I, R]) -> Result[I, R]:
    return p.run(ctx)


@curry
def fbind[I, R, S](
    fn: Callable[[R], "Parser[I, S]"], p: Parser[I, R]
) -> "Parser[I, S]":
    return p.bind(fn)


@curry
def fmap[I, R, S](fn: Callable[[R], S], p: Parser[I, R]) -> "Parser[I, S]":
    return p.map(fn)


@curry
def fapply[I, R, S](
    pfn: "Parser[I, Callable[[R], S]]", p: Parser[I, R]
) -> "Parser[I, S]":
    return pfn.bind(p.map)


@curry
def alter[I, R](p1: "Parser[I, R]", p2: "Parser[I, R]") -> "Parser[I, R]":
    @Parser
    def parse(ctx: Context[I]) -> Result[I, R]:
        r1 = p1.run(ctx)
        match r1.outcome:
            case Okay():
                return r1
            case Fail():
                ctx = r1.context.backtrack(r1.consumed, ctx.state)
                r2 = p2.run(ctx)
                match r2.outcome:
                    case Okay():
                        return r2
                    case Fail():
                        ctx = r2.context.backtrack(r2.consumed, ctx.state)
                        children = [r1.outcome.error, r2.outcome.error]
                        return Result[I, R].fail(ctx, ParseErr(children), 0)

    return parse


@curry
def fast_alter[I, R](p1: Parser[I, R], p2: Parser[I, R]) -> Parser[I, R]:
    @Parser
    def parse(ctx: Context[I]) -> Result[I, R]:
        ret = p1.run(ctx)
        match ret.outcome:
            case Okay():
                return ret
            case Fail():
                return p2.run(ctx) if ret.consumed == 0 else ret

    return parse


@curry
def pair[I, R, S](p1: Parser[I, R], p2: Parser[I, S]) -> Parser[I, tuple[R, S]]:
    return fapply(p1.map(make_pair))(p2)


@curry
def otherwise[I, R, S](p1: Parser[I, R], p2: Parser[I, S]) -> Parser[I, R | S]:
    _p1 = p1.as_type(type[R | S])
    _p2 = p2.as_type(type[R | S])
    return cast(Parser[I, R | S], alter(_p1)(_p2))


@curry
def fast_otherwise[I, R, S](p1: Parser[I, R], p2: Parser[I, S]) -> Parser[I, R | S]:
    _p1 = p1.as_type(type[R | S])
    _p2 = p2.as_type(type[R | S])
    return cast(Parser[I, R | S], fast_alter(_p1)(_p2))


@curry
def maybe[I, R](p: Parser[I, R]) -> Parser[I, R | None]:
    return default(None)(p)


@curry
def default[I, R, S](value: S, p: Parser[I, R]) -> Parser[I, R | S]:
    return otherwise(p)(Parser[I, R | S].okay(value))


@curry
def prefix[I, R](_prefix: "Parser[I, Any]", p: Parser[I, R]) -> "Parser[I, R]":
    return fapply(_prefix.map(false))(p)


@curry
def suffix[I, R](_suffix: "Parser[I, Any]", p: Parser[I, R]) -> "Parser[I, R]":
    return p.map(true).apply(_suffix)


@curry
def between[I, R](
    _prefix: "Parser[I, Any]", _suffix: "Parser[I, Any]", p: Parser[I, R]
) -> "Parser[I, R]":
    return suffix(_suffix)(prefix(_prefix)(p))


@curry
def ltrim[I, R](ignores: set["Parser[I, Any]"], p: Parser[I, R]) -> "Parser[I, R]":
    return prefix(many(sel(*ignores)))(p)


@curry
def rtrim[I, R](ignores: set["Parser[I, Any]"], p: Parser[I, R]) -> "Parser[I, R]":
    return suffix(many(sel(*ignores)))(p)


@curry
def trim[I, R](ignores: set["Parser[I, Any]"], p: Parser[I, R]) -> "Parser[I, R]":
    return rtrim(ignores)(ltrim(ignores)(p))


@curry
def sep_by[I, R](sep: "Parser[I, Any]", p: Parser[I, R]) -> "Parser[I, list[R]]":
    return p.bind(lambda x: many(sep.bind(const(p))).map(lambda xs: [x, *xs]))


@curry
def end_by[I, R](sep: "Parser[I, Any]", p: Parser[I, R]) -> "Parser[I, list[R]]":
    return some(suffix(sep)(p))


@curry
def many_till[I, R](end: "Parser[I, Any]", p: Parser[I, R]) -> "Parser[I, list[R]]":
    return suffix(end)(many(p))


@curry
def repeat[I, R](n: int, p: Parser[I, R]) -> "Parser[I, list[R]]":
    if n == 0:
        return Parser[I, list[R]].okay([])
    return p.bind(lambda x: p.repeat(n - 1).map(lambda xs: [x, *xs]))


@curry
def where[I, R](fn: Callable[[R], bool], p: Parser[I, R]) -> "Parser[I, R]":
    return p.bind(
        lambda x: Parser[I, R].okay(x) if fn(x) else Parser[I, R].fail(UnExpected(x))
    )


@curry
def eq[I, R](value: R, p: Parser[I, R]) -> "Parser[I, R]":
    return with_error(Expected(f"'{value}'"))(where(lambda v: v == value)(p))


@curry
def neq[I, R](value: R, p: Parser[I, R]) -> "Parser[I, R]":
    return with_error(UnExpected(f"'{value}'"))(where(lambda v: v != value)(p))


@curry
def range[I, R](ranges: set[R], p: Parser[I, R]) -> "Parser[I, R]":
    return where(lambda v: v in ranges)(p)


@curry
def some[I, R](p: Parser[I, R]) -> "Parser[I, list[R]]":
    return p.bind(lambda x: many(p).map(lambda xs: [x, *xs]))


@curry
def many[I, R](p: Parser[I, R]) -> "Parser[I, list[R]]":
    return alter(some(p))(Parser[I, list[R]].okay([]))


@curry
def chainl1[I, R](
    op: "Parser[I, Callable[[R], Callable[[R], R]]]", p: Parser[I, R]
) -> "Parser[I, R]":
    return p.bind(lambda x: chainl(op)(x)(p))


@curry
def chainr1[I, R, S](
    op: "Parser[I, Callable[[R], Callable[[R], R]]]", p: Parser[I, R]
) -> "Parser[I, R]":
    return p.bind(lambda x: chainr(op)(x)(p))


@curry
def chainl[I, R](
    op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R, p: Parser[I, R]
) -> "Parser[I, R]":
    def rest(x: R) -> Parser[I, R]:
        return alter(op.bind(lambda f: p.bind(lambda y: rest(f(x)(y)))))(
            Parser[I, R].okay(initial)
        )

    return p.bind(rest)


@curry
def chainr[I, R](
    op: "Parser[I, Callable[[R], Callable[[R], R]]]", initial: R, p: Parser[I, R]
) -> "Parser[I, R]":
    def rest(x: R) -> Parser[I, R]:
        return alter(op.bind(lambda f: scan.bind(lambda y: rest(f(x)(y)))))(
            Parser[I, R].okay(initial)
        )

    scan = p.bind(rest)
    return scan


@curry
def as_type[I, R, S](tp: type[S], p: Parser[I, R]) -> "Parser[I, S]":
    return cast(Parser[I, S], p)


@curry
def with_error[I, R](error: ParseErr, p: Parser[I, R]) -> "Parser[I, R]":
    @Parser
    def parse(ctx: Context[I]) -> Result[I, R]:
        ret = p.run(ctx)
        match ret.outcome:
            case Okay():
                return ret
            case Fail(error=err):
                error.children.append(err)
                return Result[I, R].fail(ret.context, err, ret.consumed)

    return parse


@overload
def sel[I, R1, R2](_p1: Parser[I, R1], _p2: Parser[I, R2]) -> Parser[I, R1 | R2]: ...


@overload
def sel[I, R1, R2, R3](
    _p1: Parser[I, R1], _p2: Parser[I, R2], _p3: Parser[I, R3]
) -> Parser[I, R1 | R2 | R3]: ...


@overload
def sel[I, R1, R2, R3, R4](
    _p1: Parser[I, R1], _p2: Parser[I, R2], _p3: Parser[I, R3], _p4: Parser[I, R4]
) -> Parser[I, R1 | R2 | R3 | R4]: ...


@overload
def sel[I, R1, R2, R3, R4, R5](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
) -> Parser[I, R1 | R2 | R3 | R4 | R5]: ...


@overload
def sel[I, R1, R2, R3, R4, R5, R6](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6]: ...


@overload
def sel[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7]: ...


@overload
def sel[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
    _p8: Parser[I, R8],
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8]: ...


@overload
def sel[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
    _p8: Parser[I, R8],
    _p9: Parser[I, R9],
) -> Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9]: ...


def sel[I](
    _p1: Parser[I, Any],
    _p2: Parser[I, Any],
    _p3: Parser[I, Any] | None = None,
    _p4: Parser[I, Any] | None = None,
    _p5: Parser[I, Any] | None = None,
    _p6: Parser[I, Any] | None = None,
    _p7: Parser[I, Any] | None = None,
    _p8: Parser[I, Any] | None = None,
    _p9: Parser[I, Any] | None = None,
    *_ps: Parser[I, Any],
) -> Parser[I, Any]:
    plist: list[Parser[I, Any]] = list(
        filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps))
    )
    return reduce(lambda x, y: otherwise(x)(y), plist)


@overload
def seq[I, R1, R2](
    _p1: Parser[I, R1], _p2: Parser[I, R2]
) -> Parser[I, tuple[R1, R2]]: ...


@overload
def seq[I, R1, R2, R3](
    _p1: Parser[I, R1], _p2: Parser[I, R2], _p3: Parser[I, R3]
) -> Parser[I, tuple[R1, R2, R3]]: ...


@overload
def seq[I, R1, R2, R3, R4](
    _p1: Parser[I, R1], _p2: Parser[I, R2], _p3: Parser[I, R3], _p4: Parser[I, R4]
) -> Parser[I, tuple[R1, R2, R3, R4]]: ...


@overload
def seq[I, R1, R2, R3, R4, R5](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
) -> Parser[I, tuple[R1, R2, R3, R4, R5]]: ...


@overload
def seq[I, R1, R2, R3, R4, R5, R6](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6]]: ...


@overload
def seq[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7]]: ...


@overload
def seq[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
    _p8: Parser[I, R8],
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8]]: ...


@overload
def seq[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: Parser[I, R1],
    _p2: Parser[I, R2],
    _p3: Parser[I, R3],
    _p4: Parser[I, R4],
    _p5: Parser[I, R5],
    _p6: Parser[I, R6],
    _p7: Parser[I, R7],
    _p8: Parser[I, R8],
    _p9: Parser[I, R9],
) -> Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8, R9]]: ...


def seq[I](
    _p1: Parser[I, Any],
    _p2: Parser[I, Any],
    _p3: Parser[I, Any] | None = None,
    _p4: Parser[I, Any] | None = None,
    _p5: Parser[I, Any] | None = None,
    _p6: Parser[I, Any] | None = None,
    _p7: Parser[I, Any] | None = None,
    _p8: Parser[I, Any] | None = None,
    _p9: Parser[I, Any] | None = None,
    *_ps: Parser[I, Any],
):
    plist: list[Parser[I, Any]] = list(
        filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps))
    )
    return reduce(lambda x, y: pair(x)(y), plist)


@Parser
def item[I](ctx: Context[I]) -> Result[I, I]:
    if ctx.stream.eos():
        return Result[I, I].fail(ctx, EOSError(), 0)
    return Result[I, I].okay(
        ctx.update(ctx.stream.peek().pop()), ctx.stream.read().pop(), 1
    )


token = item.eq


def tokens[I](values: Iterable[I]) -> Parser[I, tuple[I, ...]]:
    return seq(*[token(v) for v in values])
