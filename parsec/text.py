from functools import partial
from pathlib import Path
from parsec.context import IState, IStream, Context
from parsec.parser import Parser, token, tokens, item, Okay, Fail
from parsec.err import Expected
from typing import Callable


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
    def __init__(self, file: Path | None = None, line: int = 1, column: int = 1):
        self.file = None if file is None else str(file.absolute())
        self.line = line
        self.column = column

    def update(self, value: str):
        lines = value.count("\n")
        return TextState(
            line=self.line + lines,
            column=value.rfind("\n") + 1 if lines else self.column + len(value),
        )

    def format(self):
        if self.file is None:
            return f"{self.line}:{self.column}"
        return f"{self.file}:{self.line}:{self.column}"


def parse[R](parser: Parser[str, R], text: str):
    ctx = Context(TextStream(text), TextState())
    ret = parser.run(ctx)
    match ret.outcome:
        case Okay(value=val):
            return val
        case Fail(error=err):
            raise SystemExit(
                f"Parse error at:\n  {ret.context.state.format()}\n  {err}"
            )


_flat_str = "".join

char: Callable[[str], Parser[str, str]] = token


def literal(text: str) -> Parser[str, str]:
    return tokens(text).map(_flat_str)


dot = char(".")
comma = char(",")
semicolon = char(";")
open_round = char("(")
close_round = char(")")
open_square = char("[")
close_square = char("]")
open_curly = char("{")
close_curly = char("}")
underline = char("_")

alpha = item.where(str.isalpha).with_err(Expected("alphabet"))
alnum = item.where(str.isalnum).with_err(Expected("alphanumeric"))
lower = item.where(str.islower).with_err(Expected("lowercase"))
upper = item.where(str.isupper).with_err(Expected("uppercase"))
blank = item.where(str.isspace).with_err(Expected("whitespace"))
digit = item.where(str.isdigit).with_err(Expected("digit"))
bindigit = item.range("01").with_err(Expected("binary digit"))
octdigit = item.range("01234567").with_err(Expected("octal digit"))
hexdigit = item.range("0123456789ABCDEFabcdef").with_err(Expected("hexadecimal digit"))

num_sign = item.range("+-").default("")
digits = digit.many().map(_flat_str)
digits1 = digit.some().map(_flat_str)
_bindigit1 = bindigit.some().map(_flat_str)
_octdigit1 = octdigit.some().map(_flat_str)
_hexdigit1 = hexdigit.some().map(_flat_str)

decinteger = (num_sign & digits1).map(_flat_str)

bininteger = (num_sign & _bindigit1.prefix(char("0") & item.range("bB"))).map(_flat_str)

octinteger = (num_sign & _octdigit1.prefix(char("0") & item.range("bB"))).map(_flat_str)

hexinteger = (num_sign & _hexdigit1.prefix(char("0") & item.range("bB"))).map(_flat_str)

integer = (
    hexinteger.map(partial(int, base=16))
    | octinteger.map(partial(int, base=8))
    | bininteger.map(partial(int, base=2))
    | decinteger.map(partial(int, base=10))
)

_exponet = (item.range("eE") & decinteger).map(_flat_str).default("")
_dotment = (dot & digits).map(_flat_str).default("")
_digit_float = (digits1 & _dotment & _exponet).map(_flat_str)
_dot_float = (dot & digits1 & _exponet).map(_flat_str)
floatnumber = (
    (num_sign & (_digit_float | _dot_float))
    .map(_flat_str)
    .map(float)
    .with_err(Expected("float number"))
)

number = (floatnumber | integer).with_err(Expected("number"))
blanks = blank.many().map(_flat_str)
identifier = (
    ((alpha | underline) & (alnum | underline).many().map(_flat_str))
    .map(_flat_str)
    .with_err(Expected("identifier"))
)
