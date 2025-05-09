from dataclasses import dataclass

from core import Parser
from text import lexeme

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
>>> abs  := '\\' <var>+ '->' <expr>
>>> app  := <expr> <expr>
"""

expr = Parser[str, Expr]()
var = lexeme.lex_identifier.map(Var)
abs = (var.prefix(lexeme.lex_char('\\')) & expr.prefix(lexeme.lex_literal('->'))).map(lambda t: Abs(t[0], t[1]))
app = (expr & expr).map(lambda t: App(t[0], t[1]))
expr.define(var | abs | app | expr.between(lexeme.lex_l_round, lexeme.lex_r_round))
