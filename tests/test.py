import unittest
from parsec import text, Okay, Fail

class TestParsec(unittest.TestCase):
    def test_number_parser(self):
        # 测试数字解析器
        number_parser = text.number
        result = text.parse(number_parser, "123")
        self.assertIsInstance(result.outcome, Okay)
        self.assertEqual(result.outcome.value, 123)

        # 测试非数字输入
        result = text.parse(number_parser, "abc")
        self.assertIsInstance(result.outcome, Fail)

    def test_addition_parser(self):
        # 测试加法表达式解析器
        number = text.number
        add = text.char('+').trim(text.blank).map(lambda _: lambda x, y: x + y)
        expr = number.suffix(add).pair(number).map(lambda x: x[0] + x[1])

        # 测试有效的加法表达式
        result = text.parse(expr, "1 + 2")
        self.assertIsInstance(result.outcome, Okay)
        self.assertEqual(result.outcome.value, 3)

        # 测试无效的加法表达式
        result = text.parse(expr, "1 + ")
        self.assertIsInstance(result.outcome, Fail)

        result = text.parse(expr, "a + 2")
        self.assertIsInstance(result.outcome, Fail)

    def test_whitespace_handling(self):
        # 测试空白字符处理
        number = text.number
        add = text.char('+').trim(text.blank).map(lambda _: lambda x, y: x + y)
        expr = number.suffix(add).pair(number).map(lambda x: x[0] + x[1])

        # 测试带有空白字符的表达式
        result = text.parse(expr, " 1 + 2 ")
        self.assertIsInstance(result.outcome, Fail)

    def test_failure_cases(self):
        # 测试解析失败的情况
        number = text.number
        add = text.char('+').trim(text.blank).map(lambda _: lambda x, y: x + y)
        expr = number.suffix(add).pair(number).map(lambda x: x[0] + x[1])

        # 测试无效的输入
        result = text.parse(expr, "1 + + 2")
        self.assertIsInstance(result.outcome, Fail)

        result = text.parse(expr, "1 + a")
        self.assertIsInstance(result.outcome, Fail)

        result = text.parse(expr, "1 + 2 + 3")
        self.assertIsInstance(result.outcome, Okay)
        self.assertEqual(result.outcome.value, 3)

if __name__ == "__main__":
    unittest.main()
