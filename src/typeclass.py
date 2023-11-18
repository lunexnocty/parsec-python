from ast import TypeVar
from typing import Callable, Type, Protocol, Self, cast
from typing import runtime_checkable
from abc import abstractmethod, abstractclassmethod

from utils import cons, identity

type Lazy[T] = Callable[[], T]

@runtime_checkable
class Functor[T](Protocol):
    
    @abstractmethod
    def map[T1](
        self: Self,
        fn: Callable[[T], T1]
    ) -> 'Functor[T1]':
        raise NotImplementedError()
    
    def unzip[T1](
        self: 'Functor[tuple[T, T1]]'
    ) -> tuple['Functor[T]', 'Functor[T1]']:
        return self.map(lambda e: e[0]), self.map(lambda e: e[1])

@runtime_checkable
class Applicative[T](Functor[T], Protocol):

    @abstractclassmethod
    def of(
        cls: Type[Self],
        value: T
    ) -> Self:
        raise NotImplementedError()
    
    @abstractmethod
    def apply[T1](
        self: 'Applicative[Callable[[T], T1]]',
        m1: Lazy['Applicative[T]'],
    ) -> 'Applicative[T1]':
        raise NotImplementedError()

    def liftA2[T1, T2](
        self: Self,
        fn: Callable[[T], Callable[[T1], T2]],
        m1: Lazy['Applicative[T1]']
    ) -> 'Applicative[T2]':
        return cast(Applicative, self.map(fn)).apply(m1)
    
    def count(self, n: int) -> 'Applicative[list[T]]':
        return self.of([]) if n == 0 else self.liftA2(cons, lambda:self.count(n-1))

@runtime_checkable
class Alternative[T](Applicative[T], Protocol):
    
    @abstractclassmethod
    def of(
        cls: Type[Self],
        value: T
    ) -> Self:
        raise NotImplementedError()

    @abstractclassmethod
    def empty(
        cls: Type[Self]
    ) -> Self:
        raise NotImplementedError()
    
    @abstractmethod
    def alter_[T1](
        self: Self,
        m2: 'Alternative[T1]'
    ) -> 'Alternative[T | T1]':
        raise NotImplementedError()
    
    @staticmethod
    def alter[T1, T2](
        m1: 'Alternative[T1]',
        m2: 'Alternative[T2]'
    ) -> 'Alternative[T1 | T2]':
        return m1.alter_(m2)

    def some(self: Self) -> 'Alternative[list[T]]':
        return cast(Alternative, self.liftA2(cons, self.many))

    def many(self: Self) -> 'Alternative[list[T]]':
        return Alternative.alter(cast(Alternative, self.liftA2(cons, self.many)), self.of([]))

@runtime_checkable
class Monad[T](Applicative[T], Protocol):

    @abstractclassmethod
    def of(
        cls: Type[Self],
        value: T
    ) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def bind[T1](
        self: Self,
        fn: Callable[[T], 'Monad[T1]']
    ) -> 'Monad[T1]':
        raise NotImplementedError()
    
    def pair_[T1](self, m1: 'Monad[T1]'):
        return self.bind(lambda v1: m1.bind(lambda v2: self.of((v1, v2))))
    
    @staticmethod
    def pair[T1, T2](
        m1: 'Monad[T1]',
        m2: 'Monad[T2]'
    ):
        return m1.pair_(m2)
    
    def join(self: 'Monad[Monad[T]]') -> 'Monad[T]':
        return self.bind(identity)