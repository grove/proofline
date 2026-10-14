"""A failed isolation canary must stop before tests and keep all slots unexecuted."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from evaluation.checklist_minimal import preflight


class MinimalPreflightTest(unittest.TestCase):
    def test_failed_boundary_stops_without_evaluating_or_spending(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            here = root / 'evaluation' / 'checklist_minimal'
            here.mkdir(parents=True)
            spec = json.loads((preflight.HERE / 'protocol.json').read_text())
            (here / 'protocol.json').write_text(json.dumps(spec))
            task = spec['tasks'][0]
            (here / 'inputs').mkdir()
            (here / 'requests').mkdir()
            shutil.copyfile(preflight.HERE / 'inputs/deadline-base.tar',
                            here / 'inputs/deadline-base.tar')
            shutil.copyfile(preflight.HERE / task['request_file'], here / task['request_file'])
            python = str(Path(sys.executable).resolve())
            runtime = hashlib.sha256(Path(python).read_bytes()).hexdigest()
            (here / 'FREEZE.json').write_text(json.dumps({
                'sha256': {}, 'runtime_sha256': {'python': runtime, 'codex': runtime}}))
            original = preflight.host.run_command
            def run(argv, *args, **kwargs):
                if argv == [python, '--version']:
                    return {'exit_code': 0, 'timed_out': False,
                            'stdout': 'codex-cli 0.162.1\n'}
                return original(argv, *args, **kwargs)
            denied = {'assessment': {'status': 'NOT VERIFIED',
                      'observations': {'reads': {'actual_oracle': 'allowed'}}}}
            with patch.object(preflight, 'HERE', here), \
                 patch.object(preflight, 'CODEX', python), \
                 patch.object(preflight.host, 'run_command', side_effect=run), \
                 patch.object(preflight.host, 'probe_boundary', return_value=denied), \
                 patch.object(preflight, 'invoke') as invoke:
                result = preflight.preflight(root / 'output')
            invoke.assert_not_called()
            self.assertEqual(result['status'], 'STOPPED_NOT_QUALIFIED')
            self.assertEqual(result['blocker'], 'Existing native boundary unavailable')
            self.assertEqual(result['model_dispatches'], 0)
            self.assertIsNone(result['live_authorization'])
            self.assertEqual(len(result['assignments']), 8)
            self.assertTrue(all(r['status'] == 'NOT_EXECUTED' for r in result['assignments']))
            self.assertEqual(json.loads((root / 'output/preflight.json').read_text()), result)
