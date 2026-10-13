"""Reconcile preparation provenance without executing any worker or candidate."""
import hashlib
import json
import subprocess
import unittest

from evaluation.matched import corpus, report, study


class PublishedPreparation(unittest.TestCase):
    def test_original_failed_freeze_and_oracle_bytes_remain_reproducible(self):
        preflight = json.loads((study.HERE / "preflight.json").read_text())
        for name, expected in preflight["original_freeze"]["sha256"].items():
            data = subprocess.check_output(["git", "show", preflight["original_revision"] + ":" + name], cwd=study.ROOT)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, name)
            if name.endswith(("corpus.py", "grader.py", "protocol.json")):
                self.assertEqual((study.ROOT / name).read_bytes(), data)
        self.assertEqual(preflight["model_dispatches"], 0)
        self.assertEqual(preflight["native_grading_controls_executed"], 0)
        self.assertEqual(preflight["worker_boundary"]["assessment"]["status"], "NOT VERIFIED")
        self.assertEqual(preflight["worker_boundary"]["assessment"]["observations"]["reads"]["sibling"], "allowed")

    def test_missing_assignments_metrics_and_source_identities_reconcile(self):
        preparation = json.loads((study.HERE / "preparation.json").read_text())
        self.assertEqual(preparation["metrics"], report.summarize(preparation["assignments"]))
        self.assertEqual(preparation["original_preflight_sha256"], hashlib.sha256((study.HERE / "preflight.json").read_bytes()).hexdigest())
        self.assertEqual(preparation["empirical_acceptance"], "INCOMPLETE")
        self.assertEqual(len(preparation["assignments"]), 16)
        for row, declared in zip(preparation["assignments"], study.ledger(), strict=True):
            for key in ("task", "arm", "sequence", "status"):
                self.assertEqual(row[key], declared[key])
            self.assertEqual(row["source_sha256"], hashlib.sha256(corpus.REQUESTS[row["task"]].encode()).hexdigest())
            self.assertIsNone(row["usage"])
            self.assertIsNone(row["workflow_seconds"])

    def test_corrected_canary_is_separate_regression_not_a_live_result(self):
        corrected = json.loads((study.HERE / "corrected-canary.json").read_text())
        self.assertEqual(corrected["model_dispatches"], 0)
        self.assertEqual(corrected["assessment"]["status"], "OBSERVED")
        self.assertEqual(set(corrected["assessment"]["observations"]["reads"].values()), {"denied"})
        self.assertIn("no study resumption", corrected["scope"])
        freeze = json.loads((study.HERE / "FREEZE.json").read_text())
        self.assertIs(freeze["live_dispatch_allowed"], False)
        for name, expected in freeze["sha256"].items():
            self.assertEqual(hashlib.sha256((study.ROOT / name).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
