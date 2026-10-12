"""S4 deterministic fault injection; model judgment is qualified separately."""
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as p


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name).resolve()
        self.repo = self.work / "source"
        self.repo.mkdir()
        (self.repo / "value.py").write_text("value = 0\n")
        p.host.git(self.repo, "init", "--quiet", "--template=")
        p.host.git(self.repo, "add", "--all")
        p.host.git(self.repo, "commit", "--quiet", "-m", "Initial")
        self.calls = []
        self.prompts = []
        self.thread = str(uuid.uuid4())
        self.reviews = 0
        self.proofs = 0
        self.output = self.work / "run"
        self.brief = "\n".join(f"| D{i} | Required behavior {i} |" for i in range(1, 5))

    def boundary(self, codex, directory, inputs, *args):
        for name in ("canary.py", "canary.json"):
            (inputs / name).write_text("offline canary")
        return {"assessment": {"status": "OBSERVED"}}

    def patches(self, worker):
        stack = ExitStack()
        original = p.host.run_command
        def run_command(argv, *args, **kwargs):
            if argv == [sys.executable, "--version"]:
                return {"exit_code": 0, "timed_out": False, "stdout": "codex-cli 0.162.1"}
            return original(argv, *args, **kwargs)
        for target, name, value in ((p.platform, "system", lambda: "Darwin"),
                (p.host, "find_codex", lambda _: sys.executable),
                (p.live, "preferences", lambda: {}),
                (p.host, "run_command", run_command),
                (p.host, "probe_boundary", self.boundary), (p.live, "run_stage", worker)):
            stack.enter_context(patch.object(target, name, side_effect=value))
        return stack

    def stage(self, codex, directory, inputs, identity, role, preferences, allowance, **kwargs):
        self.calls.append((role, kwargs.get("session_id"), identity["candidate_tree"], allowance))
        self.prompts.append(kwargs["make_prompt"](role, inputs, identity))
        thread = self.thread if role == "implementer" else str(uuid.uuid4())
        verdict = {"implementer": "READY", "reviewer": "PASS", "prover": "PROVEN"}[role]
        if role == "implementer":
            value = sum(call[0] == "implementer" for call in self.calls)
            (inputs / "product" / "value.py").write_text(f"value = {value}\n")
        if role == "reviewer":
            self.reviews += 1
        if role == "prover":
            self.proofs += 1
        findings, satisfied = [], 4
        verdict, satisfied, findings = self.outcome(role, verdict, satisfied, findings)
        report = {"role": role, "binding": p.live.binding_for(identity), "verdict": verdict,
                  "summary": "Offline controlled observation", "findings": findings,
                  "criteria": [{"id": f"D{i}", "status": "SATISFIED" if i <= satisfied else
                      ("VIOLATED" if verdict == "FAIL" else "NOT VERIFIED"),
                      "observation": f"Controlled obligation {i}", "commands": ["probe"] if role == "prover" or i > satisfied else []}
                      for i in range(1, 5)]}
        private = directory / "private"
        private.mkdir()
        events = [{"type": "thread.started", "thread_id": thread}, {"type": "turn.started"},
                  {"type": "item.completed", "item": {"id": "probe", "type": "command_execution",
                    "command": "offline probe", "exit_code": 0, "status": "completed", "aggregated_output": "controlled"}},
                  {"type": "item.completed", "item": {"id": "handoff", "type": "agent_message", "text": json.dumps(report)}},
                  {"type": "turn.completed"}]
        raw = "\n".join(json.dumps(e) for e in events).encode()
        event_path = private / "events.jsonl"
        event_path.write_bytes(raw)
        receipt = {"kind": "codex_exec", "exit_code": 0, "timed_out": False,
                   "events_path": str(event_path), "events.jsonl_sha256": p.host.sha256(raw)}
        p.live.save_worker(private, {"state": "finished", "receipt": receipt})
        result = {"role": role, "identities": identity, "binding": report["binding"],
                  "status": "OBSERVED", "report": report, "receipt": receipt, "thread_id": thread,
                  "inputs_unchanged": True, "snapshot": p.host.snapshot(inputs)["sha256"],
                  "boundary": {"status": "OBSERVED"}, "usage": None,
                  "commands": {"probe": {"command": "offline probe"}}}
        (directory / "stage.json").write_text(json.dumps(result))
        return result

    def outcome(self, role, verdict, satisfied, findings):
        return verdict, satisfied, findings

    def deliver(self, **kwargs):
        return p.deliver(self.repo, "Complete source", self.brief, self.output, **kwargs)

    def test_product_repair_resumes_same_implementer_and_rechecks_changed_candidate(self):
        self.outcome = lambda role, v, s, f: ("FAIL", 2, ["D3/D4: exact failing reproduction"]) if role == "reviewer" and self.reviews == 1 else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
            confirmed = p.inspect_record(self.output / "report.json")
        self.assertEqual(confirmed["status"], "LOCAL ACCEPTED")
        self.assertEqual([c[0] for c in self.calls], ["implementer", "reviewer", "implementer", "reviewer", "prover"])
        self.assertEqual(self.calls[2][1], self.thread)
        self.assertNotEqual(self.calls[1][2], self.calls[3][2])
        self.assertEqual(result["correction_rounds"], 1)
        self.assertIn("offline probe", self.prompts[2])
        self.assertIsNone(result["stages"][0]["usage"])

    def test_evidence_only_recovery_keeps_candidate_and_review(self):
        self.outcome = lambda role, v, s, f: ("NOT VERIFIED", 3, []) if role == "prover" and self.proofs == 1 else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
            self.assertEqual(p.inspect_record(self.output / "report.json")["status"], "LOCAL ACCEPTED")
        self.assertEqual([c[0] for c in self.calls], ["implementer", "reviewer", "prover", "prover"])
        self.assertEqual(self.calls[2][2], self.calls[3][2])
        self.assertEqual(result["current_checks"]["reviewer"], 1)
        self.assertEqual(result["correction_rounds"], 0)
        self.assertEqual(result["failure_class"], "insufficient evidence")

    def test_environment_failure_never_repairs_product(self):
        self.outcome = lambda role, v, s, f: ("NOT VERIFIED", 0, ["ENVIRONMENT FAILURE: unavailable interpreter"]) if role == "prover" else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
        self.assertEqual(result["status"], "ENVIRONMENT FAILURE")
        self.assertEqual(result["correction_rounds"], 0)
        self.assertEqual(sum(c[0] == "implementer" for c in self.calls), 1)
        self.assertEqual(result["evidence_rechecks"], 2)
        self.outcome = lambda role, v, s, f: (v, s, f)
        with self.patches(self.stage):
            resumed = p.resume(self.output / "report.json")
        self.assertEqual(resumed["status"], "LOCAL ACCEPTED")
        self.assertEqual(resumed["model_dispatches"], 6)
        self.assertEqual(resumed["correction_rounds"], 0)

    def test_native_environment_must_recover_before_resume_dispatches(self):
        def unavailable(*args):
            self.boundary(*args)
            return {"assessment": {"status": "NOT VERIFIED"}}
        with self.patches(self.stage), patch.object(p.host, "probe_boundary", side_effect=unavailable):
            result = self.deliver()
            again = p.resume(self.output / "report.json")
        self.assertEqual(result["status"], "ENVIRONMENT FAILURE")
        self.assertEqual(again["status"], "ENVIRONMENT FAILURE")
        self.assertEqual(len(self.calls), 0)
        with self.patches(self.stage):
            result = p.resume(self.output / "report.json")
        self.assertEqual(result["status"], "LOCAL ACCEPTED")
        self.assertEqual(result["model_dispatches"], 3)

    def test_transport_failure_is_environment_and_bad_report_is_evidence(self):
        self.assertEqual(p.classify_failure({"status": "NOT VERIFIED", "receipt": {
            "exit_code": None, "timed_out": True}}), "environment failure")
        self.assertEqual(p.classify_failure({"status": "NOT VERIFIED", "receipt": {
            "exit_code": 0, "timed_out": False}, "error": "Proof lacks executable observation references"}), "insufficient evidence")

    def test_source_gap_stops_without_product_edits(self):
        self.outcome = lambda role, v, s, f: ("NOT VERIFIED", 0, ["INPUT NOT READY: omitted original promise"]) if role == "reviewer" else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
        self.assertEqual(result["status"], "INPUT NOT READY")
        self.assertEqual(len(self.calls), 2)

    def test_two_nonprogress_rounds_stop_early(self):
        self.outcome = lambda role, v, s, f: ("FAIL", 1, ["Same reproduced defect"]) if role == "reviewer" else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
        self.assertEqual(result["correction_rounds"], 2)
        self.assertEqual(result["model_dispatches"], 6)
        self.assertIsNone(result["next_role"])
        self.assertIn("non-progress", result["next_action"])

    def test_productive_third_round_is_allowed_within_same_budget(self):
        self.outcome = lambda role, v, s, f: ("FAIL", self.reviews - 1, ["Remaining reproduced obligations"]) if role == "reviewer" and self.reviews <= 3 else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver()
            self.assertEqual(p.inspect_record(self.output / "report.json")["status"], "LOCAL ACCEPTED")
        self.assertEqual(result["correction_rounds"], 3)
        self.assertEqual(result["model_dispatches"], 9)
        self.assertTrue(all(item["improved"] for item in result["progress"]))

    def test_dispatch_reserve_and_restart_never_reset_consumption(self):
        self.outcome = lambda role, v, s, f: ("FAIL", 1, ["Reproduced defect"]) if role == "reviewer" else (v, s, f)
        with self.patches(self.stage):
            result = self.deliver(dispatches=3)
            resumed = p.resume(self.output / "report.json")
        self.assertEqual(result["status"], "BUDGET EXHAUSTED")
        self.assertEqual(resumed["status"], "BUDGET EXHAUSTED")
        self.assertEqual(resumed["model_dispatches"], 2)
        self.assertGreaterEqual(resumed["elapsed_seconds"], result["elapsed_seconds"])
        self.assertEqual(len(self.calls), 2)

    def test_interrupted_implementation_at_episode_deadline_is_exhaustion(self):
        expired = False
        def worker(*args, **kwargs):
            nonlocal expired
            result = self.stage(*args, **kwargs)
            expired = True
            result["status"] = "NOT VERIFIED"
            result["error"] = "Invocation timed out"
            return result
        with self.patches(worker), patch.object(p, "elapsed", side_effect=lambda record: 1000 if expired else 0):
            result = self.deliver()
        self.assertEqual(result["status"], "BUDGET EXHAUSTED")
        self.assertEqual(result["model_dispatches"], 1)
        self.assertIn("active_stage", result)
        self.assertTrue(Path(result["candidate_path"]).exists())

    def interrupted(self):
        def worker(*args, **kwargs):
            result = self.stage(*args, **kwargs)
            if result["role"] == "reviewer":
                raise KeyboardInterrupt
            return result
        with self.patches(worker):
            self.deliver()
        self.assertEqual(len(self.calls), 2)

    def test_restart_reconciles_completed_worker_without_duplicate_dispatch(self):
        self.interrupted()
        with self.patches(self.stage):
            result = p.resume(self.output / "report.json")
            self.assertEqual(p.inspect_record(self.output / "report.json")["status"], "LOCAL ACCEPTED")
        self.assertEqual([c[0] for c in self.calls], ["implementer", "reviewer", "prover"])
        self.assertEqual(result["model_dispatches"], 3)

    def test_interrupted_partial_implementation_resumes_original_context(self):
        def interrupted(*args, **kwargs):
            result = self.stage(*args, **kwargs)
            directory = args[1]
            (directory / "stage.json").unlink()
            raw = (json.dumps({"type": "thread.started", "thread_id": self.thread}) + '\n{"type": ').encode()
            (directory / "private" / "events.jsonl").write_bytes(raw)
            p.live.save_worker(directory / "private", {"state": "finished", "receipt": {
                "events.jsonl_sha256": p.host.sha256(raw)}})
            raise KeyboardInterrupt
        with self.patches(interrupted):
            result = self.deliver()
        self.assertEqual(result["model_dispatches"], 1)
        with self.patches(self.stage):
            result = p.resume(self.output / "report.json")
            self.assertEqual(p.inspect_record(self.output / "report.json")["status"], "LOCAL ACCEPTED")
        self.assertEqual(self.calls[1][1], self.thread)
        self.assertEqual(result["model_dispatches"], 4)
        self.assertEqual(result["correction_rounds"], 0)
        self.assertEqual(len(result["reconciled_workers"]), 1)

    def test_dead_verifier_is_replaced_without_reusing_partial_verdict(self):
        self.interrupted()
        path = self.output / "report.json"
        record = json.loads(path.read_text())
        (Path(record["active_stage"]["directory"]) / "stage.json").unlink()
        with self.patches(self.stage):
            result = p.resume(path)
            self.assertEqual(p.inspect_record(path)["status"], "LOCAL ACCEPTED")
        self.assertEqual([c[0] for c in self.calls], ["implementer", "reviewer", "reviewer", "prover"])
        self.assertEqual(result["model_dispatches"], 4)

    def test_missing_receipt_tampered_candidate_and_changed_map_reject_acceptance(self):
        with self.patches(self.stage):
            self.deliver()
        path = self.output / "report.json"
        original = path.read_text()
        record = json.loads(original)
        record["current_checks"].pop("prover")
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "Missing independent"):
            p.inspect_record(path)
        path.write_text(original)
        record = json.loads(original)
        record["execution_map"] = "changed assumptions"
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "Execution guidance changed"):
            p.inspect_record(path)
        path.write_text(original)
        inputs = Path(record["candidate_path"]).parent
        (inputs / "product" / "value.py").write_text("value = 'changed after acceptance'\n")
        self.assertEqual(p.inspect_record(path)["status"], "NOT VERIFIED")

    def test_invalid_saved_budget_never_redispatches(self):
        self.interrupted()
        path = self.output / "report.json"
        record = json.loads(path.read_text())
        record["elapsed_seconds"] = float("nan")
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "Invalid cumulative budget"):
            p.resume(path)
        self.assertEqual(len(self.calls), 2)

    def test_backwards_clock_cannot_create_more_capacity(self):
        self.interrupted()
        path = self.output / "report.json"
        record = json.loads(path.read_text())
        record["last_clock_epoch"] += 100
        path.write_text(json.dumps(record))
        with self.patches(self.stage), self.assertRaisesRegex(ValueError, "clock moved backwards"):
            p.resume(path)
        self.assertEqual(len(self.calls), 2)

    def test_restart_counts_downtime_and_refuses_stale_inputs_and_candidate(self):
        for change in ("elapsed", "product", "source"):
            with self.subTest(change=change):
                self.output = self.work / ("case-" + change)
                self.calls.clear()
                self.interrupted()
                path = self.output / "report.json"
                record = json.loads(path.read_text())
                if change == "elapsed":
                    record["started_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1000)).isoformat()
                    path.write_text(json.dumps(record))
                else:
                    target = Path(record["candidate_path"]) / "value.py" if change == "product" else Path(record["candidate_path"]).parent / "source.md"
                    target.write_text("changed")
                with self.patches(self.stage):
                    resumed = p.resume(path)
                self.assertNotEqual(resumed["status"], "LOCAL ACCEPTED")
                self.assertEqual(resumed["model_dispatches"], 2)
                if change == "elapsed":
                    self.assertEqual(resumed["status"], "BUDGET EXHAUSTED")
                    self.assertGreater(resumed["elapsed_seconds"], 999)

    def test_unknown_or_running_worker_cannot_be_redispatched(self):
        self.interrupted()
        path = self.output / "report.json"
        record = json.loads(path.read_text())
        private = Path(record["active_stage"]["directory"]) / "private"
        for worker in ({"state": "launching"}, {"state": "running", "pid": 123, "process_start": "same"}):
            p.live.save_worker(private, worker)
            with self.patches(self.stage), patch.object(p.live, "process_start", return_value="same"):
                resumed = p.resume(path)
            self.assertEqual(resumed["status"], "NOT VERIFIED")
            self.assertEqual(resumed["model_dispatches"], 2)
        self.assertEqual(len(self.calls), 2)

    def test_concurrent_resume_has_no_dispatch(self):
        self.interrupted()
        with p.episode_lock(self.output), self.patches(self.stage):
            with self.assertRaisesRegex(ValueError, "already running"):
                p.resume(self.output / "report.json")
        self.assertEqual(len(self.calls), 2)

    def test_transport_resume_is_scoped_to_exact_implementer(self):
        args = p.live.command("/codex", self.work / "inputs", self.work / "scratch", self.work / "private", {}, True, self.thread)
        self.assertIn("resume", args)
        self.assertIn(self.thread, args)
        self.assertNotIn("--ephemeral", args)
        with self.assertRaises(ValueError):
            p.live.command("/codex", self.work / "inputs", self.work / "scratch", self.work / "private", {}, False, self.thread)
