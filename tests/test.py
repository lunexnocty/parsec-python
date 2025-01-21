import unittest


from parsec import Okay, Fail
from parsec.text import identifier, number, blank, comma, text_input

class TestBasicParser(unittest.TestCase):
    def test_identifier(self):
        ...
    
    def test_number(self):
        ...

    def test_seq_by(self):
        ...

if __name__ == '__main__':
    unittest.main()