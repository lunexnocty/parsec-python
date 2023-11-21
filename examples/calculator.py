
from dataclasses import dataclass
from typing import Literal

from src.basic import number, char, open_round, close_round, blank
from src.parsec import Parser, Result, alter, hseq
from src.utils import const


class Expr:
    """
    AST of calculator:
    >>> Expr = Num 
    >>>      | Exp (opcode: Opcode, left: Expr, right: Expr)
    """
    pass

@dataclass
class Num(Expr):
    value: float | int

type Opcode = Literal['+', '-', '*', '/']

@dataclass
class Exp(Expr):
    opcode: Opcode
    left: Expr
    right: Expr

"""
EBNF of calculator:
    >>> Expr := add_or_sub
    >>> add_or_sub :=  <mul_or_div> (('+' | '-')  <mul_or_div>)*
    >>> mul_or_div := <factor> (('*' | '/')  <factor>)*
    >>> factor := '(' <expr> ')' | <num>
    >>> num := { number }
"""

num = number.ignore(blank).map(Num)
@Parser
def factor(_input: str) -> Result[Expr]:
    l_round = open_round.ignore(blank)
    r_round = close_round.ignore(blank)
    exp = hseq(l_round, expr, r_round).at(1).as_type(Expr)
    return alter(exp, num)(_input)

def create_bin_op(op: Opcode):
    def _fn1(left: Expr):
        def _fn2(right: Expr) -> Expr:
            return Exp(opcode=op, left=left, right=right)
        return _fn2
    return char(op).ignore(blank).map(const(_fn1))

mul_or_div_exp = factor.chainl1(alter(create_bin_op('*'), create_bin_op('/')))
add_or_sub = mul_or_div_exp.chainl1(alter(create_bin_op('+'), create_bin_op('-')))
expr = add_or_sub

if __name__ == '__main__':
    ret = expr(' 1 * 2 + 1 / ( 2 - 1 ) * 3  ')
    print(ret)