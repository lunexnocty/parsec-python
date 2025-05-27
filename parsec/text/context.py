from parsec.context import Context as _Context
from parsec.context import IState as _IState
from parsec.context import IStream as _IStream
from parsec.core import Fail as _Fail
from parsec.core import Okay as _Okay
from parsec.core import Parser as _Parser


class TextStream(_IStream[str]):
    def __init__(self, text: str, offset: int = 0):
        self.data = text
        self.offset = offset

    def read(self, n: int = 1) -> list[str]:
        self.offset += n
        return list(self.data[self.offset - n : self.offset]).copy()

    def peek(self, n: int = 1) -> list[str]:
        return list(self.data[self.offset : self.offset + n]).copy()

    def move(self, offset: int):
        return TextStream(self.data, self.offset + offset)

    def seek(self, offset: int):
        return TextStream(self.data, offset)

    def tell(self) -> int:
        return self.offset

    def eos(self) -> bool:
        return not (0 <= self.offset < len(self.data))


class TextState(_IState[str]):
    from pathlib import Path

    def __init__(self, file: Path | None = None, line: int = 1, column: int = 0):
        self.file = None if file is None else str(file.absolute())
        self.line = line
        self.column = column

    def update(self, value: str):
        lines = value.count('\n')
        return TextState(
            line=self.line + lines,
            column=value.rfind('\n') + 1 if lines else self.column + len(value),
        )

    def format(self):
        if self.file is None:
            return f'{self.line}:{self.column}'
        return f'{self.file}:{self.line}:{self.column}'


def parse[R](parser: _Parser[str, R], text: str):
    ctx = _Context(TextStream(text), TextState())
    ret = parser.run(ctx)
    match ret.outcome:
        case _Okay(value=v):
            return v
        case _Fail(error=e):
            raise e
