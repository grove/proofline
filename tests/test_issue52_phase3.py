"""Phase 3 preparation: verify provenance and closed live-study gates only.

These structural assertions are NOT human source adjudication, native host
qualification, an independent behavioral oracle, or coding effectiveness.
"""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'evaluation/issue52'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def git_blob_sha1(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


class PhaseThreeReadiness(unittest.TestCase):
    def test_screened_real_sources_are_byte_pinned_but_not_selected(self):
        screen = read(HERE / 'fresh-task-screen.json')
        self.assertEqual(screen['status'], 'SCREENED_NO_QUALIFIED_FRESH_COHORT')
        self.assertFalse(screen['live_dispatch_allowed'])
        self.assertEqual(screen['authorized_live_assignments'], 0)
        self.assertGreaterEqual(len(screen['candidates']), 4)
        self.assertFalse(any(c['selected_for_live_study'] for c in screen['candidates']))
        self.assertEqual(
            {c['qualification'] for c in screen['candidates']},
            {'HOST_DEPENDENCIES_UNVERIFIED', 'PREREQUISITE_BLOCKED'})
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
