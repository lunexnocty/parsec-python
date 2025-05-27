from typing import Any, Callable

from parsec import Parser as _Parser
from parsec.text import basic as _T


def lexeme[R](_lex: _Parser[str, Any] = _T.blank) -> Callable[[_Parser[str, R]], _Parser[str, R]]:
    def _(p: _Parser[str, R]) -> _Parser[str, R]:
        return p.ltrim(_lex)

    return _


def char(value: str):
    return lexeme(_T.blank)(_T.char(value))


def literal(value: str):
    return lexeme(_T.blank)(_T.literal(value))


alnum = lexeme(_T.blank)(_T.alnum)
alpha = lexeme(_T.blank)(_T.alpha)
bindigit = lexeme(_T.blank)(_T.bindigit)
bininteger = lexeme(_T.blank)(_T.bininteger)
colon = lexeme(_T.blank)(_T.colon)
comma = lexeme(_T.blank)(_T.comma)
date = lexeme(_T.blank)(_T.date)
datetime = lexeme(_T.blank)(_T.datetime)
decinteger = lexeme(_T.blank)(_T.decinteger)
digit = lexeme(_T.blank)(_T.digit)
dot = lexeme(_T.blank)(_T.dot)
floatnumber = lexeme(_T.blank)(_T.floatnumber)
hexdigit = lexeme(_T.blank)(_T.hexdigit)
hexinteger = lexeme(_T.blank)(_T.hexinteger)
hyphen = lexeme(_T.blank)(_T.hyphen)
identifier = lexeme(_T.blank)(_T.identifier)
integer = lexeme(_T.blank)(_T.integer)
l_curly = lexeme(_T.blank)(_T.l_curly)
l_round = lexeme(_T.blank)(_T.l_round)
l_bracket = lexeme(_T.blank)(_T.l_bracket)
lower = lexeme(_T.blank)(_T.lower)
number = lexeme(_T.blank)(_T.number)
octdigit = lexeme(_T.blank)(_T.octdigit)
octinteger = lexeme(_T.blank)(_T.octinteger)
quotation = lexeme(_T.blank)(_T.quotation)
r_curly = lexeme(_T.blank)(_T.r_curly)
r_round = lexeme(_T.blank)(_T.r_round)
r_bracket = lexeme(_T.blank)(_T.r_bracket)
semicolon = lexeme(_T.blank)(_T.semicolon)
string = lexeme(_T.blank)(_T.string)
time = lexeme(_T.blank)(_T.time)
underline = lexeme(_T.blank)(_T.underline)
upper = lexeme(_T.blank)(_T.upper)
