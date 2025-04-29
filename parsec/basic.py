from parsec import parser as _P
from parsec.text import basic as _T
from parsec.text import parse as _parse

parse_text = _parse

alnum = _T.alnum
alpha = _T.alpha
bindigit = _T.bindigit
bininteger = _T.bininteger
blank = _T.blank
blanks = _T.blanks
char = _T.char
colon = _T.colon
comma = _T.comma
date = _T.date
datetime = _T.datetime
decinteger = _T.decinteger
digit = _T.digit
dot = _T.dot
floatnumber = _T.floatnumber
hexdigit = _T.hexdigit
hexinteger = _T.hexinteger
hyphen = _T.hyphen
identifier = _T.identifier
integer = _T.integer
item = _P.item
l_curly = _T.l_curly
l_round = _T.l_round
l_square = _T.l_square
literal = _T.literal
lower = _T.lower
number = _T.number
number = _T.number
octdigit = _T.octdigit
octinteger = _T.octinteger
quotation = _T.quotation
r_curly = _T.r_curly
r_round = _T.r_round
r_square = _T.r_square
semicolon = _T.semicolon
string = _T.string
time = _T.time
token = _P.token
tokens = _P.tokens
underline = _T.underline
upper = _T.upper
