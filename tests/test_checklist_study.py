"""Model-free cohort/source/accounting/authorization checks for issue #46."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.checklist import oracle, study


def rows():
    return [{'task': task, 'arm': arm, 'status': 'NOT_EXECUTED', 'stages': [],
             'source_audit': None, 'total_seconds': None}
            for task in study.TASKS for arm in study.ARMS]


class ChecklistStudy(unittest.TestCase):
    def test_unchanged_real_requests_source_grounding_and_private_inventory(self):
        spec = study.protocol()
        checklists = json.loads((study.HERE / 'checklists.json').read_text())
        clauses = json.loads((study.HERE / 'audit-clauses.json').read_text())
        for task in spec['tasks']:
            issue = task['issue']
            source = (study.HERE / 'requests' / f'issue-{issue}.md').read_bytes()
            captured = json.loads((study.HERE / 'requests' / f'issue-{issue}.json').read_text())
            self.assertEqual(source, (captured['title']+'\n\n'+captured['body']).encode())
            self.assertEqual(hashlib.sha256(source).hexdigest(), task['source_sha256'])
            self.assertEqual(oracle.preflight(issue)['status'], 'QUALIFIED')
            self.assertTrue(8 <= len(checklists[str(issue)]) <= 12)
            for item in checklists[str(issue)]:
                for ref in item['source_refs']:
                    quote = ref['quote'].encode()
                    self.assertEqual(source.count(quote), 1)
                    actual = '\n'.join(source.decode().splitlines()[ref['line_start']-1:ref['line_end']])
                    self.assertEqual(actual, ref['quote'])
            self.assertTrue(clauses[str(issue)])
            self.assertTrue(all(source.count(clause.encode()) == 1 for clause in clauses[str(issue)]))
            # New hidden probes/checklists must not be present in any task seed.
            tree = study.snapshots.git_bytes(study.ROOT, 'ls-tree', '-r', '--name-only', task['base_commit'])
            self.assertNotIn(b'evaluation/checklist/', tree)

    def test_same_model_balanced_order_and_all_slots(self):
        spec = study.protocol()
        self.assertEqual(spec['models']['ordinary'], spec['models']['checklist'])
        self.assertEqual(spec['models']['ordinary']['model_reasoning_effort'], 'medium')
        self.assertEqual(sum(order[0] == 'ordinary' for order in spec['order']), 2)
        self.assertTrue(all(set(order) == set(study.ARMS) for order in spec['order']))
        self.assertEqual(spec['limits']['campaign_seconds'], 8*spec['limits']['assignment_seconds'])
        result = study.summarize(rows())
        self.assertEqual(result['assigned'], 8)
        self.assertEqual(result['recommendation'], 'INCONCLUSIVE')
        self.assertEqual(set(result['arms']), set(study.ARMS))
        for arm in result['arms'].values():
            self.assertEqual(arm['outcomes'], {'NOT_EXECUTED': 4})
            self.assertIsNone(arm['total_seconds_per_correct_delivery_including_preparation'])
        with self.assertRaises(ValueError):
            study.summarize(rows()[:-1])
        duplicate = rows(); duplicate[0] = copy.deepcopy(duplicate[1])
        with self.assertRaises(ValueError):
            study.summarize(duplicate)

    def test_unknown_preparation_cannot_be_free_or_establish_a_winner(self):
        assigned = rows()
        for row in assigned:
            row.update(attempted=True, status='CORRECT_DELIVERY', total_seconds=2,
                       stages=[{'usage': {'input_tokens': 100, 'cached_input_tokens': 60,
                                         'output_tokens': 20}, 'commands': {}}])
        result = study.summarize(assigned)
        self.assertEqual(result['recommendation'], 'INCONCLUSIVE')
        self.assertEqual(result['arms']['checklist']['tokens']['uncached_input_tokens'], 160)
        self.assertIsNone(result['checklist_preparation_tokens'])
        self.assertIsNone(result['arms']['checklist']['total_tokens_per_correct_delivery_including_preparation'])

    def test_no_old_approval_self_review_or_unbounded_authorization(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(study, 'STORE', Path(folder)), \
                patch.object(study, 'identities', return_value='new-freeze'):
            review = {'freeze_sha256': 'new-freeze', 'decision': 'QUALIFIED',
                      'reviewer': 'independent human', 'independent_of_organizer_and_workers': True,
                      'reviewed_tasks': list(study.TASKS), 'adjudication_reference': 'written-review.md'}
            for decision in ({}, {**review, 'reviewer': 'organizer: /root'},
                             {**review, 'reviewer': 'organizer: /root (Codex), also probe author'},
                             {**review, 'freeze_sha256': 'issue38-freeze'}):
                (Path(folder) / 'review.json').write_text(json.dumps(decision))
                with self.assertRaisesRegex(ValueError, 'Independent exact-freeze'):
                    study.approved()
            (Path(folder) / 'review.json').write_text(json.dumps(review))
            approval = {'study_id': study.protocol()['study_id'], 'freeze_sha256': 'new-freeze',
                        'max_native_dispatches': 8, 'max_seconds': 9600,
                        'host': study.protocol()['host'], 'models': study.protocol()['models'],
                        'user_authorization': 'Explicit bounded user approval'}
            for decision in ({}, {**approval, 'max_seconds': 7200},
                             {**approval, 'host': {}}, {**approval, 'models': {}},
                             {**approval, 'user_authorization': ''}):
                (Path(folder) / 'approval.json').write_text(json.dumps(decision))
                with self.assertRaisesRegex(ValueError, 'Fresh explicit exact-freeze'):
                    study.approved()
            (Path(folder) / 'approval.json').write_text(json.dumps(approval))
            self.assertEqual(study.approved(), approval)

    def test_checklist_distribution_preserves_source_and_matches_worker_links(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(study, 'STORE', Path(folder)), \
                patch.object(study.existing, 'capture_with_history', return_value=('base', 'base')):
            root = Path(folder)
            for arm in study.ARMS:
                repo = root / f'01-10-{arm}' / 'seed'
                product = root / arm / 'inputs' / 'product'; product.parent.mkdir(parents=True)
                guidance = product.parent / 'guidance.md'; guidance.write_text('common')
                source = product.parent / 'source.md'; source.write_text('complete original')
                study.capture(repo, product)
                self.assertEqual(source.read_text(), 'complete original')
                text = guidance.read_text()
                if arm == 'ordinary':
                    self.assertEqual(text, 'common')
                else:
                    self.assertIn('Acceptance checklist', text)
                    self.assertIn('(source.md#L', text)
                    self.assertNotIn('../requests/', text)

    def test_missing_private_cases_cannot_inherit_a_forged_green_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / 'grade'
            (directory / 'scratch').mkdir(parents=True)
            receipts = directory / 'scratch/probe-receipts.json'
            receipts.write_text('[]\n')
            payload = {'cases': [{'id': 'status-interface', 'passed': True}],
                       'passed': True, 'unknown': [],
                       'receipts_sha256': hashlib.sha256(receipts.read_bytes()).hexdigest()}
            invocation = {'available': True, 'receipt': {'exit_code': 0,
                          'stdout': json.dumps(payload)}, 'inputs_unchanged': True}
            with patch.object(oracle, 'invoke', return_value=invocation):
                result = oracle.observe(Path(folder), 11, directory)
            self.assertTrue(result['invocation']['available'])
            self.assertFalse(result['observed']['passed'])
            self.assertIn('native-check', result['observed']['unknown'])
            self.assertIsNone(result['correct'])


if __name__ == '__main__':
    unittest.main()
