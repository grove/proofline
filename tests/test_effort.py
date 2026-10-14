"""No live models: qualification/spending, missing slots and source disputes."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from evaluation.effort import oracle, report, study


def rows():
    return [{'task': task, 'arm': arm, 'status': 'NOT_EXECUTED', 'stages': [],
             'source_audit': None, 'total_seconds': None}
            for task in (12, 28, 41, 42) for arm in ('medium', 'high')]


class EffortStudy(unittest.TestCase):
    def test_source_preflight_and_distinct_complete_requests(self):
        for task in study.protocol()['tasks']:
            self.assertEqual(oracle.preflight(task['issue'])['status'], 'QUALIFIED')
            source = (study.HERE / 'requests' / f'issue-{task["issue"]}.md').read_bytes()
            self.assertEqual(study.host.sha256(source), task['source_sha256'])
            captured = json.loads((study.HERE / 'requests' / f'issue-{task["issue"]}.json').read_text())
            self.assertEqual(source, (captured['title']+'\n\n'+captured['body']).encode())
            self.assertEqual(captured['comments'], [])

    def test_exact_two_arms_balanced_order_and_bounded_spending(self):
        spec = study.protocol()
        self.assertEqual(spec['models'], {
            'medium': {'model': 'gpt-6-luna', 'model_reasoning_effort': 'medium'},
            'high': {'model': 'gpt-6-luna', 'model_reasoning_effort': 'high'}})
        self.assertEqual(sum(order[0] == 'medium' for order in spec['order']), 2)
        self.assertTrue(all(set(order) == {'medium', 'high'} and len(order) == 2 for order in spec['order']))
        self.assertEqual(spec['limits']['native_dispatches'], 8)
        self.assertEqual(spec['limits']['campaign_seconds'], 8*spec['limits']['assignment_seconds'])

    def test_no_inherited_or_implicit_authorization_can_dispatch(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(study, 'STORE', Path(directory)), \
                patch.object(study, 'identities', return_value='new-freeze'), \
                patch.object(study.coding, 'run', side_effect=AssertionError('model dispatched')):
            for approval in ({}, {'study_id': 'issue34-recovery-v1', 'freeze_sha256': 'old'},
                             {'study_id': study.protocol()['study_id'], 'freeze_sha256': 'new-freeze',
                              'max_native_dispatches': 8, 'max_seconds': 7200}):
                (Path(directory) / 'approval.json').write_text(json.dumps(approval))
                with self.assertRaisesRegex(ValueError, 'Separate exact-freeze'):
                    study.execute()

    def test_all_slots_and_unknown_per_correct_costs_survive(self):
        result = report.summarize(rows())
        self.assertEqual(result['assigned'], 8)
        self.assertEqual(result['recommendation'], 'INCONCLUSIVE')
        for arm in result['arms'].values():
            self.assertEqual(arm['outcomes'], {'NOT_EXECUTED': 4})
            self.assertIsNone(arm['seconds_per_correct_delivery'])
            self.assertIsNone(arm['dollars_per_correct_delivery'])
        with self.assertRaises(ValueError):
            report.summarize(rows()[:-1])
        duplicate = rows(); duplicate[0] = copy.deepcopy(duplicate[1])
        with self.assertRaises(ValueError):
            report.summarize(duplicate)

    def test_disputed_oracle_is_not_a_product_defect_or_paired_result(self):
        assignments = rows()
        assignments[0].update(status='DISPUTED', source_audit={'verdict': 'DISPUTED'})
        result = report.summarize(assignments)
        self.assertEqual(result['arms']['medium']['confirmed_defects'], 0)
        self.assertEqual(result['arms']['medium']['disputed'], 1)
        self.assertIsNone(result['paired'][0]['correct_delivery_difference'])

    def test_cached_input_is_not_double_counted(self):
        assignments = rows()
        assignments[0].update(status='CORRECT_DELIVERY', attempted=True, total_seconds=20,
            stages=[{'usage': {'input_tokens': 100, 'cached_input_tokens': 70, 'output_tokens': 10}, 'commands': {}}])
        result = report.summarize(assignments)['arms']['medium']
        self.assertEqual(result['tokens']['uncached_input_tokens'], 30)
        self.assertEqual(result['tokens']['input_tokens'], 100)
        self.assertEqual(result['seconds_per_correct_delivery'], 20)
        assignments[0]['stages'][0]['usage']['cached_input_tokens'] = 101
        with self.assertRaisesRegex(ValueError, 'Invalid native token'):
            report.summarize(assignments)

    def test_incomplete_or_disputed_source_audit_cannot_declare_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'grade').mkdir()
            (root / 'grade/observation.json').write_text('{}')
            row = {'task': 12, 'candidate_tree': 'candidate', 'seed': str(root / 'seed')}
            source = (study.HERE / 'requests/issue-12.md').read_bytes()
            required = json.loads((study.HERE / 'audit-clauses.json').read_text())['12']
            audit = {'source_sha256': study.host.sha256(source), 'candidate_tree': 'candidate',
                     'observation_sha256': study.host.sha256(b'{}'), 'verdict': 'PASS',
                     'complete_source_read': True,
                     'clauses': [{'quote': clause, 'status': 'SUPPORTED', 'evidence': 'bound observation and diff'} for clause in required]}
            study.validate_audit(row, audit)
            for change in ('missing', 'disputed', 'candidate', 'defect'):
                bad = copy.deepcopy(audit)
                if change == 'missing': bad['clauses'].pop()
                elif change == 'disputed': bad['clauses'][0]['status'] = 'DISPUTED'
                elif change == 'candidate': bad['candidate_tree'] = 'other'
                else: bad['verdict'] = 'DEFECT'
                with self.assertRaises(ValueError):
                    study.validate_audit(row, bad)

    def test_large_failure_log_keeps_exact_diagnostic_and_bounded_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / 'product'; product.mkdir()
            tests = ('import unittest\nclass Failures(unittest.TestCase):\n'
                     ' def test_subcases(self):\n'
                     '  for i in range(60):\n'
                     '   with self.subTest(i=i):\n'
                     '    self.fail("x"*2000)\n')
            program = ('import sys\nfrom pathlib import Path\n'
                       f'Path("fixture.py").write_text({tests!r})\n'
                       'sys.argv=[sys.argv[0],sys.path[0],str(Path("fixture.py").resolve())]\n'+oracle.LAUNCH)
            invocation = oracle.invoke(product, program, root / 'grade', trusted=True)
            self.assertTrue(invocation['available'])
            observed = json.loads(invocation['receipt']['stdout'])
            self.assertFalse(observed['passed'])
            self.assertEqual(observed['failure_count'], 60)
            self.assertEqual(len(observed['failures']), 20)
            raw = (root / 'grade/scratch/regressions.log').read_bytes()
            self.assertGreater(len(raw), study.host.MAX_LOG_BYTES)
            self.assertEqual(study.host.sha256(raw), observed['log_sha256'])

    def test_history_keeps_real_base_and_excludes_future_solution_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'; source.mkdir()
            (source / 'app.py').write_text('base\n')
            study.host.git(source, 'init', '--quiet', '--template=')
            study.host.git(source, 'add', '--all')
            study.host.git(source, 'commit', '--quiet', '-m', 'base')
            base = study.host.git(source, 'rev-parse', 'HEAD')
            (source / 'app.py').write_text('future solution\n')
            study.host.git(source, 'add', '--all')
            study.host.git(source, 'commit', '--quiet', '-m', 'future')
            future = study.host.git(source, 'rev-parse', 'HEAD')
            before = study.host.snapshot(source)
            product = root / 'product'; product.mkdir()
            (product / 'app.py').write_text('base\n')
            study.host.git(product, 'init', '--quiet', '--template=')
            study.snapshots.freeze(product)
            study.restore_history(source, product, base)
            self.assertEqual(study.host.git(product, 'rev-parse', 'HEAD'), base)
            self.assertFalse((product / '.git/objects/info/alternates').exists())
            with self.assertRaises(subprocess.CalledProcessError):
                study.snapshots.git_bytes(product, 'cat-file', '-e', future)
            self.assertEqual(study.host.snapshot(source), before)


if __name__ == '__main__':
    unittest.main()
