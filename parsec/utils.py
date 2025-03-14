from typing import Any, Callable, cast


def const[A](a: A) -> Callable[[Any], A]:
    def func(_: Any) -> A:
        return a

    return func


def cons[T](_a: T) -> Callable[[list[T]], list[T]]:
    def put(_l: list[T]):
        return [_a, *_l]

    return put


def identity[T](_x: T) -> T:
    return _x


def curry2[T, U, V](_fn: Callable[[T, U], V]) -> Callable[[T], Callable[[U], V]]:
    return lambda t: lambda u: _fn(t, u)


def uncurry2[T, U, V](_fn: Callable[[T], Callable[[U], V]]) -> Callable[[T, U], V]:
    return lambda t, u: _fn(t)(u)


def flip[T, U, V](
    _fn: Callable[[T], Callable[[U], V]],
) -> Callable[[U], Callable[[T], V]]:
    return lambda u: lambda t: _fn(t)(u)


def compose[T, U](*_fns: Callable[[T], U]) -> Callable[[T], U]:
    def helper(x: T) -> U:
        _: Any = x
        for fn in reversed(_fns):
            _ = fn(_)
        return cast(U, _)

    return helper


def pipes[T, U](*_fns: Callable[[T], U]) -> Callable[[T], U]:
    def helper(x: T) -> U:
        _: Any = x
        for func in _fns:
            _ = func(_)
        return cast(U, _)

    return helper


def head[T, *Ts](_tuples: tuple[T, *Ts]):
    return _tuples[0]


def tail[T, *Ts](_tuples: tuple[T, *Ts]):
    return _tuples[1:]


def fst[T, *Ts](_tuples: tuple[T, *Ts]):
    return head(_tuples)


def snd[T1, T2, *Ts](_tuples: tuple[T1, T2, *Ts]):
    return _tuples[1]
