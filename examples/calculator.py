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


import unittest
from parsec.text import parse, Okay, Fail


class TestCalculatorParser(unittest.TestCase):
    def test_valid_expressions(self):
        test_cases = [
            ('2 + 3 * 4', 14),
            ('2 * (3 + 4)', 14),  # parentheses_priority
            ('((((1+2)*3)-4)/5)', 1.0),  # deep_nested_brackets
            ('0*5 + 0/1', 0),  # zero_operations
            ('1.2e3 * 2e-1', 240.0),  # scientific_notation_edge
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(
                    result.outcome.value.exec(), expected, msg=f'Failed for: {text}'
                )

    def test_failure(self):
        test_cases = [('', 0), ('++2', 2), ('+(1)', 2), ('abc', 1)]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(expr, text)
                self.assertIsInstance(result.outcome, Fail)
                self.assertEqual(result.consumed, expected, msg=f'Failed for: {text}')

    def test_partial_parsing(self):
        test_cases = [
            ('2 * (3 + 4 / (5 - 1)', 2),  # unbalanced_brackets
            ('2.3e4.5 * (3 + 4)', 23000.0),  # invalid_scientific_notation
            ('2 + 3 invalid', 5),  # trailing_junk
            ('3++4', 7),  # signed number
            ('1.2e3.4', 1.2e3),  # malformed_scientific
            ('2 * (3 + 4', 2),  # unbalanced_brackets1
            ('2 * 3) + 4', 6),  # unbalanced_brackets2
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertEqual(
                    result.outcome.value.exec(), expected, msg=f'Failed for: {text}'
                )

    def test_numerical_precision(self):
        test_cases = [
            ('0.0001 * 0.0002', 2e-8),  # float_operations
            ('-3.14 * 2', -6.28),  # negative_floats
            ('1.23e4 + 5.67e3', 17970.0),  # scientific_mix
            ('0.1e308 + 0.5e309', 5.1e308),
        ]
        for text, expected in test_cases:
            with self.subTest(msg=f'Testing: {text}'):
                result = parse(expr, text)
                self.assertIsInstance(result.outcome, Okay)
                self.assertAlmostEqual(
                    result.outcome.value.exec(),
                    expected,
                    delta=1e-12,
                    msg=f'Failed for: {text}',
                )


if __name__ == '__main__':
    unittest.main()
