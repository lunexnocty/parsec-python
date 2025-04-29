from pathlib import Path

from parsec.context import Context, IState, IStream
from parsec.parser import Fail, Okay, Parser


class TextStream(IStream[str]):
    def __init__(self, text: str, offset: int = 0):
        self.data = text
        self.offset = offset

    def read(self, n: int = 1) -> list[str]:
        self.offset += n
        return list(self.data[self.offset - n : self.offset])

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


class TextState(IState[str]):
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


type TextParser[R] = Parser[str, R]


def parse[R](parser: TextParser[R], text: str):
    ctx = Context(TextStream(text), TextState())
    ret = parser.run(ctx)
    match ret.outcome:
        case Okay(value=v):
            return v
        case Fail(error=e):
            raise e
