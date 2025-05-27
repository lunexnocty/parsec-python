from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable


class ParseErr(Exception, ABC):
    indent = 4

    def __str__(self):
        return self.pretty()

    def __hash__(self):
        return hash(tuple(sorted(vars(self).items())))

    def __eq__(self, other: object):
        if other is self:
            return True
        if isinstance(other, self.__class__):
            return vars(self) == vars(other)
        return False

    @abstractmethod
    def pretty(self, indent: int = 0) -> str:
        raise NotImplementedError


class UnExpected(ParseErr):
    __eq__ = ParseErr.__eq__
    __hash__ = ParseErr.__hash__

    def __init__(self, value: str, state: str):
        self.value = value
        self.state = state

    def pretty(self, indent: int = 0):
        pad = ' ' * indent if indent > 0 else '\n'
        return f'{pad}UnExpected "{self.value}" at {self.state}'


def EOSError(state: str):
    return UnExpected('<EOS>', state)


class Expected(ParseErr):
    __eq__ = ParseErr.__eq__

    def __init__(self, value: str, children: Iterable[ParseErr] | None = None):
        self.value = value
        self.children: list[ParseErr] = [] if children is None else list(children)
        self.resolve()

    def __hash__(self):
        return hash((self.value, tuple(self.children)))

    def resolve(self):
        children = chain.from_iterable(
            child.children if isinstance(child, AlterError) else [child] for child in self.children
        )
        self.children = list(set(children))

    def pretty(self, indent: int = 0):
        pad = ' ' * indent if indent > 0 else '\n'
        msg = [f'{pad}Expected "{self.value}"']
        for child in self.children:
            msg.append(child.pretty(indent=indent + self.indent))
        return '\n'.join(msg)


class AlterError(ParseErr):
    __eq__ = ParseErr.__eq__

    def __init__(self, children: list[ParseErr] | None = None):
        self.children: list[ParseErr] = children or []

    def __hash__(self):
        return hash(tuple(self.children))

    def join(self):
        children = chain.from_iterable(
            child.children if isinstance(child, AlterError) else [child] for child in self.children
        )
        return AlterError(list(children))

    def pretty(self, indent: int = 0):
        pad = ' ' * indent if indent > 0 else '\n'
        return f'{pad}AlterError'
