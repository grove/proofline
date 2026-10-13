"""Pinned native metadata and archived stopped results; no worker dispatch."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import zipfile

from evaluation.matched_v3 import study
from evaluation.matched_v4 import study as fresh

RESULTS = study.ROOT / 'evaluation/results/matched-v3-20261013'


class FreshMatchedStudy(unittest.TestCase):
    def test_catalog_is_frozen_and_supplied_to_native_worker(self):
        protocol = json.loads((fresh.HERE / 'protocol.json').read_text())
        path = fresh.HERE / 'model-catalog.json'
        self.assertEqual(Path(protocol['model']['model_catalog_json']).name, path.name)
        model = json.loads(path.read_text())['models'][0]
        self.assertEqual(model['slug'], protocol['model']['model'])
        self.assertIn('high', [r['effort'] for r in model['supported_reasoning_levels']])
        command = study.p.live.command(study.CODEX, Path('/inputs'), Path('/scratch'), Path('/private'), protocol['model'], implementer=True)
        self.assertIn('model_catalog_json=' + study.p.host.toml(protocol['model']['model_catalog_json']), command)

    def test_fresh_execution_requires_declaration_bound_approval(self):
        with patch.object(fresh.sys, 'argv', ['study', 'execute']), patch.object(fresh.runner, 'ROOT', Path('/nonexistent-qualification')), patch.object(fresh.runner, 'main') as execute:
            with self.assertRaisesRegex(ValueError, 'explicit approval'):
                fresh.main()
            execute.assert_not_called()

    def test_original_stopped_sources_survive_retirement_and_squash(self):
        manifest = json.loads((RESULTS / 'manifest.json').read_text())
        with zipfile.ZipFile(RESULTS / 'frozen-source.zip') as archive:
            for name in archive.namelist():
                expected = manifest['identities'].get(name)
                if expected:
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)
            original = json.loads(archive.read('evaluation/matched_v3/FREEZE.json'))
            self.assertTrue(original['live_dispatch_allowed'])
            for name, expected in original['sha256'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)
        self.assertFalse(json.loads((study.HERE / 'FREEZE.json').read_text())['live_dispatch_allowed'])

    def test_stopped_attempts_keep_all_sixteen_slots_without_effects(self):
        result = json.loads((RESULTS / 'results.json').read_text())
        self.assertEqual(result['status'], 'STOPPED')
        self.assertEqual(result['metrics'], study.report.summarize(result['assignments']))
        self.assertEqual(result['metrics']['executed'], 2)
        self.assertEqual(sum(r['status'] == 'NOT_EXECUTED' for r in result['assignments']), 14)
        self.assertIsNone(result['metrics']['paired_effects'])
        for row in result['assignments']:
            root = RESULTS / 'assignments' / f"{row['sequence']:02d}-{row['task']}-{row['arm']}"
            self.assertEqual(hashlib.sha256((root / 'source.md').read_bytes()).hexdigest(), row['source_sha256'])
            for name, entry in row['candidate_files'].items():
                if entry['kind'] == 'file':
                    self.assertEqual(hashlib.sha256((root / 'candidate' / name).read_bytes()).hexdigest(), entry['sha256'])


if __name__ == '__main__':
    unittest.main()
