"""Independent public artifact identities; never execute delivered candidate code."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import stat
import unittest
from unittest.mock import patch
import zipfile

from evaluation.matched import report

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'evaluation/results/matched-v4-20261013'


def git_object(kind, data):
    return hashlib.sha1(kind + b' ' + str(len(data)).encode() + b'\0' + data).digest()


def git_tree(root):
    entries = []
    for path in root.iterdir():
        if path.is_symlink():
            mode, digest, key = b'120000', git_object(b'blob', str(path.readlink()).encode()), path.name.encode()
        elif path.is_dir():
            mode, digest, key = b'40000', bytes.fromhex(git_tree(path)), (path.name + '/').encode()
        else:
            mode = b'100755' if path.stat().st_mode & stat.S_IXUSR else b'100644'
            digest, key = git_object(b'blob', path.read_bytes()), path.name.encode()
        entries.append((key, mode + b' ' + path.name.encode() + b'\0' + digest))
    return git_object(b'tree', b''.join(value for _, value in sorted(entries))).hex()

@unittest.skipUnless(RESULTS.exists(), 'Public native cohort not yet published')
class PublishedMatchedResults(unittest.TestCase):
    RESULTS = RESULTS
    FREEZE = "evaluation/matched_v4/FREEZE.json"

    def test_original_source_archive_matches_pre_dispatch_manifest(self):
        manifest = json.loads((self.RESULTS / 'manifest.json').read_text())
        with zipfile.ZipFile(self.RESULTS / 'frozen-source.zip') as archive:
            for name in archive.namelist():
                expected = manifest['identities'].get(name)
                if expected:
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)
            freeze_data = archive.read(self.FREEZE)
            approval = json.loads((self.RESULTS / 'approval.json').read_text())
            self.assertEqual(hashlib.sha256(freeze_data).hexdigest(), approval['freeze_sha256'])
            for name, expected in json.loads(freeze_data)['sha256'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)

    def test_all_assignments_metrics_and_exact_candidates_reconcile(self):
        result = json.loads((self.RESULTS / 'results.json').read_text())
        self.assertEqual(result['metrics'], report.summarize(result['assignments']))
        self.assertEqual(len(result['assignments']), 16)
        manifest = json.loads((self.RESULTS / 'manifest.json').read_text())
        declared = {r['sequence']: r for r in manifest['assignments']}
        self.assertEqual({r['sequence'] for r in result['assignments']}, set(range(1, 17)))
        for row in result['assignments']:
            for name in ('source_sha256', 'base_tree'):
                self.assertEqual(row[name], declared[row['sequence']][name])
            folder = self.RESULTS / 'assignments' / f"{row['sequence']:02d}-{row['task']}-{row['arm']}"
            self.assertEqual(json.loads((folder / 'result.json').read_text()), row)
            self.assertEqual(hashlib.sha256((folder / 'source.md').read_bytes()).hexdigest(), row['source_sha256'])
            if 'candidate_tree' not in row:
                continue
            self.assertEqual(git_tree(folder / 'candidate'), row['candidate_tree'])
            self.assertEqual(hashlib.sha256((folder / 'prompt.txt').read_bytes()).hexdigest(), row['receipt']['prompt_sha256'])
            if (folder / 'check.json').exists():
                check = json.loads((folder / 'check.json').read_text())
                self.assertEqual(check['candidate_tree'], row['candidate_tree'])
                self.assertEqual(check['model_dispatches'], 0)

    def test_native_controls_and_boundaries_are_observed_before_dispatch(self):
        controls = json.loads((self.RESULTS / 'controls.json').read_text())
        self.assertTrue(controls['all_12_matched'])
        self.assertEqual(len(controls['controls']), 12)
        self.assertEqual(controls['model_dispatches'], 0)
        qualification = json.loads((self.RESULTS / 'qualification.json').read_text())
        for name in ('worker', 'grader'):
            self.assertEqual(qualification[name]['assessment']['status'], 'OBSERVED')
        self.assertEqual(qualification['producer_adapter_check']['model_dispatches'], 0)
        self.assertEqual(qualification['producer_adapter_check']['promise_evidence']['coverage_completeness'], 'UNKNOWN')


@unittest.skipUnless((ROOT / 'evaluation/results/matched-v5-20261013').exists(), 'Final native cohort not yet published')
class PublishedFinalMatchedResults(PublishedMatchedResults):
    RESULTS = ROOT / 'evaluation/results/matched-v5-20261013'
    FREEZE = 'evaluation/matched_v5/FREEZE.json'

    def test_complete_finite_cohort_keeps_every_assignment_and_retires_dispatch(self):
        result = json.loads((self.RESULTS / 'results.json').read_text())
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['metrics']['executed'], 16)
        self.assertEqual(result['metrics']['empirical_acceptance'], 'OBSERVED_FINITE_STUDY')
        self.assertTrue(all(r['grade']['available'] for r in result['assignments']))
        self.assertFalse(json.loads((ROOT / 'evaluation/matched_v5/FREEZE.json').read_text())['live_dispatch_allowed'])

    def test_report_recomputes_published_metrics_without_native_dispatch(self):
        from evaluation.matched_v5 import study
        output = io.StringIO()
        with patch.object(study.sys, 'argv', ['study', 'report']), patch.object(study.runner, 'main') as native, contextlib.redirect_stdout(output):
            self.assertEqual(study.main(), 0)
        native.assert_not_called()
        result = json.loads((self.RESULTS / 'results.json').read_text())
        self.assertEqual(json.loads(output.getvalue()), result['metrics'])


if __name__ == '__main__':
    unittest.main()
