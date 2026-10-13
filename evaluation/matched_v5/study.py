"""Read published matched outcomes; live declaration is retired."""
import json
from pathlib import Path
import sys

from evaluation.matched_v3 import study as runner

HERE = Path(__file__).resolve().parent


def main():
    if sys.argv[1] == 'report':
        result = json.loads((runner.ROOT / 'evaluation/results/matched-v5-20261013/results.json').read_text())
        print(json.dumps(runner.report.summarize(result['assignments']), indent=2))
        return 0
    if sys.argv[1] == 'execute':
        approval = runner.ROOT / '.proofline/issue16-matched-v5-20261013/approval.json'
        if not approval.exists() or json.loads(approval.read_text()).get('freeze_sha256') != runner.p.host.sha256((HERE / 'FREEZE.json').read_bytes()):
            raise ValueError('Fresh study requires explicit approval of this frozen declaration')
    runner.HERE = HERE
    runner.STORE = runner.ROOT / '.proofline/issue16-matched-v5-20261013'
    runner.catalog = lambda: json.loads((HERE / 'model-catalog.json').read_text())
    return runner.main()


if __name__ == '__main__':
    raise SystemExit(main())
