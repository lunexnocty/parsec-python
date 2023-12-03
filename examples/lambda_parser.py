from dataclasses import dataclass
from functools import reduce

from src.basic import identifier, blank, char, dot, blanks, literal, open_round, close_round
from src.parsec import Parser, Result, pair, sel
from src.utils import const

"""
AST of Lambda
>>> Expr = Var
>>>      | Abs { param: Var, body: Expr }
>>>      | App { lhs: Expr, rhs: Expr }
"""


class Expr: pass
@dataclass
class Var(Expr):
    name: str
@dataclass
class Abs(Expr):
    param: Var
    body: Expr
@dataclass
class App(Expr):
    lhs: Expr
    rhs: Expr

"""EBNF of Lambda Calculus
>>> expr := <var> | <abs> | <app> | '(' <expr> ')'
>>> var  := { identifier }
>>> abs  := '\\' <var>+ '->' <expr>
>>> app  := <expr> <expr>
"""

def build_fun(_value: tuple[list[Var], Expr]):
    return reduce(lambda e, p: Abs(param=p, body=e), reversed(_value[0]), initial=_value[1])

def app_op(left: Expr):
    def _fn(right: Expr) -> Expr:
        return App(lhs=left, rhs=right)
    return _fn

@Parser
def atom(_input: str) -> Result[Expr]:
    var = identifier.ignore(blank).map(Var)
    
    arrow = literal('->').ignore(blank)
    prompt = char('\\').ignore(blank)
    fun = pair(var.some().between(prompt, arrow), expr).map(build_fun)
    
    l_round = open_round.ignore(blank)
    r_round = close_round.ignore(blank)
    factor = expr.between(l_round, r_round)
    return sel(factor, fun, var.as_type(Expr))(_input)

expr = atom.chainl1(blanks.map(const(app_op)))