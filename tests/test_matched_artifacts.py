"""Worker planning failures are observations, not loss of native qualification."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.matched_v3 import study


class WorkerArtifactFailures(unittest.TestCase):
    def test_invalid_advice_never_stops_assignments_or_falls_back_in_combined_arm(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            here, store = root / 'preparation', root / 'study'
            here.mkdir(); store.mkdir()
            (here / 'FREEZE.json').write_text('{"live_dispatch_allowed":true}')
            (here / 'protocol.json').write_bytes((study.HERE / 'protocol.json').read_bytes())
            rows = study.ledger()[:4]
            frozen = []
            for row in rows:
                inputs = store / f"{row['sequence']:02d}-{row['arm']}" / 'inputs'
                product = study.initialize(row['task'], inputs)
                row['inputs'] = str(inputs)
                frozen.append({'seed_snapshot': study.p.host.snapshot(product),
                    'source_sha256': study.p.host.sha256((inputs / 'source.md').read_bytes()),
                    'checks': study.selected_checks(row['task'])})
            (store / 'results.json').write_text(json.dumps({'status': 'QUALIFIED_NOT_DISPATCHED', 'assignments': rows}))
            manifest = {'protocol': study.read_protocol(), 'assignments': frozen}

            def launch(argv, prompt, private, seconds):
                path = private / 'events.jsonl'
                path.write_text('')
                return {'events_path': str(path)}

            def check(product, *args, **kwargs):
                return {'feedback': {'checks': []}, 'elapsed_seconds': 0, 'model_dispatches': 0,
                        'candidate_tree': study.p.host.git(product, 'rev-parse', 'HEAD^{tree}')}

            with ExitStack() as patches:
                replacements = [(study, 'HERE', here), (study, 'STORE', store),
                    (study, 'verify', lambda: manifest), (study, 'boundary', lambda *a, **k: {}),
                    (study, 'producer_files', lambda: {}), (study.p.live, 'launch', launch),
                    (study.p.live, 'read_events', lambda r: {'report': {'completed': True, 'summary': 'simulated'},
                        'usage': {'input_tokens': 10, 'output_tokens': 1}, 'thread_id': 'simulated', 'commands': {}}),
                    (study.p.live, 'reconcile_worker', lambda *a: {}),
                    (study.local_run, 'inspect', lambda p: {'status': 'CHECKS PASSED'}),
                    (study.grader, 'grade', lambda *a, **k: {'correct': True, 'available': True})]
                for owner, name, value in replacements:
                    patches.enter_context(patch.object(owner, name, value))
                rejected = patches.enter_context(patch.object(study.intentline_advisory, 'load_export', side_effect=ValueError('Unsupported revision 2')))
                checked = patches.enter_context(patch.object(study.local_run, 'check', side_effect=check))
                patches.enter_context(patch('builtins.print'))
                study.execute()
            result = json.loads((store / 'results.json').read_text())
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual([r['status'] for r in result['assignments']],
                ['CORRECT_DELIVERY', 'CORRECT_DELIVERY', 'CORRECT_DELIVERY', 'CORRECT_BUT_BLOCKED'])
            self.assertEqual(rejected.call_count, 2)
            self.assertEqual(checked.call_count, 1)
            self.assertEqual(result['assignments'][3]['check_status'], 'IMPORT REJECTED')
            self.assertTrue(all(r['model_dispatches'] == 1 for r in result['assignments']))


if __name__ == '__main__':
    unittest.main()
