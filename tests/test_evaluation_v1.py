"""Finite offline controls and honest non-observation for vNext baseline v1."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from evaluation.v1 import benchmark, tasks


class FrozenBaselineV1(unittest.TestCase):
    def test_population_and_preparation_ledger_are_frozen(self):
        protocol, ledger, manifest = benchmark.frozen_inputs()
        self.assertEqual(len(protocol["tasks"]), 6)
        self.assertEqual(protocol["tasks"], list(tasks.TASKS))
        self.assertEqual(protocol["model_dispatches_planned"], 6)
        self.assertEqual([row["status"] for row in ledger["assignments"]],
                         ["NOT_EXECUTED"] * 6)
        self.assertTrue(manifest["git_blob_sha1"])

    def test_modified_oracle_cannot_inherit_old_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            _, _, freeze = benchmark.frozen_inputs()
            for name in freeze["git_blob_sha1"]:
                (temp / name).write_bytes((benchmark.HERE / name).read_bytes())
            (temp / "FREEZE.json").write_text(json.dumps(freeze))
            with patch.object(benchmark, "HERE", temp):
                benchmark.frozen_inputs()
                (temp / "oracle.py").write_text("# changed grader\n")
                with self.assertRaisesRegex(ValueError, "Frozen baseline input"):
                    benchmark.frozen_inputs()

    def test_seed_excludes_controls_and_is_write_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            for task_id in tasks.TASKS:
                dest = Path(tmp) / task_id
                product = tasks.seed(task_id, dest)
                self.assertEqual((dest / "source.md").read_text(), tasks.TASKS[task_id])
                self.assertEqual(sorted(p.name for p in product.iterdir()),
                                 ["README.md", "app.py", "cli.py", "service.py", "tests"])
                self.assertNotIn("ref_", (product / "app.py").read_text())
                self.assertNotIn("VECTORS", (product / "app.py").read_text())
                with self.assertRaises(FileExistsError):
                    tasks.seed(task_id, dest)

    def test_all_eighteen_independent_controls_are_exercised(self):
        report = benchmark.run_controls()
        self.assertEqual(len(report["controls"]), 6)
        self.assertTrue(report["all_18_matched"], report)
        for row in report["controls"]:
            self.assertTrue(row["reference"]["all_finite_checks_passed"])
            self.assertTrue(row["alternative"]["all_finite_checks_passed"])
            self.assertFalse(row["defective"]["all_finite_checks_passed"])
            self.assertGreater(row["defective"]["passes"], 0)
            self.assertGreater(row["defective"]["failures"], 0)
        self.assertEqual(report["live_model_assignments_executed"], 0)

    def test_unavailable_model_is_not_reported_as_failure_or_success(self):
        record = benchmark.summarize_unexecuted()
        self.assertEqual(record["assigned"], 6)
        self.assertEqual(record["executed"], 0)
        self.assertEqual(record["unexecuted"], 6)
        self.assertEqual(record["status"], "PREPARED_ONLY_NO_LIVE_MODEL_ACCESS")
        for field in ("independently_correct_deliveries", "correct_delivery_rate",
                      "false_acceptances", "unnecessary_blocks",
                      "elapsed_seconds_per_correct_delivery",
                      "reported_tokens_per_correct_delivery",
                      "operator_effort_seconds", "dollars_per_correct_delivery"):
            self.assertIsNone(record[field], field)

    def test_public_cli_reports_incomplete_observations(self):
        proc = subprocess.run([sys.executable, "-B", str(benchmark.HERE / "benchmark.py"), "report"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["executed"], 0)


if __name__ == "__main__":
    unittest.main()
