"""Phase 3 preparation: verify provenance and closed live-study gates only.

These structural assertions are NOT human source adjudication, native host
qualification, an independent behavioral oracle, or coding effectiveness.
"""
import hashlib
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import Mock, patch
import zipfile

from evaluation.issue52 import native, qualify


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'evaluation/issue52'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def git_blob_sha1(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


class PhaseThreeReadiness(unittest.TestCase):
    def test_pinned_codex_reaches_catalog_both_roles_and_roundtrip(self):
        runner = Mock()
        runner.boundary.return_value = {}
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.codex').mkdir()
            (home / '.codex/models_cache.json').write_text('{}')
            output = home / 'observation'
            with patch.object(native.Path, 'home', return_value=home), \
                    patch.object(qualify, 'CODEX', '/pinned/codex'), \
                    patch.object(qualify, 'input_identities', return_value={}), \
                    patch.object(native, 'bound_module', return_value=runner) as bind, \
                    patch.object(native.codex_catalog, 'readback', return_value={}) as catalog, \
                    patch.object(native.producer, 'producer_files', return_value={}), \
                    patch.object(native.host, 'git'), \
                    patch.object(qualify.snapshots, 'freeze'), \
                    patch.object(native.preflight, 'check_adapter_roundtrip',
                                 side_effect=ValueError('review pending')) as roundtrip:
                with self.assertRaisesRegex(ValueError, 'review pending'):
                    native.run(output)
                self.assertEqual(bind.call_args.kwargs['CODEX'], '/pinned/codex')
                self.assertEqual(catalog.call_args.args[0], '/pinned/codex')
                self.assertEqual([c.kwargs for c in runner.boundary.call_args_list],
                                 [{}, {'worker': True}])
                self.assertEqual(roundtrip.call_args.kwargs['codex'], '/pinned/codex')
            self.assertEqual(read(output / 'qualification.json')['status'], 'STOPPED_NOT_QUALIFIED')

    def test_new_shortlist_does_not_become_a_live_freeze_or_replace_history(self):
        cohort = read(HERE / 'candidate-cohort.json')
        self.assertEqual(cohort['status'], 'NOT_QUALIFIED')
        self.assertFalse(cohort['live_dispatch_allowed'])
        self.assertIsNone(cohort['semantic_reviewer'])
        self.assertIsNone(cohort['live_freeze'])
        self.assertEqual(len(cohort['tasks']), 4)
        self.assertTrue(any(t['category'] == 'straightforward-documentation-control'
                            for t in cohort['tasks']))
        for task in cohort['tasks']:
            raw = (ROOT / task['original_request_file']).read_bytes()
            self.assertEqual(git_blob_sha1(raw), task['original_request_blob_sha'])
            capture = read(ROOT / task['issue_capture_file'])
            self.assertIn(capture['body'].encode(), raw)
            for comment in capture['comments']:
                self.assertIn(comment['body'].encode(), raw)
            self.assertFalse(task['selected_for_live_study'])
            self.assertEqual(task['independent_review'], 'PENDING')
        slots = cohort['proposed_assignments']
        self.assertEqual(len(slots), 16)
        self.assertEqual([r['arm'] for r in slots[:4]], ['A'] * 4)
        self.assertEqual({(r['task'], r['arm']) for r in slots},
                         {(t['id'], a) for t in cohort['tasks'] for a in 'ABCD'})
        self.assertTrue(all(r['status'] == 'NOT_EXECUTED' and r['independent_grade'] is None
                            and r['actual_billed_cost'] == 'UNKNOWN' for r in slots))

    def test_retained_native_controls_do_not_become_semantic_approval(self):
        folder = ROOT / 'evaluation/results/issue52-phase3'
        result = read(folder / 'results.json')
        self.assertEqual(result['status'], 'NOT_QUALIFIED')
        self.assertEqual(result['model_dispatches'], 0)
        self.assertFalse(result['live_dispatch_allowed'])
        self.assertIsNone(result['independent_semantic_reviewer'])
        self.assertEqual(result['independent_semantic_review'], 'PENDING')
        self.assertEqual(result['qualified_live_tasks'], [])
        self.assertEqual(hashlib.sha256((HERE / 'candidate-cohort.json').read_bytes()).hexdigest(),
                         result['candidate_manifest_sha256'])
        for name, digest in result['archives'].items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
            with zipfile.ZipFile(folder / name) as archive:
                members = result['evidence_members_sha256'][name]
                self.assertEqual(set(archive.namelist()), set(members))
                for member, expected in members.items():
                    self.assertEqual(hashlib.sha256(archive.read(member)).hexdigest(), expected)
        self.assertEqual(len(result['controls']), 4)
        for control in result['controls']:
            self.assertTrue(control['matched'])
            observation = control['parsed_observation']
            self.assertIsNone(observation['error'])
            self.assertIsNone(observation['whole_source_correct'])
            self.assertEqual(observation['probe_passed'],
                             control['variant'] in ('reference', 'alternative'))
            if control['variant'] != 'original':
                self.assertEqual(control['existing_suite']['exit_code'], 0)
        self.assertEqual(set(result['decisions'].values()), {'INCONCLUSIVE'})

    def test_screened_real_sources_are_byte_pinned_but_not_selected(self):
        screen = read(HERE / 'fresh-task-screen.json')
        self.assertEqual(screen['status'], 'SCREENED_NO_QUALIFIED_FRESH_COHORT')
        self.assertFalse(screen['live_dispatch_allowed'])
        self.assertEqual(screen['authorized_live_assignments'], 0)
        self.assertGreaterEqual(len(screen['candidates']), 4)
        self.assertFalse(any(c['selected_for_live_study'] for c in screen['candidates']))
        self.assertEqual(
            {c['qualification'] for c in screen['candidates']},
            {'BUILD_QUALIFICATION_INCOMPLETE', 'PREREQUISITE_BLOCKED'})
        self.assertEqual(len({c['id'] for c in screen['candidates']}), len(screen['candidates']))
        for row in screen['candidates']:
            with self.subTest(task=row['id']):
                captured = ROOT / row['original_request_file']
                raw = captured.read_bytes()
                self.assertTrue(raw.startswith(b'# '))
                self.assertEqual(git_blob_sha1(raw), row['original_request_blob_sha'])
                self.assertEqual(len(row['base_commit']), 40)
                self.assertEqual(len(row['base_tree']), 40)
                self.assertEqual(row['independent_oracle'], 'NOT_AUTHORED')
                self.assertEqual(row['native_control_receipts'], 'NOT_EXECUTED')

    def test_review_findings_are_source_cited_and_remain_unapproved(self):
        review = read(HERE / 'source-review-packet.json')
        self.assertEqual(review['cohort_qualification'], 'NOT_QUALIFIED')
        self.assertIsNone(review['reviewer_name'])
        self.assertIsNone(review['reviewer_attestation'])
        self.assertFalse(review['live_dispatch_allowed'])
        self.assertEqual(len(review['source_reviews']), 4)
        original = read(HERE / 'task-manifest.json')
        task_identities = {row['id']: row['source_blob_sha'] for row in original['tasks']}
        self.assertEqual({row['task'] for row in review['source_reviews']}, set(task_identities))
        all_finding_ids = []
        for row in review['source_reviews']:
            with self.subTest(task=row['task']):
                raw = (ROOT / row['source_file']).read_bytes()
                self.assertEqual(git_blob_sha1(raw), task_identities[row['task']])
                self.assertEqual(row['source_blob_sha'], task_identities[row['task']])
                self.assertEqual(row['semantic_qualification'], 'NOT_QUALIFIED')
                self.assertEqual(row['candidate_grading'], 'NOT_PERFORMED')
                self.assertGreaterEqual(len(row['findings']), 2)
                for finding in row['findings']:
                    all_finding_ids.append(finding['id'])
                    self.assertEqual(raw.count(finding['source_fragment'].encode('utf-8')), 1)
                    self.assertEqual(finding['proposal_status'], 'UNREVIEWED_COVERAGE_GAP')
                    self.assertIsNone(finding['independent_review'])
        self.assertEqual(len(all_finding_ids), len(set(all_finding_ids)))
        self.assertEqual(len(all_finding_ids), review['findings_total'])

    def test_original_phase_one_and_two_assignments_are_still_unexecuted(self):
        protocol = read(HERE / 'protocol.json')
        phase2 = read(HERE / 'phase2.json')
        evidence = read(ROOT / 'evaluation/results/issue52-phase2/results.json')
        self.assertFalse(protocol['live_dispatch_allowed'])
        self.assertFalse(phase2['live_dispatch_allowed'])
        self.assertFalse(evidence['live_dispatch_allowed'])
        self.assertEqual(evidence['model_dispatches'], 0)
        self.assertEqual(evidence['live_assignments_executed'], 0)
        self.assertEqual(len(evidence['assignments']), 16)
        self.assertTrue(all(row['status'] == 'NOT_EXECUTED'
                            for row in evidence['assignments']))


if __name__ == '__main__':
    unittest.main()
