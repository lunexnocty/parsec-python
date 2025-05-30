from abc import ABC, abstractmethod
from dataclasses import dataclass


class IState[I](ABC):
    @abstractmethod
    def update(self, value: I) -> 'IState[I]':
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
    def seek(self, offset: int) -> 'IStream[I]':
        raise NotImplementedError

    @abstractmethod
    def move(self, offset: int) -> 'IStream[I]':
        raise NotImplementedError

    @abstractmethod
    def eos(self) -> bool:
        raise NotImplementedError


@dataclass
class Context[I]:
    stream: IStream[I]
    state: IState[I]

    def backtrack(self, consumed: int, state: IState[I]):
        return Context(self.stream.move(-consumed), state)

    def update(self, value: I):
        return Context(self.stream, self.state.update(value))
