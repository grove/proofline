"""Independent behavioral sample for python-dotenv #715; standard library only."""
import io
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(sys.path[0]) / 'src'))
from dotenv import dotenv_values

with patch.dict(os.environ, {}, clear=True):
    cases = [
        ('b=\na=${b:-d}', {'b': '', 'a': 'd'}),
        ('a=${b:-d}', {'a': 'd'}),
        ('b=c\na=${b:-d}', {'b': 'c', 'a': 'c'}),
        ('b=\na=${b}', {'b': '', 'a': ''}),
    ]
    for source, expected in cases:
        actual = dotenv_values(stream=io.StringIO(source))
        assert actual == expected, (source, actual, expected)
print('4 source-grounded cases passed')
