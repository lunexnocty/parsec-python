from dataclasses import dataclass

class ParseErr: ...

@dataclass
class UnExceptedError[I](ParseErr):
    value: I
    def __str__(self) -> str:
        return f'{self.__class__.__name__}: unexcepted "{self.value}" caused by:'

@dataclass
class Excepted(ParseErr):
    value: str
    def __str__(self) -> str:
        return f'excepted "{self.value}"'

@dataclass
class EOSError(ParseErr):
    def __str__(self) -> str:
        return f'{self.__class__.__name__}: End of input stream'
