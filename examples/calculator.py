
from dataclasses import dataclass
from typing import Literal

from src.basic import number, char, open_round, close_round, blank
from src.parsec import Parser, Result, alter, hseq
from src.utils import const

"""
AST of calculator:
>>> Expr = Number { value: number }
>>>      | BinaryExpr { opcode: Opcode, left: Expr, right: Expr }
"""
class Expr: pass
@dataclass
class Number(Expr):
    value: float | int
type Opcode = Literal['+', '-', '*', '/']
@dataclass
class BinaryExpr(Expr):
    opcode: Opcode
    left: Expr
    right: Expr


"""
EBNF of calculator:
>>> expr := <add_or_sub_exp>
>>> add_or_sub_exp :=  <mul_or_div_exp> (('+' | '-')  <mul_or_div_exp>)*
>>> mul_or_div_exp := <factor> (('*' | '/')  <factor>)*
>>> factor := '(' <expr> ')' | <num>
>>> num := { number }
"""

num = number.ignore(blank).map(Number)
@Parser
def factor(_input: str) -> Result[Expr]:
    l_round = open_round.ignore(blank)
    r_round = close_round.ignore(blank)
    exp = hseq(l_round, expr, r_round).at(1).as_type(Expr)
    return alter(exp, num)(_input)

def binary_op(op: Opcode):
    def _fn1(left: Expr):
        def _fn2(right: Expr) -> Expr:
            return BinaryExpr(opcode=op, left=left, right=right)
        return _fn2
    return char(op).ignore(blank).map(const(_fn1))

mul_or_div = alter(binary_op('*'), binary_op('/'))
add_or_sub = alter(binary_op('+'), binary_op('-'))
mul_or_div_exp = factor.chainl1(mul_or_div)
add_or_sub_exp = mul_or_div_exp.chainl1(add_or_sub)
expr = add_or_sub_exp

if __name__ == '__main__':
    ret = expr(' 1 * 2 + 1 / ( 2 - 1 ) * 3  ')
    print(ret)