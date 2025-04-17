from abc import ABC, abstractmethod
from dataclasses import dataclass

from parsec.err import ParseErr


class IState[I](ABC):
    @abstractmethod
    def update(self, item: I) -> "IState[I]":
        raise NotImplementedError

    @abstractmethod
    def format(self) -> str:
        raise NotImplementedError


class IStream[I](ABC):
    @abstractmethod
    def tell(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def read(self, n: int = 1) -> list[I]:
        raise NotImplementedError

    @abstractmethod
    def peek(self, n: int = 1) -> list[I]:
        raise NotImplementedError

    @abstractmethod
    def seek(self, offset: int) -> "IStream[I]":
        raise NotImplementedError

    @abstractmethod
    def eos(self) -> bool:
        raise NotImplementedError


@dataclass
class Context[I]:
    stream: IStream[I]
    state: IState[I]

    def backtrack(self, consumed: int, state: IState[I]):
        return Context(self.stream.seek(-consumed), state)

    def update(self, value: I):
        return Context(self.stream, self.state.update(value))


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
