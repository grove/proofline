import unittest
from app import process

class HappyPath(unittest.TestCase):
    def test_existing_example(self):
        self.assertEqual(process({'nodes': ['z', 'a'], 'edges': []}), {'order': ['z', 'a']})
