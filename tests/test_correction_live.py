"""Opt-in native same-thread correction control, deliberately retaining a seed defect.

This qualifies transport and isolation, not how often ordinary coding needs repair.
Run with PROOFLINE_CORRECTION_LIVE=1 on the supported authenticated macOS host.
Evidence is retained under a new system-temporary directory, never cleaned up.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

from checks import candidate_snapshot, local_run as runner


@unittest.skipUnless(sys.platform=='darwin' and os.environ.get('PROOFLINE_CORRECTION_LIVE')=='1',
                     'opt-in authenticated native correction qualification')
class NativeCorrectionControl(unittest.TestCase):
    def test_seeded_assertion_is_corrected_on_original_thread(self):
        root=Path(tempfile.mkdtemp(prefix='proofline-correction-control-')).resolve()
        repo=root/'source';repo.mkdir()
        (repo/'tiny.py').write_text('answer = 0\n')
        runner.host.git(repo,'init','--quiet','--template=')
        candidate_snapshot.freeze(repo)
        before=runner.host.snapshot(repo)
        source=(
            'This is a deliberate two-turn native qualification control, not an ordinary delivery.\n'
            'The final product must export answer = 42 from tiny.py. Preserve that interface.\n'
            'For the first turn ONLY, retain the seeded answer = 0 defect and create phase.txt '
            'containing first handoff. Report completed=true for that first qualification phase '
            'so the host can observe the real assertion failure; do not fix answer yet.\n'
            'When the host resumes you with actual failing check evidence, correct tiny.py '
            'to answer = 42 in the NEW product path named by the new prompt. '
            'Leave phase.txt intact. This is the only correction turn.\n')
        checks=[[str(Path(sys.executable).resolve()),'-B','-c',
                 'from tiny import answer; assert answer == 42, "expected 42; observed %s" % answer'],
                [str(Path(sys.executable).resolve()),'-B','-c',
                 'from pathlib import Path; assert Path("phase.txt").read_text().strip() == "first handoff"']]
        record=runner.run(repo,source,checks,root/'run',seconds=300,
                          stage_seconds=120,check_seconds=15,correct_once=True)
        print('Native correction control evidence: '+str(root/'run/report.json'),flush=True)
        self.assertEqual(record['status'],'CHECKS PASSED',record)
        self.assertEqual(runner.inspect(root/'run/report.json')['status'],'CHECKS PASSED')
        self.assertEqual(record['model_dispatches'],2)
        self.assertEqual(record['stages'][0]['thread_id'],record['stages'][1]['thread_id'])
        initial=runner.inspect(root/'run/initial/report.json')
        self.assertEqual(initial['status'],'CHECKS FAILED')
        self.assertEqual(initial['observations'][0]['returncode'],1)
        self.assertIn('AssertionError: expected 42; observed 0',
                      initial['observations'][0]['receipts'][0]['stderr'])
        self.assertEqual(len(record['observations']),len(checks))
        self.assertNotEqual(initial['candidate_tree'],record['candidate_tree'])
        for directory in ('coding','correction'):
            import json
            boundary=json.loads((root/'run'/directory/'preflight/report.json').read_text())
            self.assertEqual(boundary['assessment']['status'],'OBSERVED')
        self.assertEqual(runner.host.snapshot(repo),before)
        self.assertLess(record['elapsed_seconds'],record['limits']['seconds'])
