from datetime import date as Date
from datetime import datetime as Datetime
from datetime import time as Time
from functools import partial
from typing import Callable, cast

from parsec.parser import Parser, item, token, tokens
from parsec.text import TextParser

_s_join = ''.join

char = cast(Callable[[str], TextParser[str]], token)


def literal(text: str) -> TextParser[str]:
    return tokens(text).map(_s_join)


def _digit_n(n: int) -> TextParser[str]:
    return digit.repeat(n).map(_s_join)


dot: TextParser[str] = char('.')
comma: TextParser[str] = char(',')
semicolon: TextParser[str] = char(';')
l_round: TextParser[str] = char('(')
r_round: TextParser[str] = char(')')
l_square: TextParser[str] = char('[')
r_square: TextParser[str] = char(']')
l_curly: TextParser[str] = char('{')
r_curly: TextParser[str] = char('}')
underline: TextParser[str] = char('_')
colon: TextParser[str] = char(':')
hyphen: TextParser[str] = char('-')
quotation: TextParser[str] = char('"')

alpha: TextParser[str] = item.where(str.isalpha)
alnum: TextParser[str] = item.where(str.isalnum)
lower: TextParser[str] = item.where(str.islower)
upper: TextParser[str] = item.where(str.isupper)
blank: TextParser[str] = item.where(str.isspace)
digit: TextParser[str] = item.where(str.isdigit)
bindigit: TextParser[str] = item.range('01')
octdigit: TextParser[str] = item.range('01234567')
hexdigit: TextParser[str] = item.range('0123456789ABCDEFabcdef')

_num_sign: TextParser[str] = item.range('+-').default('')
_digits: TextParser[str] = digit.many().map(_s_join)
_digits1: TextParser[str] = digit.some().map(_s_join)
_bindigit1: TextParser[str] = bindigit.some().map(_s_join)
_octdigit1: TextParser[str] = octdigit.some().map(_s_join)
_hexdigit1: TextParser[str] = hexdigit.some().map(_s_join)

decinteger: TextParser[str] = (_num_sign & _digits1).map(_s_join)
bininteger: TextParser[str] = (_num_sign & _bindigit1.prefix(char('0') & item.range('bB'))).map(_s_join)
octinteger: TextParser[str] = (_num_sign & _octdigit1.prefix(char('0') & item.range('oO'))).map(_s_join)
hexinteger: TextParser[str] = (_num_sign & _hexdigit1.prefix(char('0') & item.range('xX'))).map(_s_join)
integer: TextParser[int] = (
    hexinteger.map(partial(int, base=16))
    | octinteger.map(partial(int, base=8))
    | bininteger.map(partial(int, base=2))
    | decinteger.map(partial(int, base=10))
).label('integer')

_exponent: TextParser[str] = (item.range('eE') & decinteger).map(_s_join)
_dotment: TextParser[str] = (dot & _digits & _exponent.default('')).map(_s_join)
_digit_float: TextParser[str] = (_num_sign & _digits1 & (_dotment | _exponent)).map(_s_join)
_dot_float: TextParser[str] = (_num_sign & dot & _digits1 & _exponent.default('')).map(_s_join)
floatnumber: TextParser[float] = (_dot_float | _digit_float).map(float).label('float number')
number: TextParser[float | int] = (floatnumber | integer).label('number')

blanks: TextParser[str] = blank.many().map(_s_join)
identifier: TextParser[str] = (
    ((alpha | underline) & (alnum | underline).many().map(_s_join)).map(_s_join).label('identifier')
)
date: TextParser[Date] = (
    (_digit_n(4) & hyphen & _digit_n(2) & hyphen & _digit_n(2)).map(_s_join).map(Date.fromisoformat)
).label('date')
time: TextParser[Time] = (
    (_digit_n(2) & colon & _digit_n(2) & colon & _digit_n(2)).map(_s_join).map(Time.fromisoformat)
).label('time')
datetime: TextParser[Datetime] = (date.suffix(char(' ')) & time).map(lambda dt: Datetime.combine(dt[0], dt[1]))
string: TextParser[str] = cast(Parser[str, str], item).many().map(_s_join).between(quotation, quotation)
