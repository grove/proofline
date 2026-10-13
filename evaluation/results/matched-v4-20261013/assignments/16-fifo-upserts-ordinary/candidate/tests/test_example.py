import unittest
from app import process

class HappyPath(unittest.TestCase):
    def test_existing_example(self):
        self.assertEqual(process({'capacity': 2, 'events': [{'id': 'a', 'value': 1}, {'id': 'b', 'value': 2}, {'id': 'a', 'value': 3}, {'id': 'c', 'value': 4}]}), {'items': [{'id': 'b', 'value': 2}, {'id': 'c', 'value': 4}], 'evicted': ['a']})
