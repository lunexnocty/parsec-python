from typing import Any, Callable, cast

def const[A](a: A):
    def func(b: Any) -> A: return a
    return func


def cons[T](a: T):
    def put(l: list[T]):
        return [a, *l]
    return put


def identity[T](x: T):
    return x


def curry2[T, U, V](
    fn: Callable[[T, U], V]
) -> Callable[[T], Callable[[U], V]]:
    return lambda t: lambda u: fn(t, u)


def uncurry2[T, U, V](
    fn: Callable[[T], Callable[[U], V]]
) -> Callable[[T, U], V]:
    return lambda t, u: fn(t)(u)


def flip[T, U, V](
    fn: Callable[[T], Callable[[U], V]]
) -> Callable[[U], Callable[[T], V]]:
    return lambda u: lambda t: fn(t)(u)


def compose[T, U](
    *fns: Callable[[T], U]
) -> Callable[[T], U]:
    def helper(x: T) -> U:
        for fn in reversed(fns):
            x = fn(x)
        return cast(U, x)
    return helper


def pipes[T, U](
    *fns: Callable[[T], U]
) -> Callable[[T], U]:
    def helper(x: T) -> U:
        for func in fns:
            x = func(x)
        return cast(U, x)
    return helper