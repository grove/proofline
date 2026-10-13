"""Reproduce published candidate identities and reconcile finite live evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from evaluation import live_v1 as live
from evaluation.v1 import oracle

HERE = live.ROOT / "evaluation/results/live-v1-20261013"
# Immutable study-publication commit: keep revalidating the exact historical
# runtime, not mutable code on the current development branch.
FROZEN_PUBLICATION = "9c3684d22d4ae7ce0c87115ff9f1be7667dd374d"


class PublishedLiveV1(unittest.TestCase):
    def test_published_candidates_receipts_and_totals_reconcile(self):
        report = json.loads((HERE / "results.json").read_text())
        manifest = json.loads((HERE / "manifest.json").read_text())
        self.assertEqual(manifest["revision"], live.REVISION)
        self.assertEqual([r["task"] for r in report["assignments"]], list(live.tasks.TASKS))
        for name, expected in manifest["identities"].items():
            if name in ("codex", "python"):
                continue
            filename = "evaluation/live_v1.py" if name == "runner" else name
            try:
                pinned = subprocess.check_output(
                    ["git", "show", FROZEN_PUBLICATION + ":" + filename],
                    cwd=live.ROOT, stderr=subprocess.PIPE, timeout=15)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                self.fail("Frozen study source unavailable; checkout must include the "
                          "published Git history: " + filename + " (" + str(error) + ")")
            self.assertEqual(hashlib.sha256(pinned).hexdigest(), expected, name)
        rows = []
        invocation_ids, thread_ids = set(), set()
        for assigned in report["assignments"]:
            folder = HERE / "assignments" / assigned["task"]
            row = json.loads((folder / "result.json").read_text())
            self.assertEqual(row["status"], assigned["status"])
            if not row["model_dispatches"]:
                continue
            rows.append(row)
            self.assertLessEqual(row["receipt"]["elapsed_seconds"], 600)
            self.assertLessEqual(row["episode_with_evaluation_seconds"], 900)
            self.assertNotIn(row["receipt"]["invocation_id"], invocation_ids)
            invocation_ids.add(row["receipt"]["invocation_id"])
            if row.get("thread_id"):
                self.assertNotIn(row["thread_id"], thread_ids)
                thread_ids.add(row["thread_id"])
            for name, identity in row["candidate_files"].items():
                path = folder / "candidate" / name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), identity["sha256"])
                self.assertEqual(oct(path.stat().st_mode & 0o777), identity["mode"])
            with tempfile.TemporaryDirectory() as tmp:
                product = Path(tmp) / "product"
                shutil.copytree(folder / "candidate", product)
                live.p.host.git(product, "init", "--quiet", "--template=")
                live.p.host.git(product, "add", "--force", "--all")
                self.assertEqual(live.p.host.git(product, "write-tree"), row["candidate_tree"])
            if row["grade"]["available"]:
                self.assertEqual(len(row["grade"]["probes"]), 3 * len(oracle.VECTORS[row["task"]]) + 2)
                self.assertEqual(row["grade"]["passed"], not row["grade"]["failures"])
                self.assertEqual(live.outcome(row["handoff"], row["correct"]), row["status"])
        metrics = report["metrics"]
        self.assertEqual(metrics["assigned"], 6)
        self.assertEqual(metrics["executed"], len(rows))
        self.assertAlmostEqual(metrics["workflow_seconds"], sum(r["workflow_seconds"] for r in rows))
        self.assertEqual(metrics["independently_correct_deliveries"], sum(r["status"] == "CORRECT_DELIVERY" for r in rows))
        for key, total in metrics["known_tokens"].items():
            self.assertEqual(total, sum((r["usage"] or {}).get(key, 0) for r in rows))
        controls = json.loads((HERE / "controls.json").read_text())
        self.assertTrue(controls["offline"]["all_18_matched"])
        self.assertEqual(len(controls["native"]), 18)
        self.assertTrue(all(c["matched"] for c in controls["native"]))


if __name__ == "__main__":
    unittest.main()
