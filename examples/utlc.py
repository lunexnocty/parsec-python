from dataclasses import dataclass

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
