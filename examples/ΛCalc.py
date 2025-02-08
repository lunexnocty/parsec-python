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

import unittest
from parsec.text import parse, Okay, Fail

class TestLambdaParser(unittest.TestCase):
    def test_basic_structures(self):
        test_cases = [
            ("x", Var("x")),  # single_var
            (r"\x->x", Abs(Var("x"), Var("x"))),  # single_abs
            ("f x", App(Var("f"), Var("x"))),  # simple_app
            (r"\x y->x y", Abs(Var("x"), Abs(Var("y"), App(Var("x"), Var("y"))))),  # multi_param_abs
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f"Testing: {text}"):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)

    def test_nested_structures(self):
        test_cases = [
            (r"(\x->x) y", App(Abs(Var("x"), Var("x")), Var("y"))),  # app_with_paren
            (r"\x->\y->x y", Abs(Var("x"), Abs(Var("y"), App(Var("x"), Var("y"))))),  # nested_abs
            ("f (g x)", App(Var("f"), App(Var("g"), Var("x")))),  # nested_app
            (r"\a->a b c", Abs(Var("a"), App(App(Var("a"), Var("b")), Var("c")))),  # left_associative_app
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)

    def test_edge_cases(self):
        test_cases = [
            (r"\x y z->x", Abs(Var("x"), Abs(Var("y"), Abs(Var("z"), Var("x"))))),  # multi_param_arrow
            ("  x   ", Var("x")),  # whitespace_handling
            ("((x))", Var("x")),  # redundant_parens
            ("x y z", App(App(Var("x"), Var("y")), Var("z"))),  # chained_app
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)
    
    def test_parse_failures(self):
        test_cases = [
            r"\x->",        # missing_body
            "123",          # invalid_identifier
            r"\1x->y",      # invalid_variable_name
            r"\x\y->z",     # missing_arrow
            r"(x y",        # unmatched_paren
            "",             # empty_input
            r"\x->\y",      # incomplete_abs
        ]
        for text in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Fail, msg=f"Should fail but passed: {text}")

    def test_advanced_syntax(self):
        test_cases = [
            (r"(\f x->f x) (\x->x)", 
             App(
                 Abs(Var("f"), Abs(Var("x"), App(Var("f"), Var("x")))),
                 Abs(Var("x"), Var("x"))
             )),  # church_encoding
            (r"\x->x \y->y", 
             Abs(Var("x"), App(Var("x"), Abs(Var("y"), Var("y"))))),  # abs_in_app
            (r"x \y->y", 
             App(Var("x"), Abs(Var("y"), Var("y")))),  # app_with_abs
            (r"\x->(\y->y) x", 
             Abs(Var("x"), App(Abs(Var("y"), Var("y")), Var("x")))),  # nested_abs_in_app
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)

    def test_whitespace_handling(self):
        test_cases = [
            ("  x  ", Var("x")),  # surrounding_whitespace
            ("x   y", App(Var("x"), Var("y"))),  # multiple_spaces
            (r"\x  ->  x", Abs(Var("x"), Var("x"))),  # spaces_around_arrow
            ("(  x  )", Var("x")),  # spaces_in_parens
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)

    def test_complex_expressions(self):
        test_cases = [
            (r"(\x->x) (\y->y) z", 
             App(App(Abs(Var("x"), Var("x")), Abs(Var("y"), Var("y"))), Var("z"))),  # nested_apps
            (r"\x->\y->\z->x y z", 
             Abs(Var("x"), Abs(Var("y"), Abs(Var("z"), App(App(Var("x"), Var("y")), Var("z")))))),  # deep_nested_abs
            (r"(\x->x y) (\z->z)", 
             App(Abs(Var("x"), App(Var("x"), Var("y"))), Abs(Var("z"), Var("z")))),  # complex_app
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(lam_expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(result.outcome.value, expected)

if __name__ == '__main__':
    unittest.main()