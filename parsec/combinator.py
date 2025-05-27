from functools import reduce as _reduce
from typing import Any as _Any
from typing import Callable as _Callable
from typing import Iterable as _Iterable
from typing import overload as _overload

from parsec.core import Parser as _Parser
from parsec.utils import curry as _curry


@_curry
def bind[I, R, S](fn: _Callable[[R], _Parser[I, S]], p: _Parser[I, R]) -> _Parser[I, S]:
    return p.bind(fn)


@_curry
def fmap[I, R, S](fn: _Callable[[R], S], p: _Parser[I, R]) -> _Parser[I, S]:
    return p.map(fn)


@_curry
def apply[I, R, S](pfn: _Parser[I, _Callable[[R], S]], p: _Parser[I, R]) -> _Parser[I, S]:
    return p.apply(pfn)


def alter[I, R](p1: _Parser[I, R], p2: _Parser[I, R]) -> _Parser[I, R]:
    return p1.alter(p2)


def pair[I, R, S](p1: _Parser[I, R], p2: _Parser[I, S]) -> _Parser[I, tuple[R, S]]:
    return p1.pair(p2)


def otherwise[I, R, S](p1: _Parser[I, R], p2: _Parser[I, S]) -> _Parser[I, R | S]:
    return p1.otherwise(p2)


@_curry
def maybe[I, R](p: _Parser[I, R]) -> _Parser[I, R | None]:
    return p.maybe()


@_curry
def default[I, R, S](value: S, p: _Parser[I, R]) -> _Parser[I, R | S]:
    return p.default(value)


