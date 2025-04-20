from pathlib import Path
from parsec.context import IState, IStream, Context
from parsec.parser import Parser, token, tokens, item, Okay, Fail
# from parsec.combinator import expected, sel, seq, where, range, default, some, fmap
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

    def seek(self, offset: int) -> IStream[str]:
        # return TextStream(self.data, self.offset + offset)
        self.offset += offset
        return self

    def tell(self) -> int:
        return self.offset

    def eos(self) -> bool:
        return not (0 <= self.offset < len(self.data))


class TextState(IState[str]):
    def __init__(self, file: Path | None = None, line: int = 1, column: int = 1):
        self.file = None if file is None else str(file.absolute())
        self.line = line
        self.column = column

    def update(self, item: str):

        lines = item.count("\n")
        return TextState(
            line=self.line + lines,
            column=item.rfind("\n") + 1 if lines else self.column + len(item),
        )
        # self.line += lines
        # self.column = item.rfind("\n") + 1 if lines else self.column + len(item)
        # return self

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

# alpha = item << where(str.isalpha) << expected("alphabet")
# alnum = item << where(str.isalnum) << expected("alphanumeric")
# lower = item << where(str.islower) << expected("lowercase")
# upper = item << where(str.isupper) << expected("uppercase")
# blank = item << where(str.isspace) << expected("whitespace")
# digit = item << where(str.isdigit) << expected("digit")
# bindigit = item << range("01") << expected("binary digit")
# octdigit = item << range("01234567") << expected("octal digit")
# hexdigit = item << range("0123456789ABCDEFabcdef") << expected("hexadecimal digit")

# num_sign = item << range("+-") << default("")

# decinteger = (
#     (num_sign & (digit << some << fmap("".join)))
#     << fmap(lambda x: int("".join(x), base=10))
#     << expected("decimal integer")
# )
# bininteger = seq(
#     num_sign, bindigit.many().prefix(seq(char("0"), item << range("bB"))).map("".join)
# ).map(lambda x: int("".join(x), base=2)) << expected("binary integer")
# octinteger = seq(
#     num_sign, octdigit.many().prefix(seq(char("0"), item << range("oO"))).map("".join)
# ).map(lambda x: int("".join(x), base=8)) << expected("octal integer")
# hexinteger = seq(
#     num_sign, hexdigit.many().prefix(seq(char("0"), item << range("xX"))).map("".join)
# ).map(lambda x: int("".join(x), base=16)) << expected("hexadecimal integer")
# integer = sel(hexinteger, octinteger, bininteger, decinteger) << expected("integer")

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
# floatnumber = sel(exponentfloat, pointfloat) << expected("float number")

# number = (floatnumber | integer) << expected("number")
# blanks = blank.many().map("".join) << expected("blanks")
# identifier = seq(sel(alpha, underline), sel(alnum, underline).many().map("".join)).map(
#     "".join
# ) << expected("identifier")


def parse[R](parser: Parser[str, R], text: str):
    ctx = Context(TextStream(text), TextState())
    ret = parser.run(ctx)
    match ret.outcome:
        case Okay(value=val):
            return val
        case Fail(error=err):
            raise RuntimeError(
                f"Parse error:\n  {ret.context.state.format()}\n  {err}"
            )
