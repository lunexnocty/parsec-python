from parsec.text import basic as _T


def lex_char(value: str):
    return _T.lexeme(_T.blank)(_T.char(value))


def lex_literal(value: str):
    return _T.lexeme(_T.blank)(_T.literal(value))


lex_alnum = _T.lexeme(_T.blank)(_T.alnum)
lex_alpha = _T.lexeme(_T.blank)(_T.alpha)
lex_bindigit = _T.lexeme(_T.blank)(_T.bindigit)
lex_bininteger = _T.lexeme(_T.blank)(_T.bininteger)
lex_colon = _T.lexeme(_T.blank)(_T.colon)
lex_comma = _T.lexeme(_T.blank)(_T.comma)
lex_date = _T.lexeme(_T.blank)(_T.date)
lex_datetime = _T.lexeme(_T.blank)(_T.datetime)
lex_decinteger = _T.lexeme(_T.blank)(_T.decinteger)
lex_digit = _T.lexeme(_T.blank)(_T.digit)
lex_dot = _T.lexeme(_T.blank)(_T.dot)
lex_floatnumber = _T.lexeme(_T.blank)(_T.floatnumber)
lex_hexdigit = _T.lexeme(_T.blank)(_T.hexdigit)
lex_hexinteger = _T.lexeme(_T.blank)(_T.hexinteger)
lex_hyphen = _T.lexeme(_T.blank)(_T.hyphen)
lex_identifier = _T.lexeme(_T.blank)(_T.identifier)
lex_integer = _T.lexeme(_T.blank)(_T.integer)
lex_l_curly = _T.lexeme(_T.blank)(_T.l_curly)
lex_l_round = _T.lexeme(_T.blank)(_T.l_round)
lex_l_bracket = _T.lexeme(_T.blank)(_T.l_bracket)
lex_lower = _T.lexeme(_T.blank)(_T.lower)
lex_number = _T.lexeme(_T.blank)(_T.number)
lex_octdigit = _T.lexeme(_T.blank)(_T.octdigit)
lex_octinteger = _T.lexeme(_T.blank)(_T.octinteger)
lex_quotation = _T.lexeme(_T.blank)(_T.quotation)
lex_r_curly = _T.lexeme(_T.blank)(_T.r_curly)
lex_r_round = _T.lexeme(_T.blank)(_T.r_round)
lex_r_bracket = _T.lexeme(_T.blank)(_T.r_bracket)
lex_semicolon = _T.lexeme(_T.blank)(_T.semicolon)
lex_string = _T.lexeme(_T.blank)(_T.string)
lex_time = _T.lexeme(_T.blank)(_T.time)
lex_underline = _T.lexeme(_T.blank)(_T.underline)
lex_upper = _T.lexeme(_T.blank)(_T.upper)
