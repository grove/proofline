"""Fresh declaration reusing the retired v3 controller with a pinned catalog."""
import json
from pathlib import Path
import sys

from evaluation.matched_v3 import study as runner

HERE = Path(__file__).resolve().parent


def main():
    if sys.argv[1] == 'execute':
        approval = runner.ROOT / '.proofline/issue16-matched-v4-20261013/approval.json'
        if not approval.exists() or json.loads(approval.read_text()).get('freeze_sha256') != runner.p.host.sha256((HERE / 'FREEZE.json').read_bytes()):
            raise ValueError('Fresh study requires explicit approval of this frozen declaration')
    runner.HERE = HERE
    runner.STORE = runner.ROOT / '.proofline/issue16-matched-v4-20261013'
    runner.catalog = lambda: json.loads((HERE / 'model-catalog.json').read_text())
    return runner.main()


if __name__ == '__main__':
    raise SystemExit(main())
