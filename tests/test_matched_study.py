"""No model dispatches: independent controls, accounting and campaign guardrails."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from evaluation.matched import corpus, grader, report, study


class MatchedStudy(unittest.TestCase):
    def test_four_by_four_and_missing_runs_are_not_results(self):
        rows = study.ledger()
        self.assertEqual(len(rows), 16)
        for task in corpus.REQUESTS:
            self.assertEqual({r["arm"] for r in rows if r["task"] == task}, set(report.ARMS))
        result = report.summarize(rows)
        self.assertEqual(result["empirical_acceptance"], "INCOMPLETE")
        self.assertIsNone(result["paired_effects"])
        for arm in result["arms"].values():
            self.assertEqual(arm["assigned"], 4)
            self.assertEqual(arm["executed"], 0)
            self.assertIsNone(arm["observed_delivery_rate"])
            self.assertIsNone(arm["known_tokens"])

    def test_green_repository_tests_do_not_hide_missing_batch(self):
        controls = grader.controls()
        self.assertTrue(controls["all_12_matched"], controls)
        self.assertEqual(len(controls["controls"]), 12)
        for row in controls["controls"]:
            if row["variant"] == "defective":
                self.assertTrue(row["grade"]["repository_tests_passed"])
                self.assertFalse(row["grade"]["correct"])
                self.assertTrue(all(f["seam"] == "batch" for f in row["grade"]["failures"]))

    def test_missing_attempts_and_unknown_costs_stay_in_denominator(self):
        rows = study.ledger()
        row = next(r for r in rows if r["arm"] == "proofline")
        row.update(status="UNAVAILABLE", model_dispatches=1, workflow_seconds=2)
        result = report.summarize(rows)
        self.assertEqual(result["assigned"], 16)
        self.assertEqual(result["executed"], 1)
        arm = result["arms"]["proofline"]
        self.assertEqual(arm["outcomes"], {"UNAVAILABLE": 1, "NOT_EXECUTED": 3})
        self.assertEqual(arm["observed_delivery_rate"], 0)
        self.assertEqual(arm["unknown_usage_attempts"], 1)
        self.assertIsNone(arm["seconds_per_correct_delivery"])
        self.assertIsNone(result["paired_effects"])

    def test_paired_effects_and_cached_subset_are_not_double_counted(self):
        rows = study.ledger()
        for row in rows:
            row.update(status="CORRECT_DELIVERY" if row["arm"] != "ordinary" else "FALSE_ACCEPTANCE",
                       usage={"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 10},
                       model_dispatches=1, tool_executions=2, workflow_seconds=10)
        result = report.summarize(rows)
        self.assertEqual(result["arms"]["combined"]["known_tokens"]["input_tokens"], 400)
        self.assertEqual(result["arms"]["combined"]["tokens_per_correct_delivery"], 110)
        self.assertEqual(result["paired_effects"]["proofline_minus_ordinary"]["percentage_points"], 100)
        self.assertEqual(result["paired_effects"]["interaction"]["percentage_points"], -100)
        self.assertEqual(result["paired_effects"]["intentline_minus_ordinary"]["task_bootstrap_95_percent_descriptive_interval"], [100, 100])

    def test_native_grader_never_falls_back_to_bare_candidate_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product = corpus.seed("atomic-transfers", root / "inputs", "reference")
            with patch.object(grader.host, "run_command", return_value={"exit_code": None, "timed_out": True, "stdout": "", "stderr": ""}), patch.object(
                    subprocess, "run", side_effect=AssertionError("Bare candidate execution")):
                result = grader.grade(product, "atomic-transfers", root / "grade")
            self.assertFalse(result["available"])
            self.assertIsNone(result["correct"])

    def test_seed_excludes_private_controls_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product = corpus.seed("fifo-upserts", root / "inputs")
            self.assertEqual((root / "inputs/source.md").read_text(), corpus.REQUESTS["fifo-upserts"])
            self.assertEqual((product / "app.py").read_text(), corpus.v1.APP_STUB)
            self.assertFalse((product / "service.py").read_text().find("def batch") >= 0)
            with self.assertRaises(FileExistsError):
                corpus.seed("fifo-upserts", root / "inputs")

    def test_qualifications_and_stopped_campaigns_cannot_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "results.json").write_text(json.dumps({"status": "STOPPED"}))
            with patch.object(study, "STORE", root), patch.object(study, "verify", return_value={}):
                with self.assertRaisesRegex(ValueError, "No retry or resume"):
                    study.execute()
                with self.assertRaises(FileExistsError):
                    study.qualify()

    def test_outcome_taxonomy_separates_handoff_from_finite_correctness(self):
        self.assertEqual([report.outcome(h, c) for h,c in [(True, True), (True, False), (False, True), (False, False), (True, None)]],
                         ["CORRECT_DELIVERY", "FALSE_ACCEPTANCE", "CORRECT_BUT_BLOCKED", "INCORRECT_NO_HANDOFF", "UNAVAILABLE"])


if __name__ == "__main__":
    unittest.main()
