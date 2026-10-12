"""Offline transport/report fault injection; these tests cannot qualify S0."""
import copy
import json
import os
from pathlib import Path
import sys
import signal
import subprocess
import tempfile
import unittest
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checks"))
import codex_live as live
import host_probe as host
import s0_live


def report(role="prover"):
    return {"role": role, "binding": "current", "verdict": {"prover": "PROVEN", "reviewer": "PASS", "implementer": "READY"}[role],
            "summary": "Observed all required behavior", "findings": [], "criteria": [
                {"id": key, "status": "SATISFIED", "observation": "Actual CLI observations",
                 "commands": ["item_1"]} for key in ("U1", "U2", "U3", "U4")]}


class LiveTransportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def events(self):
        return [{"type": "thread.started", "thread_id": "host-issued-thread"},
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"id": "item_1", "type": "command_execution",
                    "command": "python probe.py", "exit_code": 0, "status": "completed", "aggregated_output": "ok"}},
                {"type": "item.completed", "item": {"id": "item_2", "type": "agent_message", "text": json.dumps(report())}},
                {"type": "turn.completed", "usage": {"input_tokens": 50, "output_tokens": 20}}]

    def receipt(self, events=None):
        raw = "\n".join(json.dumps(event) for event in (self.events() if events is None else events)).encode()
        path = self.work / "events.jsonl"
        path.write_bytes(raw)
        return {"exit_code": 0, "timed_out": False, "events_path": str(path),
                "events.jsonl_sha256": host.sha256(raw)}

    def test_real_native_launch_and_distinct_receipts(self):
        for i in range(2):
            directory = self.work / str(i)
            directory.mkdir()
            result = live.launch([sys.executable, "-I", "-B", "-c",
                                  "import sys; print(sys.stdin.read())"], "native input", directory, 5)
            self.assertTrue(host.succeeded(result), result)
            self.assertEqual((directory / "events.jsonl").read_text(), "native input\n")
            self.assertEqual(result["prompt_sha256"], host.sha256(b"native input"))
            if i:
                self.assertNotEqual(previous["invocation_id"], result["invocation_id"])
            previous = result

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("PROOFLINE_NATIVE_TESTS") == "1",
                         "opt-in macOS interrupted worker reconciliation")
    def test_controller_death_never_redispatches_a_running_worker(self):
        private = self.work / "private"
        private.mkdir()
        controller_code = ("import sys; from pathlib import Path; "
            f"sys.path.insert(0, {str(Path(live.__file__).parent)!r}); import codex_live; "
            f"codex_live.launch([sys.executable, '-c', 'import time; time.sleep(30)'], 'input', Path({str(private)!r}), 40)")
        controller = subprocess.Popen([sys.executable, "-I", "-B", "-c", controller_code])
        worker = None
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                path = private / "worker.json"
                if path.exists():
                    value = json.loads(path.read_text())
                    if value["state"] == "running":
                        worker = value
                        break
                time.sleep(.02)
            self.assertIsNotNone(worker)
            controller.kill()
            controller.wait(timeout=5)
            with self.assertRaisesRegex(ValueError, "still running"):
                live.reconcile_worker(private)
            os.killpg(worker["pid"], signal.SIGKILL)
            deadline = time.monotonic() + 5
            while True:
                try:
                    live.reconcile_worker(private)
                    break
                except ValueError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.02)
        finally:
            if controller.poll() is None:
                controller.kill()
            controller.wait(timeout=5)
            if worker:
                try:
                    os.killpg(worker["pid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_timeout_and_missing_executable_cannot_be_receipts(self):
        for i, argv in enumerate(([sys.executable, "-c", "import time; time.sleep(10)"], ["/missing-proofline-executable"])):
            directory = self.work / str(i)
            directory.mkdir()
            result = live.launch(argv, "test", directory, .1)
            self.assertFalse(host.succeeded(result))
            with self.assertRaises(ValueError):
                live.read_events(result)

    def test_host_ids_and_usage_come_from_events(self):
        observed = live.read_events(self.receipt())
        self.assertEqual(observed["thread_id"], "host-issued-thread")
        self.assertEqual(observed["usage"]["input_tokens"], 50)
        self.assertEqual(observed["report"], report())
        events = self.events()
        events[-1].pop("usage")
        self.assertIsNone(live.read_events(self.receipt(events))["usage"])

    def test_missing_duplicate_failed_and_unsupported_events_fail_closed(self):
        normal = self.events()
        mutations = [[], normal[1:], normal[:-1], normal + [normal[-1]],
                     [normal[0]] + normal,
                     normal[:-1] + [{"type": "turn.failed"}],
                     normal[:-1] + [{"type": "error"}] + normal[-1:]]
        for item in ("mcp_tool_call", "web_search", "unknown_remote_surface"):
            events = copy.deepcopy(normal)
            events[2]["item"]["type"] = item
            mutations.append(events)
        for key, value in (("status", "in_progress"), ("exit_code", None),
                           ("exit_code", True), ("aggregated_output", None), ("command", "")):
            events = copy.deepcopy(normal)
            events[2]["item"][key] = value
            mutations.append(events)
        for events in mutations:
            with self.subTest(events=events):
                with self.assertRaises((ValueError, KeyError)):
                    live.read_events(self.receipt(events))

    def test_tampered_or_non_json_receipts_fail_closed(self):
        receipt = self.receipt()
        Path(receipt["events_path"]).write_text("agent says thread.started and PROVEN")
        with self.assertRaises(ValueError):
            live.read_events(receipt)

    def test_exact_role_input_and_criterion_evidence_required(self):
        commands = {"item_1": {"command": "python probe.py"}}
        live.validate_report(report(), "prover", "current", commands)
        mutations = []
        for key, value in (("binding", "stale"), ("role", "reviewer"), ("verdict", "PASS"), ("summary", ""),
                           ("criteria", []), ("findings", ["material defect"])):
            changed = report()
            changed[key] = value
            mutations.append(changed)
        for key, value in (("id", "U9"), ("status", "planned"), ("status", "VIOLATED"),
                           ("commands", []), ("commands", ["invented"]), ("observation", "")):
            changed = report()
            changed["criteria"][0][key] = value
            mutations.append(changed)
        changed = report()
        changed["criteria"].append(changed["criteria"][0])
        mutations.append(changed)
        for changed in mutations:
            with self.subTest(report=changed):
                with self.assertRaises(ValueError):
                    live.validate_report(changed, "prover", "current", commands)

    def test_real_defect_and_unknown_criterion_remain_distinct(self):
        for verdict, status in (("FAIL", "VIOLATED"), ("NOT VERIFIED", "NOT VERIFIED")):
            changed = report()
            changed["verdict"] = verdict
            changed["criteria"][0]["status"] = status
            live.validate_report(changed, "prover", "current", {"item_1": {}})

    def test_command_ref_resolution_does_not_use_substrings_or_guess(self):
        changed = report()
        changed["criteria"][0]["commands"] = ["python probe.py"]
        live.resolve_command_refs(changed, {"item_1": {"command": "python probe.py"}})
        self.assertEqual(changed["criteria"][0]["commands"], ["item_1"])
        changed["criteria"][0]["commands"] = ["probe.py"]
        live.resolve_command_refs(changed, {"item_1": {"command": "python probe.py"}})
        self.assertEqual(changed["criteria"][0]["commands"], ["probe.py"])
        changed["criteria"][0]["commands"] = ["python probe.py"]
        live.resolve_command_refs(changed, {"item_1": {"command": "/bin/zsh -c 'python probe.py'"}})
        self.assertEqual(changed["criteria"][0]["commands"], ["item_1"])
        self.assertIsNone(live.shell_payload("/bin/zsh -c 'python probe.py'; echo injected"))
        changed["criteria"][0]["commands"] = ["python probe.py"]
        live.resolve_command_refs(changed, {
            "earlier": {"command": "/bin/zsh -c 'python probe.py'"},
            "latest": {"command": "/bin/zsh -c 'python probe.py'"}})
        self.assertEqual(changed["criteria"][0]["commands"], ["latest"])

    def test_fresh_command_has_narrow_policy_and_no_resume(self):
        inputs, scratch, private = (self.work / name for name in ("inputs", "scratch", "private"))
        argv = live.command("/installed/codex", inputs, scratch, private, {"model": "configured-model"})
        for option in ("--no-daemon", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--strict-config"):
            self.assertIn(option, argv)
        for forbidden in ("resume", "fork", "--sandbox", "--dangerously-bypass-approvals-and-sandbox"):
            self.assertNotIn(forbidden, argv)
        self.assertIn('approval_policy="never"', argv)
        self.assertIn('web_search="disabled"', argv)
        self.assertIn('shell_environment_policy.inherit="none"', argv)
        self.assertIn('default_permissions="proofline"', argv)
        profile = host.permission_profile(inputs, scratch, private)
        self.assertFalse(profile["network"]["enabled"])
        self.assertEqual(profile["filesystem"][str(inputs)], "read")
        self.assertEqual(profile["filesystem"][str(private)], "deny")
        self.assertEqual(profile["filesystem"][str(scratch)], "write")
        self.assertIn(str(Path(sys.executable).resolve()), profile["filesystem"])
        self.assertIn(sys.executable, profile["filesystem"])
        for feature in live.DISABLED_FEATURES:
            self.assertIn("features." + feature + "=false", argv)
        import tomllib
        setting = next(item.split('=', 1)[1] for item in argv if item.startswith('shell_environment_policy.set='))
        environment = tomllib.loads('value=' + setting)['value']
        self.assertIn(str(Path(sys.executable).resolve().parent), environment['PATH'].split(os.pathsep))

    def test_same_bytes_bind_across_different_candidate_locations(self):
        a = {"source_sha256": "source", "candidate_tree": "tree", "candidate_path": "/one"}
        b = {**a, "candidate_path": "/two"}
        self.assertEqual(live.binding_for(a), live.binding_for(b))
        self.assertNotEqual(live.binding_for(a), live.binding_for({**b, "candidate_tree": "other"}))

    def test_existing_run_is_not_overwritten(self):
        path = self.work / "report.json"
        path.write_text("preserve")
        with self.assertRaises(FileExistsError):
            s0_live.qualify(self.work, 10, 5)
        self.assertEqual(path.read_text(), "preserve")

    def test_changed_candidate_cannot_be_accepted_even_with_successful_process(self):
        inputs = self.work / "inputs"
        (inputs / "product" / ".git").mkdir(parents=True)
        for path in ("source.md", "accepted-input.md", "product/username.py", "product/.git/HEAD"):
            (inputs / path).write_text("original")
        def tamper(*args):
            self.assertIn("1.0 seconds", args[1])
            self.assertIn("final structured handoff", args[1])
            self.assertIn("reserve the final 30 seconds", args[1])
            self.assertIn("concrete unresolved risk or binding requirement", args[1])
            self.assertEqual(args[-1], 1)
            (inputs / "source.md").write_text("narrowed promise")
            return {"exit_code": 0, "timed_out": False}
        with patch.object(host, "write_diff"), patch.object(live, "launch", side_effect=tamper):
            result = s0_live.run_stage("codex", self.work, inputs, {"base_commit": "base"}, "reviewer", {}, 1)
        self.assertEqual(result["status"], "NOT VERIFIED")
        self.assertFalse(result["inputs_unchanged"])
        self.assertIn("changed", result["error"])

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("PROOFLINE_NATIVE_TESTS") == "1",
                         "opt-in macOS native sandbox test")
    def test_oracle_executes_generated_product_inside_read_only_native_boundary(self):
        inputs, private, scratch = (self.work / name for name in ("inputs", "private", "scratch"))
        for path in (inputs, private, scratch):
            path.mkdir()
        protected = private / "receipt"
        protected.write_text("original")
        script = inputs / "probe.py"
        alias = inputs / "alias.py"
        alias.symlink_to("probe.py")
        script.write_text("from pathlib import Path\nimport sys,subprocess\n"
                          "subprocess.run([sys.executable, '-I', '-B', '-c', 'print(123)'], check=True)\n"
                          f"assert Path({str(alias)!r}).read_bytes() == Path(__file__).read_bytes()\n"
                          f"for path in ({str(protected)!r}, __file__, {str(alias)!r}):\n"
                          " try: Path(path).write_text('tampered')\n"
                          " except PermissionError: pass\n"
                          " else: raise AssertionError('write permitted')\n")
        before = host.snapshot(inputs)
        receipts = []
        run = s0_live.oracle_runner(host.find_codex(None), inputs.resolve(), private.resolve(), receipts)
        result = run([str(Path(sys.executable).resolve()), "-I", "-B", str(script)], cwd=scratch, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "123\n")
        self.assertEqual(host.snapshot(inputs), before)
        self.assertEqual(protected.read_text(), "original")
        self.assertEqual(len(receipts), 1)
        script.write_text("import json,sys; print(json.dumps(sys.argv[1]))\n")
        result = run([str(Path(sys.executable).resolve()), "-I", "-B", str(script), "name-\udcff"],
                     cwd=scratch, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), "name-\udcff")

    @unittest.skipUnless(sys.platform == "darwin" and os.environ.get("PROOFLINE_NATIVE_TESTS") == "1",
                         "opt-in macOS native Git helper test")
    def test_local_git_fetch_works_with_the_actual_worker_tool_environment(self):
        import tomllib
        inputs, private, scratch = (self.work / name for name in ("inputs", "private", "scratch"))
        for path in (inputs, private, scratch):
            path.mkdir()
        argv = live.command(host.find_codex(None), inputs.resolve(), scratch.resolve(), private.resolve(), {})
        setting = next(item.split("=", 1)[1] for item in argv if item.startswith("shell_environment_policy.set="))
        environment = tomllib.loads("value=" + setting)["value"]
        script = inputs / "git-probe.py"
        script.write_text("import os,subprocess\nfrom pathlib import Path\n" +
            "env = os.environ | " + repr(environment) + "\n" +
            "def run(*args): subprocess.run(args, env=env, check=True, capture_output=True)\n" +
            "run('git','init','--quiet','source')\nPath('source/file').write_text('exact bytes')\n" +
            "run('git','-C','source','add','--all')\n" +
            "run('git','-C','source','-c','user.name=Probe','-c','user.email=probe@localhost','commit','--quiet','-m','Probe')\n" +
            "run('git','init','--bare','--quiet','destination.git')\n" +
            "run('git','-C','destination.git','fetch','--quiet','--depth=1',str(Path('source').resolve()),'HEAD')\n" +
            "data=subprocess.check_output(['git','--git-dir=destination.git','show','FETCH_HEAD:file'],env=env)\n" +
            "assert data == b'exact bytes'\nprint('local fetch preserved exact bytes')\n")
        before = host.snapshot(inputs)
        receipts = []
        run = s0_live.oracle_runner(host.find_codex(None), inputs.resolve(), private.resolve(), receipts)
        result = run([str(Path(sys.executable).resolve()), "-I", "-B", str(script)], cwd=scratch, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "local fetch preserved exact bytes\n")
        self.assertEqual(host.snapshot(inputs), before)

    def test_unavailable_host_never_dispatches(self):
        with patch.object(s0_live.platform, "system", return_value="Unsupported"), patch.object(live, "launch") as launch:
            result = s0_live.qualify(self.work / "new", 10, 5)
        launch.assert_not_called()
        self.assertEqual(result["model_dispatches"], 0)
        self.assertEqual(result["s0"]["decision"], "NO-GO")

    def test_budget_input_rejects_nonfinite_and_nonpositive(self):
        import argparse
        for value in ("0", "-1", "nan", "inf", "3601"):
            with self.assertRaises(argparse.ArgumentTypeError):
                s0_live.positive_seconds(value)
