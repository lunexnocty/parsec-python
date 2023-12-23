import os
from functools import partial

from src.parsec import Parser, Input, Result, Okay, Fail, hsel, seq, sel, State


class Path:
    def __init__(self, _url: str) -> None:
        # assert os.path.isfile(_url), FileNotFoundError(_url)
        self.url = _url


class Pos(State[str]):
    def __init__(self, filename: Path | None = None, line = 1, column = 1) -> None:
        self.url =  Path('::memory') if filename is None else filename
        self.line = line
        self.column = column
    
    def update(self, val: str):
        match val:
            case '\r':
                return Pos(self.url, line=self.line, column=1)
            case '\n':
                return Pos(self.url, line=self.line + 1, column=1)
            case _:
                return Pos(self.url, line=self.line, column = self.column + 1)

def stream(src: str | Path) -> Input[str]:
    if isinstance(src, str):
        return Input(src, Pos())
    with open(src.url, 'r') as f:
        return Input(f.read(), Pos(src))

@Parser
def item(_in: Input[str]) -> Result[str, str]:
    val, rest = _in.get()
    return Fail(['EOFError']) if val is None else Okay(val, rest)

char = item.eq

def literal(_token: str):
    @Parser
    def parse(_in: Input[str]) -> Result[str, str]:
        if not _token: return Okay('', _in)
        return char(_token[0]).bind(lambda c: literal(_token[1:]).bind(lambda cs: Parser.okay(c + cs)))(_in)
    return parse

dot = char('.')
comma = char(',')
semicolon = char(';')
open_round = char('(')
close_round = char(')')
open_square = char('[')
close_square = char(']')
open_curly = char('{')
close_curly = char('}')

alpha = item.where(str.isalpha, 'expected a alphabet')
alnum = item.where(str.isalnum, 'expected a alphabet or digit')
lower = item.where(str.islower, 'expected a lower-case')
upper = item.where(str.isupper, 'expected a upper-case')
blank = item.where(str.isspace, 'expected a white space')
digit = item.where(str.isdigit, 'expected a digit')
bindigit = item.range('01')
octdigit = item.range('01234567')
hexdigit = item.range('0123456789ABCDEFabcdef')

decinteger = digit.some().str().map(int)
bininteger = bindigit.many().str().map(partial(int, base=2)).prefix(seq(char('0'), item.range('bB')))
octinteger = octdigit.many().str().map(partial(int, base=8)).prefix(seq(char('0'), item.range('oO')))
hexinteger = hexdigit.many().str().map(partial(int, base=16)).prefix(seq(char('0'), item.range('xX')))
integer = sel(hexinteger, octinteger, bininteger, decinteger)

dot = char('.')
underline = char('_')

_digitpart = digit.some().str()
_fraction = seq(dot, _digitpart).str()
_exponent = seq(item.range('eE'), item.range('+-').default(''), _digitpart).str()

_pointfloat = sel(seq(_digitpart.default(''), _fraction).str(), seq(_digitpart, dot).str())

pointfloat = _pointfloat.map(float)
exponentfloat = seq(sel(_pointfloat, _digitpart), _exponent).str().map(float)
floatnumber = sel(exponentfloat, pointfloat)

number = hsel(floatnumber, integer)

blanks = blank.many().str()
identifier = seq(sel(alpha, underline), sel(alnum, underline).many().str()).str()