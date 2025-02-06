from dataclasses import dataclass
from functools import reduce

from parsec.text import identifier, blank, char, literal, open_round, close_round
from parsec import Parser, sel

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
    return reduce(lambda e, p: Abs(param=p, body=e), reversed(_value[0]), _value[1])

def app_op(left: Expr):
    def _fn(right: Expr) -> Expr:
        return App(lhs=left, rhs=right)
    return _fn

lam_expr = Parser[str, Expr]()
var = identifier.ltrim(blank).map(Var)
arrow = literal('->').ltrim(blank)
prompt = char('\\').ltrim(blank)
fun = var.some().between(prompt, arrow).pair(lam_expr).map(build_fun)
l_round = open_round.ltrim(blank)
r_round = close_round.ltrim(blank)
factor = lam_expr.between(l_round, r_round)
atom = sel(factor, fun, var.as_type(Expr))
op = blank.some().map(lambda _: app_op)
lam_expr.define(atom.chainl1(op))