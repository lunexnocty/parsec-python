from typing import Any, Callable, cast, overload


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


def flatten(t: tuple[Any, Any]) -> tuple[Any, ...]:
    match t:
        case (tuple(left), right):
            return (*left, right)
        case (left, right):
            return (left, right)


@overload
def curry[T1, R](fn: Callable[[T1], R]) -> Callable[[T1], R]: ...


@overload
def curry[T1, T2, R](
    fn: Callable[[T1, T2], R],
) -> Callable[[T1], Callable[[T2], R]]: ...


@overload
def curry[T1, T2, T3, R](
    fn: Callable[[T1, T2, T3], R],
) -> Callable[[T1], Callable[[T2], Callable[[T3], R]]]: ...


@overload
def curry[T1, T2, T3, T4, R](
    fn: Callable[[T1, T2, T3, T4], R],
) -> Callable[[T1], Callable[[T2], Callable[[T3], Callable[[T4], R]]]]: ...


@overload
def curry[T1, T2, T3, T4, T5, R](
    fn: Callable[[T1, T2, T3, T4, T5], R],
) -> Callable[
    [T1], Callable[[T2], Callable[[T3], Callable[[T4], Callable[[T5], R]]]]
]: ...


@overload
def curry[T1, T2, T3, T4, T5, T6, R](
    fn: Callable[[T1, T2, T3, T4, T5, T6], R],
) -> Callable[
    [T1],
    Callable[[T2], Callable[[T3], Callable[[T4], Callable[[T5], Callable[[T6], R]]]]],
]: ...


@overload
def curry[T1, T2, T3, T4, T5, T6, T7, R](
    fn: Callable[[T1, T2, T3, T4, T5, T6, T7], R],
) -> Callable[
    [T1],
    Callable[
        [T2],
        Callable[
            [T3], Callable[[T4], Callable[[T5], Callable[[T6], Callable[[T7], R]]]]
        ],
    ],
]: ...


@overload
def curry[T1, T2, T3, T4, T5, T6, T7, T8, R](
    fn: Callable[[T1, T2, T3, T4, T5, T6, T7, T8], R],
) -> Callable[
    [T1],
    Callable[
        [T2],
        Callable[
            [T3],
            Callable[
                [T4], Callable[[T5], Callable[[T6], Callable[[T7], Callable[[T8], R]]]]
            ],
        ],
    ],
]: ...


@overload
def curry[T1, T2, T3, T4, T5, T6, T7, T8, T9, R](
    fn: Callable[[T1, T2, T3, T4, T5, T6, T7, T8, T9], R],
) -> Callable[
    [T1],
    Callable[
        [T2],
        Callable[
            [T3],
            Callable[
                [T4],
                Callable[
                    [T5],
                    Callable[[T6], Callable[[T7], Callable[[T8], Callable[[T9], R]]]],
                ],
            ],
        ],
    ],
]: ...


def curry(fn: Callable[..., Any]) -> Callable[..., Any]:
    from functools import wraps

    def make_curried(expected_args):
        @wraps(fn)
        def inner(*args):
            if len(args) >= expected_args:
                return fn(*args)
            return curry(lambda *more: fn(*args, *more))

        return inner

    n = fn.__code__.co_argcount
    return make_curried(n)


@curry
def make_pair[A, B](a: A, b: B) -> tuple[A, B]:
    return (a, b)


@curry
def false[A](_a: Any, _b: A) -> A:
    return _b


@curry
def true[A](_a: A, _b: Any) -> A:
    return _a
