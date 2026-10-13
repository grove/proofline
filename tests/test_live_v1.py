"""Offline guardrails for the one-shot native v1 campaign; no model calls."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from evaluation import live_v1 as live


class NativeV1(unittest.TestCase):
    def test_outcomes_keep_missing_observation_separate(self):
        self.assertEqual([live.outcome(h, c) for h, c in
                          [(True, True), (True, False), (False, True), (False, False), (True, None)]],
                         ["CORRECT_DELIVERY", "FALSE_ACCEPTANCE", "UNNECESSARY_BLOCKING", "FAILED_IMPLEMENTATION", "UNAVAILABLE"])

    def test_frozen_scorer_has_no_unsandboxed_candidate_invocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            product = live.tasks.seed("collision-slugs", root / "inputs")
            (product / "app.py").write_text(live.variants.candidate_code("collision-slugs", "reference"))
            original = live.b._invoke
            launches = []

            def unavailable(argv, cwd, timeout, env):
                launches.append(argv)
                return {"exit_code": None, "timed_out": True, "stdout": "", "stderr": ""}

            with patch.object(live.p.host, "run_command", unavailable), patch.object(
                    subprocess, "run", side_effect=AssertionError("Unsandboxed subprocess forbidden")):
                result = live.grade(product, "collision-slugs", root / "evaluation")
            self.assertFalse(result["available"])
            self.assertIsNone(result["passed"])
            self.assertIs(live.b._invoke, original)
            self.assertEqual(len(launches), 1)
            self.assertIn("sandbox", launches[0])
            self.assertIn("--include-managed-config", launches[0])
            self.assertIn('"enabled"=false', launches[0][3])

    def test_execute_cannot_resume_or_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results.json").write_text('{"status":"STOPPED"}')
            with patch.object(live, "STORE", root), patch.object(live, "verify", return_value={}):
                with self.assertRaisesRegex(ValueError, "No retry or resume"):
                    live.execute()


if __name__ == "__main__":
    unittest.main()
