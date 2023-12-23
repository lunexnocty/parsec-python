
from dataclasses import dataclass
from typing import Literal

from src.text import number, char, open_round, close_round, blank
from src.parsec import Parser, Input, Result, alter
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

num = number.trim(blank).map(Number)
@Parser
def factor(_input: Input[str]) -> Result[str, Expr]:
    l_round = open_round.trim(blank)
    r_round = close_round.trim(blank)
    exp = expr.between(l_round, r_round)
    return alter(exp, num)(_input)

def binary_op(op: Opcode):
    def _fn1(left: Expr):
        def _fn2(right: Expr) -> Expr:
            return BinaryExpr(opcode=op, left=left, right=right)
        return _fn2
    return char(op).trim(blank).map(const(_fn1))

mul_or_div = alter(binary_op('*'), binary_op('/'))
add_or_sub = alter(binary_op('+'), binary_op('-'))
mul_or_div_exp = factor.chainl1(mul_or_div)
add_or_sub_exp = mul_or_div_exp.chainl1(add_or_sub)
expr = add_or_sub_exp