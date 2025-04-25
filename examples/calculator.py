from abc import abstractmethod
from dataclasses import dataclass
from operator import add, mul, sub, truediv
from typing import Literal

from parsec import combinator as C
from parsec import text as T
from parsec.utils import curry

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


type Opcode = Literal["+", "-", "*", "/"]


@dataclass
class BinaryExpr(Expr):
    opcode: Opcode
    left: Expr
    right: Expr
    op_func = dict(zip("+-*/", (add, sub, mul, truediv)))

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


def calc(op: str):
    @curry
    def _(x: int | float, y: int | float):
        return {"+": x + y, "-": x - y, "*": x * y, "/": x / y}[op]

    return _


expr = T.Parser[str, int | float]()
num = T.number << C.trim(T.blank)
factor = expr << C.between(T.open_round)(T.close_round) | num
mul_or_div = T.char("*") | T.char("/")
mul_or_div_op = (mul_or_div << C.trim(T.blank)) @ calc
mul_or_div_expr = factor << C.chainl1(mul_or_div_op)
add_or_sub = T.item << C.range("+-")
add_or_sub_op = (add_or_sub << C.trim(T.blank)) @ calc
add_or_sub_expr = mul_or_div_expr << C.chainl1(add_or_sub_op)
expr.define(add_or_sub_expr)
