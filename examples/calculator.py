from dataclasses import dataclass
from abc import abstractmethod
from operator import add, sub, mul, truediv
from typing import Literal


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
