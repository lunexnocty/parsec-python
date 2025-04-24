import unittest
from typing import Callable

from parsec.parser import look
from parsec.text import Parser, blank, char, digit, item, parse
from parsec.utils import const


class TestBasic(unittest.TestCase):
    def test_between(self):
        p = char("a").between(char("("), char(")"))
        self.assertEqual(parse(p, "(a)"), "a")

        p = char("a").many().between(char("("), char(")"))
        self.assertEqual(parse(p, "(aaa)"), ["a", "a", "a"])

    def test_ltrim(self):
        p = char("a").ltrim(blank)
        self.assertEqual(parse(p, "   a"), "a")

        p = char("a").ltrim(blank)
        self.assertEqual(parse(p, "a"), "a")

        p = char("a").ltrim(blank)
        self.assertEqual(parse(p, " \t\na"), "a")

    def test_rtrim(self):
        p = char("a").rtrim(blank)
        self.assertEqual(parse(p, "a   "), "a")

        p = char("a").rtrim(blank)
        self.assertEqual(parse(p, "a"), "a")

        p = char("a").rtrim(blank)
        self.assertEqual(parse(p, "a \t\n"), "a")

    def test_trim(self):
        p = char("a").trim(blank)
        self.assertEqual(parse(p, "   a   "), "a")

        p = char("a").trim(blank)
        self.assertEqual(parse(p, "a"), "a")

        p = char("a").trim(blank)
        self.assertEqual(parse(p, " \t\na \t\n"), "a")

    def test_many_till(self):
        p = char("a").many_till(char("b"))
        self.assertEqual(parse(p, "aaab"), ["a", "a", "a"])

        p = char("a").many_till(char("b"))
        self.assertEqual(parse(p, "b"), [])

        p = char("a").many_till(char("b"))
        self.assertEqual(parse(p, "aaabb"), ["a", "a", "a"])

    def test_repeat(self):
        p = char("a").repeat(3)
        self.assertEqual(parse(p, "aaaa"), ["a", "a", "a"])

        p = char("a").repeat(0)
        self.assertEqual(parse(p, ""), [])

        p = char("a").repeat(1)
        self.assertEqual(parse(p, "aaa"), ["a"])

    def test_where(self):
        p = digit.where(lambda x: int(x) > 5)
        self.assertEqual(parse(p, "7"), "7")

        p = digit.where(lambda x: int(x) >= 5)
        self.assertEqual(parse(p, "5"), "5")

        p = digit.where(lambda x: int(x) <= 9)
        self.assertEqual(parse(p, "9"), "9")

    def test_eq(self):
        p = char("a").eq("a")
        self.assertEqual(parse(p, "a"), "a")

        p = digit.eq("5")
        self.assertEqual(parse(p, "5"), "5")

        p = char("+").eq("+")
        self.assertEqual(parse(p, "+"), "+")

    def test_neq(self):
        p = item.neq("0")
        self.assertEqual(parse(p, "a"), "a")

    def test_range(self):
        p = char("b").range("abc")
        self.assertEqual(parse(p, "b"), "b")

        p = char("a").range("abc")
        self.assertEqual(parse(p, "a"), "a")

        p = char("c").range("abc")
        self.assertEqual(parse(p, "c"), "c")

    def test_chainl1(self):
        def _add_(x: int):
            def _add_x_(y: int):
                return x + y

            return _add_x_

        op = char("+").map(const(_add_))
        p = digit.map(int).chainl1(op)
        self.assertEqual(parse(p, "1+2+3"), 6)

        p = digit.map(int).chainl1(op)
        self.assertEqual(parse(p, "1"), 1)

        p = digit.map(int).chainl1(op)
        self.assertEqual(parse(p, "1+1+1"), 3)

    def test_chainr1(self):
        def _exp_(x: int):
            def _exp_x_(y: int):
                return x**y

            return _exp_x_

        op = char("^").map(const(_exp_))
        p = digit.map(int).chainr1(op)
        self.assertEqual(parse(p, "2^3^2"), 512)

        p = digit.map(int).chainr1(op)
        self.assertEqual(parse(p, "2"), 2)

        p = digit.map(int).chainr1(op)
        self.assertEqual(parse(p, "2^2^2"), 16)

    def test_sep_by(self):
        p = digit.sep_by(char(","))
        self.assertEqual(parse(p, "1,2,3"), ["1", "2", "3"])

        p = digit.sep_by(char(","))
        self.assertEqual(parse(p, "1"), ["1"])

    def test_end_by(self):
        p = digit.end_by(char(","))
        self.assertEqual(parse(p, "1,2,3,"), ["1", "2", "3"])

        p = digit.end_by(char(","))
        self.assertEqual(parse(p, "1,"), ["1"])

        p = digit.end_by(char(","))
        self.assertEqual(parse(p, ""), [])

    def test_chainl(self):
        def _add_(x: int):
            def _add_x_(y: int):
                return x + y

            return _add_x_

        op = char("+").map(const(_add_))
        p = digit.map(int).chainl(op, 0)
        self.assertEqual(parse(p, "1+2+3"), 6)

        p = digit.map(int).chainl(op, 0)
        self.assertEqual(parse(p, ""), 0)

        p = digit.map(int).chainl(op, 0)
        self.assertEqual(parse(p, "1"), 1)

    def test_chainr(self):
        def _exp_(x: int):
            def _exp_x_(y: int):
                return x**y

            return _exp_x_

        op = char("^").map(const(_exp_))
        p = digit.map(int).chainr(op, 1)
        self.assertEqual(parse(p, "2^3^2"), 512)

        p = digit.map(int).chainr(op, 1)
        self.assertEqual(parse(p, ""), 1)

        p = digit.map(int).chainr(op, 1)
        self.assertEqual(parse(p, "2"), 2)

    def test_some(self):
        p = char("a").some()
        self.assertEqual(parse(p, "aaa"), ["a", "a", "a"])

        p = char("a").some()
        self.assertEqual(parse(p, "a"), ["a"])

        with self.assertRaises(SystemExit):
            parse(p, "")

    def test_many(self):
        p = char("a").many()
        self.assertEqual(parse(p, "aaa"), ["a", "a", "a"])

        p = char("a").many()
        self.assertEqual(parse(p, "a"), ["a"])

        p = char("a").many()
        self.assertEqual(parse(p, ""), [])

    def test_maybe(self):
        p = char("a").maybe()
        self.assertEqual(parse(p, "a"), "a")

        p = char("a").maybe()
        self.assertEqual(parse(p, ""), None)

        p = char("a").maybe()
        self.assertEqual(parse(p, "b"), None)

    def test_default(self):
        p = char("a").default("b")
        self.assertEqual(parse(p, "a"), "a")

        p = char("a").default("b")
        self.assertEqual(parse(p, ""), "b")

        p = char("a").default("b")
        self.assertEqual(parse(p, "c"), "b")

    def test_pair(self):
        p = char("a").pair(char("b"))
        self.assertEqual(parse(p, "ab"), ("a", "b"))

        p = digit.pair(char("a"))
        self.assertEqual(parse(p, "1a"), ("1", "a"))

        p = char("a").pair(char("b")).pair(char("c"))
        self.assertEqual(parse(p, "abc"), (("a", "b"), "c"))

    def test_alter(self):
        p = char("a").alter(char("b"))
        self.assertEqual(parse(p, "b"), "b")

        p = char("a").alter(char("b"))
        self.assertEqual(parse(p, "a"), "a")

    def test_fast_alter(self):
        p = look.eq("a").fast_alter(char("b"))
        self.assertEqual(parse(p, "b"), "b")

        p = char("a").fast_alter(char("b"))
        self.assertEqual(parse(p, "a"), "a")

    def test_map(self):
        p = digit.map(int)
        self.assertEqual(parse(p, "1"), 1)

        p = char("a").map(lambda x: x.upper())
        self.assertEqual(parse(p, "a"), "A")

        p = char("a").many().map(lambda xs: "".join(xs))
        self.assertEqual(parse(p, "aaa"), "aaa")

    def test_bind(self):
        p = digit.map(int).bind(lambda n: char("a").repeat(n))
        self.assertEqual(parse(p, "3aaa"), ["a", "a", "a"])

        p = digit.map(int).bind(lambda n: digit.repeat(n))
        self.assertEqual(parse(p, "21234"), ["1", "2"])

        p = digit.map(int).bind(lambda n: char("a").repeat(n))
        self.assertEqual(parse(p, "3aaaaa"), ["a", "a", "a"])

    def test_apply(self):
        p = char("a").apply(Parser[str, Callable[[str], str]].okay(lambda x: x.upper()))
        self.assertEqual(parse(p, "a"), "A")

        p = digit.map(int).apply(
            Parser[str, Callable[[int], int]].okay(lambda x: x * 2)
        )
        self.assertEqual(parse(p, "2"), 4)

        p = (
            char("a")
            .many()
            .apply(Parser[str, Callable[[list[str]], int]].okay(lambda xs: len(xs)))
        )
        self.assertEqual(parse(p, "aaa"), 3)


if __name__ == "__main__":
    unittest.main()
