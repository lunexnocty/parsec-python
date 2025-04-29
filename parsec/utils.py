from typing import Any, Callable, overload


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
) -> Callable[[T1], Callable[[T2], Callable[[T3], Callable[[T4], Callable[[T5], R]]]]]: ...


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
        Callable[[T3], Callable[[T4], Callable[[T5], Callable[[T6], Callable[[T7], R]]]]],
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
            Callable[[T4], Callable[[T5], Callable[[T6], Callable[[T7], Callable[[T8], R]]]]],
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

    expected_args = fn.__code__.co_argcount

    @wraps(fn)
    def curried(*args: Any) -> Any:
        if len(args) >= expected_args:
            return fn(*args)

        def _(*more: Any) -> Any:
            return curried(*args, *more)

        return _

    return curried
