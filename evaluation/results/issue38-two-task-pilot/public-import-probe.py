import sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.path[0])/'src'))
import humanize
assert humanize.naturalsize(999_999,gnu=True,format='Size: %.1f')=='Size: 976.6K'
print('public package import and original reproducer passed')
