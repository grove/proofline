"""Offline qualification guards; no model, native sandbox or campaign dispatch."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from evaluation.issue52 import oracles, qualify, validate


class PhaseTwo(unittest.TestCase):
    def test_original_phase_one_and_all_slots_remain_unexecuted(self):
        self.assertEqual(validate.check()['assignments'], 16)
        self.assertFalse(qualify.spec()['live_dispatch_allowed'])
        self.assertEqual(set(qualify.CLAUSES), set(oracles.CASES))
        for task in oracles.CASES:
            binding = qualify.source_binding(task)
            self.assertEqual(binding['structural_preflight']['status'], 'QUALIFIED')
            self.assertEqual(binding['semantic_qualification'], 'NOT_QUALIFIED')
            self.assertEqual(binding['independent_review'], 'PENDING')

    def test_changed_source_identity_blocks_before_candidate_execution(self):
        spec = copy.deepcopy(qualify.spec())
        spec['tasks'][0]['source_blob_sha'] = '0' * 40
        with patch.object(qualify, 'spec', return_value=spec), self.assertRaisesRegex(ValueError, 'request blob'):
            qualify.source_binding('feedback')

    def test_native_observation_never_upgrades_incomplete_or_error_output(self):
        good = [{'id': n, 'passed': True, 'error': None} for n in oracles.CASES['feedback']]
        for rows, available in [(good, True), (good[:-1], False),
                                ([{**r, 'error': 'ImportError'} for r in good], False),
                                ([{**r, 'passed': 'yes'} for r in good], False)]:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as tmp:
                result = {'available': True, 'receipt': {'exit_code': 0, 'stdout': json.dumps({'cases': rows})}}
                with patch.object(qualify, 'invoke', return_value=result):
                    observed = qualify.observe(Path(tmp), 'feedback', Path(tmp), native=True, seconds=1)
                self.assertEqual(observed['available'], available)
                self.assertIsNone(observed['correct'])
                self.assertEqual(observed['model_dispatches'], 0)

    def test_bundled_probes_pass_current_product_without_an_inference_call(self):
        # Individual probes exercise the public existing seams, not copied production logic.
        with tempfile.TemporaryDirectory() as tmp:
            product = Path(tmp) / 'product'
            shutil.copytree(qualify.ROOT / 'checks', product / 'checks',
                            ignore=shutil.ignore_patterns('__pycache__'))
            result = qualify.observe(product, 'next-check-hints', Path(tmp)/'observation', native=False, seconds=20)
        self.assertTrue(result['available'], result)
        self.assertTrue(result['probes_passed'], result)

    def test_existing_evidence_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileExistsError):
            qualify.controls(Path(tmp))

    def test_published_receipts_sources_and_unexecuted_denominator_reconcile(self):
        folder = qualify.ROOT / 'evaluation/results/issue52-phase2'
        report = json.loads((folder / 'results.json').read_text())
        self.assertFalse(report['live_dispatch_allowed'])
        self.assertEqual(report['model_dispatches'], 0)
        self.assertEqual(len(report['assignments']), 16)
        self.assertTrue(all(r['status'] == 'NOT_EXECUTED' and r['independent_grade'] is None
                            for r in report['assignments']))
        for name, digest in report['archives'].items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
        with zipfile.ZipFile(folder / 'source-v2.zip') as base, \
                zipfile.ZipFile(folder / 'source-v3-delta.zip') as delta:
            for name, digest in report['phase2_inputs_sha256'].items():
                raw = delta.read(name) if name in delta.namelist() else base.read(name)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, name)
        with zipfile.ZipFile(folder / 'evidence.zip') as evidence:
            self.assertEqual(set(evidence.namelist()), set(report['evidence_sha256']))
            for name, digest in report['evidence_sha256'].items():
                self.assertEqual(hashlib.sha256(evidence.read(name)).hexdigest(), digest, name)
            rows = report['controls']
            self.assertEqual(len(rows), 12)
            self.assertEqual({(r['task'], r['variant']) for r in rows},
                             {(t, v) for t in oracles.CASES for v in ('reference', 'alternative', 'defective')})
            for row in rows:
                result = json.loads(evidence.read('native-controls-v3/'+row['observation']))
                self.assertTrue(row['matched'] and result['available'])
                self.assertEqual(result['probes_passed'], row['variant'] != 'defective')
                self.assertIsNone(result['correct'])
            self.assertTrue(any(r.get('green_existing_suite') for r in rows))
            self.assertEqual(report['original_suite']['exit_code'], 0)
            host = json.loads(evidence.read('native-host-v2/qualification.json'))
            self.assertEqual(host['roundtrip']['check_status'], 'CHECKS PASSED')
            self.assertTrue(all(b['assessment']['status'] == 'OBSERVED' for b in host['boundaries'].values()))
            text = evidence.read('native-host-v2/status-readback.log').decode()
            self.assertIn('NOT DEMONSTRATED', text)
            self.assertIn('unverified Intentline', text)
            self.assertIn('overall coverage UNKNOWN', text)
        self.assertEqual(set(report['decisions'].values()), {'INCONCLUSIVE'})


if __name__ == '__main__':
    unittest.main()
