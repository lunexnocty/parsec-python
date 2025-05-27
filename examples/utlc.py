from dataclasses import dataclass

from parsec.core import Parser
from parsec.text import lex

"""
AST of Lambda
>>> Expr = Var
>>>      | Abs { param: Var, body: Expr }
>>>      | App { lhs: Expr, rhs: Expr }
"""


class Expr:
    pass


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
>>> abs  := '\\' <var> '->' <expr>
>>> app  := <expr> <expr>
"""

expr = Parser[str, Expr]()
var = lex.identifier @ Var
abs = (var.prefix(lex.char('\\')) & expr.prefix(lex.literal('->'))).map(lambda t: Abs(*t))
app = (expr & expr).map(lambda t: App(*t))
expr.define(var | abs | app | expr.between(lex.l_round, lex.r_round))
