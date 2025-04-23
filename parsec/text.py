from pathlib import Path
from parsec.context import IState, IStream, Context
from parsec.parser import Parser, token, tokens, item, Okay, Fail
from parsec import combinator as C
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


char: Callable[[str], Parser[str, str]] = token


def literal(text: str) -> Parser[str, str]:
    return tokens(text).map("".join)


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

alpha = item << C.where(str.isalpha) << C.with_err(Expected("alphabet"))
alnum = item << C.where(str.isalnum) << C.with_err(Expected("alphanumeric"))
lower = item << C.where(str.islower) << C.with_err(Expected("lowercase"))
upper = item << C.where(str.isupper) << C.with_err(Expected("uppercase"))
blank = item << C.where(str.isspace) << C.with_err(Expected("whitespace"))
digit = item << C.where(str.isdigit) << C.with_err(Expected("digit"))
bindigit = item << C.range("01") << C.with_err(Expected("binary digit"))
octdigit = item << C.range("01234567") << C.with_err(Expected("octal digit"))
hexdigit = (
    item
    << C.range("0123456789ABCDEFabcdef")
    << C.with_err(Expected("hexadecimal digit"))
)

num_sign = item << C.range("+-") << C.default("+")

decinteger = (
    (num_sign & digit.some())
    .map(lambda x: int(x[0] + "".join(x[1]), base=10))
    .with_err(Expected("decimal integer"))
)

bininteger = (
    (num_sign & bindigit.some().prefix(char("0") & item.range("bB")))
    .map(lambda x: int(x[0] + "".join(x[1]), base=2))
    .with_err(Expected("bininteger integer"))
)

octinteger = (
    (num_sign & octdigit.some().prefix(char("0") & item.range("bB")))
    .map(lambda x: int(x[0] + "".join(x[1]), base=2))
    .with_err(Expected("octinteger integer"))
)

hexinteger = (
    (num_sign & hexdigit.some().prefix(char("0") & item.range("bB")))
    .map(lambda x: int(x[0] + "".join(x[1]), base=2))
    .with_err(Expected("hexinteger integer"))
)

integer = hexinteger | octinteger | bininteger | decinteger

# _digitpart = digit.some().map("".join)
# _exponent = seq(item << range("eE"), num_sign, _digitpart).map("".join)

# _pointfloat = sel(
#     seq(_digitpart.default(""), dot, _digitpart).map("".join),
#     seq(_digitpart, dot).map("".join),
# )

# pointfloat = seq(num_sign, _pointfloat).map("".join).map(float)
# exponentfloat = (
#     seq(num_sign, sel(_pointfloat, _digitpart), _exponent).map("".join).map(float)
# )
# floatnumber = sel(exponentfloat, pointfloat) << C.with_err(Expected("float number"))

# number = (floatnumber | integer) << C.with_err(Expected("number"))
# blanks = blank.many().map("".join) << C.with_err(Expected("blanks"))
# identifier = seq(sel(alpha, underline), sel(alnum, underline).many().map("".join)).map(
#     "".join
# ) << C.with_err(Expected("identifier"))


def parse[R](parser: Parser[str, R], text: str):
    ctx = Context(TextStream(text), TextState())
    ret = parser.run(ctx)
    match ret.outcome:
        case Okay(value=val):
            return val
        case Fail(error=err):
            raise RuntimeError(f"Parse error:\n  {ret.context.state.format()}\n  {err}")
