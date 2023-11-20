from functools import partial

from src.parsec import Parser, Result, Okay, Fail, hsel, hseq, seq, sel

@Parser
def item(_input: str) -> Result[str]:
    return Okay(_input[0], _input[1:]) if _input else Fail(['EOFError'])

char = item.eq
dot = char('.')
comma = char(',')
semicolon = char(';')
open_round = char('(')
close_round = char(')')
open_square = char('[')
close_square = char(']')
open_curly = char('{')
close_curly = char('}')

alpha = item.where(str.isalpha)
alnum = item.where(str.isalnum)
lower = item.where(str.islower)
upper = item.where(str.isupper)
blank = item.where(str.isspace)
digit = item.where(str.isdigit)
bindigit = item.range('01')
octdigit = item.range('01234567')
hexdigit = item.range('0123456789ABCDEFabcdef')

decinteger = digit.some().str().map(int)
bininteger = hseq(
        char('0'),
        item.range('bB'),
        bindigit.many().str().map(partial(int, base=2))
    ).at(2).as_type(int)
octinteger = hseq(
        char('0'),
        item.range('oO'),
        octdigit.many().str().map(partial(int, base=8))
    ).at(2).as_type(int)
hexinteger = hseq(
    char('0'),
    item.range('xX'),
    hexdigit.many().str().map(partial(int, base=16))
).at(2).as_type(int)
integer = hsel(hexinteger, octinteger, bininteger, decinteger)

dot = char('.')
underline = char('_')

_digitpart = digit.some().str()
_fraction = seq(dot, _digitpart).str()
_exponent = hseq(
    item.range('eE'),
    item.range('+-').maybe(),
    _digitpart
).as_type(tuple[str]).str()
_pointfloat = hsel(
        hseq(_digitpart.maybe(), _fraction).as_type(tuple[str]).str(),
        hseq(_digitpart, dot).str()
    )

pointfloat = _pointfloat.map(float)
exponentfloat = hseq(
        hsel(_pointfloat, _digitpart),
        _exponent
    ).str().map(float)
floatnumber = sel(exponentfloat, pointfloat)

number = hsel(floatnumber, integer)

blanks = blank.many().str()
identifier = seq(
    sel(alpha, underline),
    sel(alnum, underline).many().str()
).str()

def literal(string: str):
    return seq(*(char(ch) for ch in string)).str()