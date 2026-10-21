"""Independent compatibility sample for humanize #366; standard library only."""
import importlib
from pathlib import Path
import sys
import types

# A Git checkout lacks hatch's generated _version.py; load the real submodule
# without fabricating a generated version or modifying candidate contents.
package = types.ModuleType('humanize')
package.__path__ = [str(Path(sys.path[0]) / 'src/humanize')]
sys.modules['humanize'] = package
naturalsize = importlib.import_module('humanize.filesize').naturalsize
cases = [
    ((999_999,), {'gnu': True, 'format': 'Size: %.1f'}, 'Size: 976.6K'),
    ((999_999,), {'gnu': True, 'format': '%.1f remaining'}, '976.6 remainingK'),
    ((-999_999,), {'gnu': True, 'format': 'Size: %.1f'}, 'Size: -976.6K'),
    ((999_999,), {}, '1.0 MB'),
    ((1024**2-1,), {'binary': True}, '1.0 MiB'),
    ((1024**2-1,), {'gnu': True}, '1.0M'),
    ((300,), {}, '300 Bytes'),
]
for args, kwargs, expected in cases:
    actual = naturalsize(*args, **kwargs)
    assert actual == expected, (args, kwargs, actual, expected)
# The issue allows skipping rollover for decorated formats OR computing it
# independently. Either result satisfies this boundary case.
actual = naturalsize(999_999, format='Size: %.1f')
assert actual in ('Size: 1000.0 kB', 'Size: 1.0 MB'), actual
print('8 source/compatibility cases passed')
