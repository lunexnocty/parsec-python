from pathlib import Path
from parsec import *


class TextStream(IStream[str]):
    def __init__(self, text: str, offset = 0):
        self.data = text
        self.offset = offset

    def read(self, n: int = 1) -> list[str]:
        self.offset += n
        return list(self.data[self.offset-n:self.offset])

    def peek(self, n: int = 1) -> list[str]:
        return list(self.data[self.offset:self.offset + n]).copy()

    def seek(self, offset: int) -> IStream[str]:
        return TextStream(self.data, self.offset + offset)
    
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
        lines = item.count('\n')
        return TextState(line=self.line + lines, column=item.rfind('\n') + 1 if lines else self.column + len(item))

    def format(self):
        if self.file is None:
            return f'{self.line}:{self.column}'
        return f'{self.file}:{self.line}:{self.column}'

char: Callable[[str], Parser[str, str]] = token
def literal(text: str) -> Parser[str, str]:
    return tokens(text).map(''.join)

dot = char('.')
comma = char(',')
semicolon = char(';')
open_round = char('(')
close_round = char(')')
open_square = char('[')
close_square = char(']')
open_curly = char('{')
close_curly = char('}')
underline = char('_')
alpha = item.where(str.isalpha).label('alphabet')
alnum = item.where(str.isalnum).label('alphanumeric')
lower = item.where(str.islower).label('lowercase')
upper = item.where(str.isupper).label('uppercase')
blank = item.where(str.isspace).label('whitespace')
digit = item.where(str.isdigit).label('digit')
bindigit = item.range('01').label('binary digit')
octdigit = item.range('01234567').label('octal digit')
hexdigit = item.range('0123456789ABCDEFabcdef').label('hexadecimal digit')

num_sign = item.range('+-').default('')

decinteger = seq(num_sign, digit.some().map(''.join)).map(lambda x: int(''.join(x), base=10)).label('decimal integer')
bininteger = seq(num_sign, bindigit.many().prefix(seq(char('0'), item.range('bB'))).map(''.join)).map(lambda x: int(''.join(x), base=2)).label('binary integer')
octinteger = seq(num_sign, octdigit.many().prefix(seq(char('0'), item.range('oO'))).map(''.join)).map(lambda x: int(''.join(x), base=8)).label('octal integer')
hexinteger = seq(num_sign, hexdigit.many().prefix(seq(char('0'), item.range('xX'))).map(''.join)).map(lambda x: int(''.join(x), base=16)).label('hexadecimal integer')
integer = sel(hexinteger, octinteger, bininteger, decinteger).label('integer')

dot = char('.')
underline = char('_')
_digitpart = digit.some().map(''.join)
_fraction = seq(dot, _digitpart).map(''.join)
_exponent = seq(item.range('eE'), num_sign, _digitpart).map(''.join)

_pointfloat = sel(seq(_digitpart.default(''), _fraction).map(''.join), seq(_digitpart, dot).map(''.join))

pointfloat = seq(num_sign, _pointfloat).map(''.join).map(float)
exponentfloat = seq(num_sign, sel(_pointfloat, _digitpart), _exponent).map(''.join).map(float)
floatnumber = sel(exponentfloat, pointfloat).label('float number')

number = floatnumber.or_else(integer).label('number')
blanks = blank.many().map(''.join).label('blanks')
identifier = seq(sel(alpha, underline), sel(alnum, underline).many().map(''.join)).map(''.join).label('identifier')

def parse[R](parser: Parser[str, R], text: str):
    ctx = Context(TextStream(text), TextState())
    return parser.run(ctx)
        
