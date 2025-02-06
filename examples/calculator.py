
from dataclasses import dataclass
from abc import abstractmethod
from operator import add, sub, mul, truediv
from typing import Literal

from parsec.text import number, char, open_round, close_round, blank
from parsec import Parser, sel

"""
AST of calculator:
>>> Expr = Number { value: number }
>>>      | BinaryExpr { opcode: Opcode, left: Expr, right: Expr }
"""

class Expr:
    @abstractmethod
    def exec(self) -> float | int:
        raise NotImplementedError

@dataclass
class Number(Expr):
    value: float | int
    def exec(self):
        return self.value

type Opcode = Literal['+', '-', '*', '/']

@dataclass
class BinaryExpr(Expr):
    opcode: Opcode
    left: Expr
    right: Expr
    op_func = dict(zip('+-*/', (add, sub, mul, truediv)))

    def exec(self):
        l_value = self.left.exec()
        r_value = self.right.exec()
        return self.op_func[self.opcode](l_value, r_value)
        


"""
EBNF of calculator:
>>> expr := <add_or_sub_exp>
>>> add_or_sub_exp :=  <mul_or_div_exp> (('+' | '-')  <mul_or_div_exp>)*
>>> mul_or_div_exp := <factor> (('*' | '/')  <factor>)*
>>> factor := '(' <expr> ')' | <num>
>>> num := { number }
"""

num = number.trim(blank).map(Number)
l_round = open_round.trim(blank)
r_round = close_round.trim(blank)

expr = Parser[str, Expr]()
factor = sel(expr.between(l_round, r_round), num)
def binary_op(op: Opcode):
    def _fn1(left: Expr):
        def _fn2(right: Expr) -> Expr:
            return BinaryExpr(opcode=op, left=left, right=right)
        return _fn2
    return char(op).trim(blank).map(lambda _: _fn1)

mul_or_div = sel(binary_op('*'), binary_op('/'))
add_or_sub = sel(binary_op('+'), binary_op('-'))
mul_or_div_exp = factor.chainl1(mul_or_div)
add_or_sub_exp = mul_or_div_exp.chainl1(add_or_sub)
expr.define(add_or_sub_exp)
