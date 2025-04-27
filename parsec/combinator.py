from functools import reduce
from typing import Iterable, overload, Any, Callable

from parsec.utils import curry
from parsec.parser import Parser


@curry
def bind[I, R, S](fn: Callable[[R], Parser[I, S]], p: Parser[I, R]) -> Parser[I, S]:
    return p.bind(fn)


@curry
def fmap[I, R, S](fn: Callable[[R], S], p: Parser[I, R]) -> Parser[I, S]:
    return p.map(fn)


@curry
def apply[I, R, S](pfn: Parser[I, Callable[[R], S]], p: Parser[I, R]) -> Parser[I, S]:
    return p.apply(pfn)


def alter[I, R](p1: Parser[I, R], p2: Parser[I, R]) -> Parser[I, R]:
    return p1.alter(p2)


def pair[I, R, S](p1: Parser[I, R], p2: Parser[I, S]) -> Parser[I, tuple[R, S]]:
    return p1.pair(p2)


def otherwise[I, R, S](p1: Parser[I, R], p2: Parser[I, S]) -> Parser[I, R | S]:
    return p1.otherwise(p2)


@curry
def maybe[I, R](p: Parser[I, R]) -> Parser[I, R | None]:
    return p.maybe()


@curry
def default[I, R, S](value: S, p: Parser[I, R]) -> Parser[I, R | S]:
    return p.default(value)


@curry
def prefix[I, R](_prefix: Parser[I, Any], p: Parser[I, R]) -> Parser[I, R]:
    return p.prefix(_prefix)


@curry
def suffix[I, R](_suffix: Parser[I, Any], p: Parser[I, R]) -> Parser[I, R]:
    return p.suffix(_suffix)


@curry
def between[I, R](
    left: Parser[I, Any], right: Parser[I, Any], p: Parser[I, R]
) -> Parser[I, R]:
    return p.between(left, right)


@curry
def ltrim[I, R](ignore: Parser[I, Any], p: Parser[I, R]) -> Parser[I, R]:
    return p.ltrim(ignore)


@curry
def rtrim[I, R](ignore: Parser[I, Any], p: Parser[I, R]) -> Parser[I, R]:
    return p.rtrim(ignore)


@curry
def trim[I, R](ignore: Parser[I, Any], p: Parser[I, R]) -> Parser[I, R]:
    return p.trim(ignore)


@curry
def sep_by[I, R](sep: Parser[I, Any], p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.sep_by(sep)


@curry
def end_by[I, R](sep: Parser[I, Any], p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.end_by(sep)


@curry
def many_till[I, R](end: Parser[I, Any], p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.many_till(end)


@curry
def repeat[I, R](n: int, p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.repeat(n)


@curry
def where[I, R](fn: Callable[[R], bool], p: Parser[I, R]) -> Parser[I, R]:
    return p.where(fn)


@curry
def eq[I, R](value: R, p: Parser[I, R]) -> Parser[I, R]:
    return p.eq(value)


@curry
def neq[I, R](value: R, p: Parser[I, R]) -> Parser[I, R]:
    return p.neq(value)


@curry
def range[I, R](ranges: Iterable[R], p: Parser[I, R]) -> Parser[I, R]:
    return p.range(ranges)


@curry
def some[I, R](p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.some()


@curry
def many[I, R](p: Parser[I, R]) -> Parser[I, list[R]]:
    return p.many()


@curry
def chainl1[I, R](
    op: Parser[I, Callable[[R], Callable[[R], R]]], p: Parser[I, R]
) -> Parser[I, R]:
    return p.chainl1(op)


@curry
def chainr1[I, R, S](
    op: Parser[I, Callable[[R], Callable[[R], R]]], p: Parser[I, R]
) -> Parser[I, R]:
    return p.chainr1(op)


@curry
def chainl[I, R](
    op: Parser[I, Callable[[R], Callable[[R], R]]], initial: R, p: Parser[I, R]
) -> Parser[I, R]:
    return p.chainl(op, initial)


@curry
def chainr[I, R](
    op: Parser[I, Callable[[R], Callable[[R], R]]], initial: R, p: Parser[I, R]
) -> Parser[I, R]:
    return p.chainr(op, initial)


@curry
def as_type[I, R, S](tp: type[S], p: Parser[I, R]) -> Parser[I, S]:
    return p.as_type(tp)


@curry
def label[I, R](value: str, p: Parser[I, R]) -> Parser[I, R]:
    return p.label(value)


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
    return reduce(lambda x, y: x | y, plist)


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
    return reduce(lambda x, y: x & y, plist)
