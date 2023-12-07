from functools import partial

from src.parsec import Parser, Result, Okay, Fail, hsel, seq, sel

@Parser
def item(_input: str) -> Result[str]:
    return Okay(_input[0], _input[1:]) if _input else Fail(['EOFError'])

def literal(_token: str):
    @Parser
    def parse(_input: str) -> Result[str]:
        if not _token: return Okay('', _input)
        return char(_token[0]).bind(lambda c: literal(_token[1:]).bind(lambda cs: Parser.okay(c + cs)))(_input)
    return parse

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