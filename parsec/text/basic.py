from datetime import date as _Date
from datetime import datetime as _Datetime
from datetime import time as _Time
from functools import partial as _partial
from typing import cast

from parsec.core import Parser as _Parser
from parsec.core import item as _item
from parsec.core import tokens as _tokens

_s_join = ''.join

char = cast(_Parser[str, str], _item).eq


def literal(text: str) -> _Parser[str, str]:
    return _tokens(text).map(_s_join)


def _digit_n(n: int) -> _Parser[str, str]:
    return digit.repeat(n).map(_s_join)


dot = char('.')
comma = char(',')
semicolon = char(';')
l_round = char('(')
r_round = char(')')
l_bracket = char('[')
r_bracket = char(']')
l_curly = char('{')
r_curly = char('}')
underline = char('_')
colon = char(':')
hyphen = char('-')
quotation = char('"')

alpha = _item.where(str.isalpha)
alnum = _item.where(str.isalnum)
lower = _item.where(str.islower)
upper = _item.where(str.isupper)
blank = _item.where(str.isspace)
digit = _item.where(str.isdigit)
bindigit = _item.range('01')
octdigit = _item.range('01234567')
hexdigit = _item.range('0123456789ABCDEFabcdef')

_num_sign = _item.range('+-').default('')
_digits = digit.many().map(_s_join)
_digits1 = digit.some().map(_s_join)
_bindigit1 = bindigit.some().map(_s_join)
_octdigit1 = octdigit.some().map(_s_join)
_hexdigit1 = hexdigit.some().map(_s_join)

decinteger = (_num_sign & _digits1).map(_s_join)
bininteger = (_num_sign & _bindigit1.prefix(char('0') & _item.range('bB'))).map(_s_join)
octinteger = (_num_sign & _octdigit1.prefix(char('0') & _item.range('oO'))).map(_s_join)
hexinteger = (_num_sign & _hexdigit1.prefix(char('0') & _item.range('xX'))).map(_s_join)
integer: _Parser[str, int] = (
    hexinteger.map(_partial(int, base=16))
    | octinteger.map(_partial(int, base=8))
    | bininteger.map(_partial(int, base=2))
    | decinteger.map(_partial(int, base=10))
).label('integer')

_exponent = (_item.range('eE') & decinteger).map(_s_join)
_dotment = (dot & _digits & _exponent.default('')).map(_s_join)
_digit_float = (_num_sign & _digits1 & (_dotment | _exponent)).map(_s_join)
_dot_float = (_num_sign & dot & _digits1 & _exponent.default('')).map(_s_join)
floatnumber: _Parser[str, float] = (_dot_float | _digit_float).map(float).label('float number')
number: _Parser[str, float | int] = (floatnumber | integer).label('number')

blanks = blank.many().map(_s_join)
identifier = ((alpha | underline) & (alnum | underline).many().map(_s_join)).map(_s_join).label('identifier')
date: _Parser[str, _Date] = (
    (_digit_n(4) & hyphen & _digit_n(2) & hyphen & _digit_n(2)).map(_s_join).map(_Date.fromisoformat)
).label('date')
time: _Parser[str, _Time] = (
    (_digit_n(2) & colon & _digit_n(2) & colon & _digit_n(2)).map(_s_join).map(_Time.fromisoformat)
).label('time')
datetime: _Parser[str, _Datetime] = (date.suffix(char(' ')) & time).map(lambda dt: _Datetime.combine(dt[0], dt[1]))
string = _item.neq('"').many().map(_s_join).between(quotation, quotation)