@_curry
def prefix[I, R](_prefix: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.prefix(_prefix)


@_curry
def suffix[I, R](_suffix: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.suffix(_suffix)


@_curry
def between[I, R](left: _Parser[I, _Any], right: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.between(left, right)


@_curry
def ltrim[I, R](ignore: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.ltrim(ignore)


@_curry
def rtrim[I, R](ignore: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.rtrim(ignore)


@_curry
def trim[I, R](ignore: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.trim(ignore)


@_curry
def sep_by[I, R](sep: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.sep_by(sep)


@_curry
def end_by[I, R](sep: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.end_by(sep)


@_curry
def many_till[I, R](end: _Parser[I, _Any], p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.many_till(end)


@_curry
def repeat[I, R](n: int, p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.repeat(n)


@_curry
def where[I, R](fn: _Callable[[R], bool], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.where(fn)


@_curry
def eq[I, R](value: R, p: _Parser[I, R]) -> _Parser[I, R]:
    return p.eq(value)


@_curry
def neq[I, R](value: R, p: _Parser[I, R]) -> _Parser[I, R]:
    return p.neq(value)


@_curry
def range[I, R](ranges: _Iterable[R], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.range(ranges)


@_curry
def some[I, R](p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.some()


@_curry
def many[I, R](p: _Parser[I, R]) -> _Parser[I, list[R]]:
    return p.many()


@_curry
def chainl1[I, R](op: _Parser[I, _Callable[[R], _Callable[[R], R]]], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.chainl1(op)


@_curry
def chainr1[I, R, S](op: _Parser[I, _Callable[[R], _Callable[[R], R]]], p: _Parser[I, R]) -> _Parser[I, R]:
    return p.chainr1(op)


@_curry
def chainl[I, R](op: _Parser[I, _Callable[[R], _Callable[[R], R]]], initial: R, p: _Parser[I, R]) -> _Parser[I, R]:
    return p.chainl(op, initial)


@_curry
def chainr[I, R](op: _Parser[I, _Callable[[R], _Callable[[R], R]]], initial: R, p: _Parser[I, R]) -> _Parser[I, R]:
    return p.chainr(op, initial)


@_curry
def as_type[I, R, S](tp: type[S], p: _Parser[I, R]) -> _Parser[I, S]:
    return p.as_type(tp)


@_curry
def label[I, R](value: str, p: _Parser[I, R]) -> _Parser[I, R]:
    return p.label(value)


@_overload
def sel[I, R1, R2](_p1: _Parser[I, R1], _p2: _Parser[I, R2]) -> _Parser[I, R1 | R2]: ...


@_overload
def sel[I, R1, R2, R3](_p1: _Parser[I, R1], _p2: _Parser[I, R2], _p3: _Parser[I, R3]) -> _Parser[I, R1 | R2 | R3]: ...


@_overload
def sel[I, R1, R2, R3, R4](
    _p1: _Parser[I, R1], _p2: _Parser[I, R2], _p3: _Parser[I, R3], _p4: _Parser[I, R4]
) -> _Parser[I, R1 | R2 | R3 | R4]: ...


@_overload
def sel[I, R1, R2, R3, R4, R5](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
) -> _Parser[I, R1 | R2 | R3 | R4 | R5]: ...


@_overload
def sel[I, R1, R2, R3, R4, R5, R6](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
) -> _Parser[I, R1 | R2 | R3 | R4 | R5 | R6]: ...


@_overload
def sel[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
) -> _Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7]: ...


@_overload
def sel[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
    _p8: _Parser[I, R8],
) -> _Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8]: ...


@_overload
def sel[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
    _p8: _Parser[I, R8],
    _p9: _Parser[I, R9],
) -> _Parser[I, R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9]: ...


def sel[I](
    _p1: _Parser[I, _Any],
    _p2: _Parser[I, _Any],
    _p3: _Parser[I, _Any] | None = None,
    _p4: _Parser[I, _Any] | None = None,
    _p5: _Parser[I, _Any] | None = None,
    _p6: _Parser[I, _Any] | None = None,
    _p7: _Parser[I, _Any] | None = None,
    _p8: _Parser[I, _Any] | None = None,
    _p9: _Parser[I, _Any] | None = None,
    *_ps: _Parser[I, _Any],
) -> _Parser[I, _Any]:
    plist: list[_Parser[I, _Any]] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps)))
    return _reduce(lambda x, y: x | y, plist)


@_overload
def seq[I, R1, R2](_p1: _Parser[I, R1], _p2: _Parser[I, R2]) -> _Parser[I, tuple[R1, R2]]: ...


@_overload
def seq[I, R1, R2, R3](
    _p1: _Parser[I, R1], _p2: _Parser[I, R2], _p3: _Parser[I, R3]
) -> _Parser[I, tuple[R1, R2, R3]]: ...


@_overload
def seq[I, R1, R2, R3, R4](
    _p1: _Parser[I, R1], _p2: _Parser[I, R2], _p3: _Parser[I, R3], _p4: _Parser[I, R4]
) -> _Parser[I, tuple[R1, R2, R3, R4]]: ...


@_overload
def seq[I, R1, R2, R3, R4, R5](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
) -> _Parser[I, tuple[R1, R2, R3, R4, R5]]: ...


@_overload
def seq[I, R1, R2, R3, R4, R5, R6](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
) -> _Parser[I, tuple[R1, R2, R3, R4, R5, R6]]: ...


@_overload
def seq[I, R1, R2, R3, R4, R5, R6, R7](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
) -> _Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7]]: ...


@_overload
def seq[I, R1, R2, R3, R4, R5, R6, R7, R8](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
    _p8: _Parser[I, R8],
) -> _Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8]]: ...


@_overload
def seq[I, R1, R2, R3, R4, R5, R6, R7, R8, R9](
    _p1: _Parser[I, R1],
    _p2: _Parser[I, R2],
    _p3: _Parser[I, R3],
    _p4: _Parser[I, R4],
    _p5: _Parser[I, R5],
    _p6: _Parser[I, R6],
    _p7: _Parser[I, R7],
    _p8: _Parser[I, R8],
    _p9: _Parser[I, R9],
) -> _Parser[I, tuple[R1, R2, R3, R4, R5, R6, R7, R8, R9]]: ...


def seq[I](
    _p1: _Parser[I, _Any],
    _p2: _Parser[I, _Any],
    _p3: _Parser[I, _Any] | None = None,
    _p4: _Parser[I, _Any] | None = None,
    _p5: _Parser[I, _Any] | None = None,
    _p6: _Parser[I, _Any] | None = None,
    _p7: _Parser[I, _Any] | None = None,
    _p8: _Parser[I, _Any] | None = None,
    _p9: _Parser[I, _Any] | None = None,
    *_ps: _Parser[I, _Any],
):
    plist: list[_Parser[I, _Any]] = list(filter(None, (_p1, _p2, _p3, _p4, _p5, _p6, _p7, _p8, _p9, *_ps)))
    return _reduce(lambda x, y: x & y, plist)
