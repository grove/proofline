import copy
from pathlib import Path
import tempfile
import unittest

from checks import s6_compare as s6
from checks.s6_regression_audit import probe, timestamp_probe, version_probe, evaluate
from checks.s6_results import resources


class ReadbackTests(unittest.TestCase):
    def test_preliminary_cost_includes_failures_without_charging_carried_copies(self):
        failed = {'id': 'original', 'outcome': 'FAILED', 'end_to_end_seconds': 20,
                  'delivery': {'model_dispatches': 2, 'stages': [{'usage': {
                      'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 10}}]}}
        carried = {**failed, 'id': 'copy', 'carried_from': {'original_id': 'original'}}
        total = resources([{'assignments': [failed]}, {'assignments': [carried, {
            'id': 'unexecuted', 'outcome': 'NOT EXECUTED'}]}])
        self.assertEqual(total['original_episodes'], 1)
        self.assertEqual(total['known_workflow_seconds'], 20)
        self.assertEqual(total['known_native_dispatches'], 2)
        self.assertEqual(total['known_tokens']['input_tokens'], 100)
        self.assertEqual(total['unknown_usage_dispatches'], 1)
        self.assertIsNone(total['cost_usd'])
        with self.assertRaises(ValueError):
            resources([{'assignments': [failed, copy.deepcopy(failed)]}])

    def test_large_csv_field_is_a_real_regression_not_a_false_rejection(self):
        item = probe()
        item['good'] = 'import csv,io\ndef process(data):\n    rows=list(csv.reader(io.StringIO(data)))\n    return [dict(zip(rows[0],row)) for row in rows[1:]]\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            limited = root / 'limited'
            s6.seed(limited, item, 'good')
            result = s6.evaluate(limited, item, directory=root / 'limited-evaluation')
            self.assertTrue(result['observed'])
            self.assertFalse(result['correct'])
            fixed = {**item, 'good': item['good'].replace('def process(data):',
                'def process(data):\n    csv.field_size_limit(max(csv.field_size_limit(), len(data)))')}
            s6.seed(root / 'fixed', fixed, 'good')
            result = s6.evaluate(root / 'fixed', item, directory=root / 'fixed-evaluation')
            self.assertTrue(result['observed'])
            self.assertTrue(result['correct'])

    def test_large_native_receipt_check_emits_only_the_verdict(self):
        item = probe()
        code = 'def process(data):\n    return [{"name": "x" * 131073}]\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            s6.seed(root / 'product', {**item, 'good': code}, 'good')
            result = evaluate(root / 'product', item, None, root / 'evaluation')
            self.assertTrue(result['observed'])
            self.assertTrue(result['correct'])
            self.assertEqual(result['observations'], {'library_correct': True, 'cli_correct': True})

    def test_ordinal_date_control_matches_independently_authored_utc_value(self):
        item = timestamp_probe()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            s6.seed(root / 'product', item, 'good')
            result = s6.evaluate(root / 'product', item, directory=root / 'evaluation')
            self.assertTrue(result['observed'])
            self.assertTrue(result['correct'])

    def test_long_version_component_rejection_is_a_real_defect(self):
        item = version_probe()
        limited = 'def process(data):\n    return sorted(data,key=lambda v:tuple(map(int,v.split("."))))\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, code, expected in [('limited', limited, False), ('valid', item['good'], True)]:
                s6.seed(root / name, {**item, 'good': code}, 'good')
                result = s6.evaluate(root / name, item, directory=root / (name + '-evaluation'))
                self.assertTrue(result['observed'])
                self.assertEqual(result['correct'], expected)
