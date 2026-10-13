import unittest
from app import process

class HappyPath(unittest.TestCase):
    def test_existing_example(self):
        self.assertEqual(process({'balances': {'a': 5, 'b': 0}, 'transfers': [['a', 'b', 3]]}), {'balances': {'a': 2, 'b': 3}})
