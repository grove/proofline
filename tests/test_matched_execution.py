"""Exercise all arm interfaces with simulated transport; no empirical observations."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.matched import study


class MatchedExecution(unittest.TestCase):
    def test_all_arms_use_same_checks_and_keep_correct_but_blocked_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            here, store = root / "preparation", root / "study"
            here.mkdir(); store.mkdir()
            (here / "protocol.json").write_bytes((study.HERE / "protocol.json").read_bytes())
            # This test fixture alone enables simulated dispatch; the published study is retired.
            (here / "FREEZE.json").write_text('{"live_dispatch_allowed":true}')
            rows, frozen = study.ledger(), []
            for row in rows:
                inputs = store / f'{row["sequence"]:02d}-{row["arm"]}' / "inputs"
                product = study.initialize(row["task"], inputs)
                row["inputs"] = str(inputs)
                frozen.append({"seed_snapshot": study.p.host.snapshot(product),
                               "source_sha256": study.p.host.sha256((inputs / "source.md").read_bytes()),
                               "checks": study.selected_checks(row["task"])})
            (store / "results.json").write_text(json.dumps({"status": "QUALIFIED_NOT_DISPATCHED", "assignments": rows}))
            manifest = {"protocol": study.read_protocol(), "assignments": frozen}

            def launch(argv, prompt, private, seconds):
                path = private / "events.jsonl"
                path.write_text('{"type":"item.completed","item":{"type":"command_execution"}}\n')
                return {"events_path": str(path)}

            def inspect(path):
                return {"status": "CHECKS FAILED" if "-proofline" in str(path) else "CHECKS PASSED"}

            with ExitStack() as patches:
                for owner, name, value in [(study, "HERE", here), (study, "STORE", store)]:
                    patches.enter_context(patch.object(owner, name, value))
                patches.enter_context(patch.object(study, "verify", return_value=manifest))
                patches.enter_context(patch.object(study, "boundary", return_value={}))
                patches.enter_context(patch.object(study, "producer_files", return_value={}))
                worker = patches.enter_context(patch.object(study.p.live, "launch", side_effect=launch))
                patches.enter_context(patch.object(study.p.live, "read_events", return_value={
                    "report": {"completed": True, "summary": "simulated"}, "usage": {"input_tokens": 10, "output_tokens": 1},
                    "thread_id": "simulated", "commands": {}}))
                patches.enter_context(patch.object(study.p.live, "reconcile_worker", return_value={}))
                imported = patches.enter_context(patch.object(study.intentline_advisory, "load_export", return_value={"metadata": {"advisory": True}}))
                checked = patches.enter_context(patch.object(study.local_run, "check", return_value={"feedback": {"checks": []}, "elapsed_seconds": 0, "model_dispatches": 0}))
                patches.enter_context(patch.object(study.local_run, "inspect", side_effect=inspect))
                patches.enter_context(patch.object(study.grader, "grade", return_value={"correct": True, "available": True}))
                patches.enter_context(patch("builtins.print"))
                study.execute()
            result = json.loads((store / "results.json").read_text())
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(worker.call_count, 16)
            self.assertEqual(checked.call_count, 8)
            self.assertEqual(imported.call_count, 12)
            self.assertEqual(sum(r["status"] == "CORRECT_BUT_BLOCKED" for r in result["assignments"]), 4)
            for call in checked.call_args_list:
                product, source, checks = call.args[:3]
                task = next(task for task, request in study.corpus.REQUESTS.items() if request == source)
                self.assertEqual(checks, study.selected_checks(task))
                self.assertTrue(product.is_dir())
            self.assertTrue(all(r["usage"]["input_tokens"] == 10 for r in result["assignments"]))


if __name__ == "__main__":
    unittest.main()
