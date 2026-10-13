import unittest
from app import process

class HappyPath(unittest.TestCase):
    def test_existing_example(self):
        self.assertEqual(process({'catalog': {'fr-CA': {'a': 'CA'}, 'fr': {'b': 'FR'}, 'en': {'c': 'EN'}}, 'locales': ['fr-CA'], 'keys': ['b', 'a', 'c', 'x', 'a'], 'default': 'en'}), {'texts': ['FR', 'CA', 'EN', None, 'CA']})
