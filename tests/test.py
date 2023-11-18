import unittest


from src import Okay, Fail
from src.basic import identifier, number, blank, comma

class TestBasicParser(unittest.TestCase):
    def test_identifier(self):
        self.assertIsInstance(identifier(''), Fail)
        self.assertIsInstance(identifier('1234567890'), Fail)
        self.assertIsInstance(identifier('123hello'), Fail)
        self.assertEqual(identifier('hello'), Okay(value='hello', rest=''))
        self.assertEqual(identifier('hello world'), Okay(value='hello', rest=' world'))
        self.assertEqual(identifier('hello,world!'), Okay(value='hello', rest=',world!'))
        self.assertEqual(identifier('hello,'), Okay(value='hello', rest=','))
    
    def test_number(self):
        self.assertEqual(number("123"), Okay(123, ""))
        self.assertEqual(number("0"), Okay(0, ""))
        self.assertEqual(number("3.14"), Okay(3.14, ""))
        self.assertEqual(number("0.0"), Okay(0.0, ""))
        self.assertEqual(number("1.23e2"), Okay(123.0, ""))
        self.assertEqual(number("6.022e23"), Okay(6.022e23, ""))
        self.assertEqual(number("1.23.45"), Okay(1.23, '.45'))
        self.assertEqual(number("1e"), Okay(1, 'e'))
        self.assertIsInstance(number("-4.56e-3"), Fail)
        self.assertIsInstance(number("-2.5"), Fail)
        self.assertIsInstance(number("-456"), Fail)
        self.assertIsInstance(number("abc"), Fail)
        self.assertIsInstance(number(""), Fail)

    def test_seq_by(self):
        self.assertEqual(number.ignore(blank).sep_by(comma.ignore(blank))(' 1\n,\t2.3 ,4 ,  1e3'), Okay([1, 2.3, 4, 1e3], ''))

if __name__ == '__main__':
    unittest.main()