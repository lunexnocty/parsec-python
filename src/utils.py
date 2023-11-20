from typing import Any, Callable, cast

def const[A](a: A):
    def func(b: Any) -> A: return a
    return func


def cons[T](_a: T):
    def put(_l: list[T]):
        return [_a, *_l]
    return put


def identity[T](_x: T):
    return _x


def curry2[T, U, V](
    _fn: Callable[[T, U], V]
) -> Callable[[T], Callable[[U], V]]:
    return lambda t: lambda u: _fn(t, u)


def uncurry2[T, U, V](
    _fn: Callable[[T], Callable[[U], V]]
) -> Callable[[T, U], V]:
    return lambda t, u: _fn(t)(u)


def flip[T, U, V](
    _fn: Callable[[T], Callable[[U], V]]
) -> Callable[[U], Callable[[T], V]]:
    return lambda u: lambda t: _fn(t)(u)


def compose[T, U](
    *_fns: Callable[[T], U]
) -> Callable[[T], U]:
    def helper(x: T) -> U:
        for fn in reversed(_fns):
            x = fn(x)
        return cast(U, x)
    return helper


def pipes[T, U](
    *_fns: Callable[[T], U]
) -> Callable[[T], U]:
    def helper(x: T) -> U:
        for func in _fns:
            x = func(x)
        return cast(U, x)
    return helper