#!/usr/bin/env python3
"""Offline regression checks for the S0 diagnostic, never host qualification.

Git, Python commands, snapshots, process cleanup, and loopback failures run for
real in disposable directories. The explicitly named offline Codex executable
is a transport test double: its invented denial messages are deliberately not
evidence that a real sandbox or a live model was qualified.
"""

from __future__ import annotations

import copy
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "proofline_host_probe", ROOT / "checks" / "host_probe.py"
)
probe = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(probe)


class DisposableCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix="proofline-host-test-"
        )
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)

    def python(self, code, *arguments, timeout=5):
        return probe.run_command(
            [sys.executable, "-I", "-B", "-c", code, *arguments],
            self.work, timeout=timeout,
        )

    def make_inputs(self, name="inputs"):
        inputs = self.work / name
        (inputs / "product" / ".git").mkdir(parents=True)
        for relative, data in (
            ("source.md", "Original source promise.\n"),
            ("accepted-input.md", "Accepted obligations.\n"),
            ("product/username.py", "print('candidate')\n"),
            ("product/.git/HEAD", "ref: refs/heads/main\n"),
        ):
            (inputs / relative).write_text(data)
        return inputs

    def offline_codex(self, fault=None):
        """A real executable with fabricated host messages, only for tests."""
        executable = self.work / "codex-offline-transport-double"
        program = textwrap.dedent("""\
            import json
            from pathlib import Path
            import stat
            import sys

            if sys.argv[1:] == ["--version"]:
                print("offline Codex transport double; no host qualification")
            elif sys.argv[1:] == ["login", "status"]:
                print("Logged in (invented offline test status)")
            elif "sandbox" in sys.argv:
                spec = json.loads(Path(sys.argv[-1]).read_text())
                result = {
                    "nonce": spec["nonce"],
                    "writes": dict.fromkeys(spec["writes"], "denied"),
                    "reads": dict.fromkeys(spec["reads"], "denied"),
                    "mode_change": "denied", "scratch": True,
                    "network": "denied",
                }
                Path(spec["scratch_file"]).write_text(spec["nonce"])
                if FAULT and FAULT.startswith("write:"):
                    Path(spec["writes"][FAULT.split(":", 1)[1]]).write_text("tampered")
                elif FAULT == "private-oracle":
                    Path(spec["reads"]["oracle-canary"]).write_text("tampered")
                elif FAULT == "mode":
                    target = Path(spec["mode_target"])
                    target.chmod(stat.S_IMODE(target.stat().st_mode) ^ stat.S_IXUSR)
                elif FAULT == "symlink":
                    target = Path(spec["writes"]["source"])
                    target.unlink()
                    target.symlink_to(spec["writes"]["input"])
                elif FAULT == "missing-write":
                    result["writes"].pop("source")
                elif FAULT == "allowed-read":
                    result["reads"]["receipt-canary"] = "allowed"
                print(json.dumps(result))
            else:
                sys.exit(64)
        """)
        executable.write_text(
            "#!" + sys.executable + " -B\nFAULT = " + repr(fault) + "\n" + program
        )
        executable.chmod(0o700)
        return str(executable)


class SnapshotTests(DisposableCase):
    def test_content_mode_and_path_changes_have_distinct_identities(self):
        root = self.work / "tree"
        root.mkdir()
        file = root / "promise.txt"
        file.write_bytes(b"first promise\n")
        file.chmod(0o644)
        original = probe.snapshot(root)
        self.assertEqual(probe.snapshot(root), original)

        file.write_bytes(b"other promise\n")
        self.assertNotEqual(probe.snapshot(root)["sha256"], original["sha256"])
        file.write_bytes(b"first promise\n")
        self.assertEqual(probe.snapshot(root), original)

        file.chmod(0o744)
        self.assertNotEqual(probe.snapshot(root)["sha256"], original["sha256"])
        file.chmod(0o644)
        file.rename(root / "renamed-promise.txt")
        self.assertNotEqual(probe.snapshot(root)["sha256"], original["sha256"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_link_targets_are_recorded_without_reading_external_contents(self):
        root = self.work / "tree"
        root.mkdir()
        external = self.work / "outside"
        external.mkdir()
        private = external / "private.txt"
        private.write_text("first private contents")
        link = root / "outside-link"
        link.symlink_to(external, target_is_directory=True)
        original = probe.snapshot(root)
        self.assertEqual(len(original["entries"]), 1)
        self.assertEqual(original["entries"][0]["kind"], "symlink")
        self.assertEqual(original["entries"][0]["target"], str(external))

        private.write_text("different private contents")
        self.assertEqual(probe.snapshot(root), original)
        link.unlink()
        link.symlink_to(private)
        self.assertNotEqual(probe.snapshot(root)["sha256"], original["sha256"])


class FrozenFixtureTests(DisposableCase):
    def test_source_hashes_and_both_git_revisions_are_reconstructible(self):
        destination = self.work / "frozen"
        identities = probe.freeze_fixture(destination, "correct")
        product = destination / "product"
        self.assertEqual(identities["candidate_path"], str(product))
        for name, key in (("source.md", "source_sha256"),
                          ("accepted-input.md", "input_sha256")):
            original = (probe.FIXTURES / name).read_bytes()
            self.assertEqual((destination / name).read_bytes(), original)
            self.assertEqual(identities[key], hashlib.sha256(original).hexdigest())

        # Reconstruct using Git's public interface, independently of freeze_fixture.
        def git_bytes(*arguments):
            completed = subprocess.run(
                ["git", *arguments], cwd=product, capture_output=True,
                check=True, timeout=10,
            )
            return completed.stdout

        base = identities["base_commit"]
        candidate = identities["candidate_commit"]
        self.assertNotEqual(base, candidate)
        self.assertEqual(git_bytes("rev-parse", candidate + "^").decode().strip(), base)
        self.assertEqual(git_bytes("rev-parse", candidate + "^{tree}").decode().strip(),
                         identities["candidate_tree"])
        for commit, fixture in ((base, "baseline"), (candidate, "correct")):
            expected = probe.FIXTURES / "workers" / fixture
            for path in expected.iterdir():
                if path.is_file():
                    self.assertEqual(git_bytes("show", commit + ":" + path.name),
                                     path.read_bytes())
        self.assertEqual(git_bytes("status", "--porcelain"), b"")
        self.assertFalse((destination / "oracle.py").exists())
        self.assertFalse((destination / "workers").exists())


class ProcessReceiptTests(DisposableCase):
    def test_native_status_output_and_distinct_invocation_ids_are_recorded(self):
        first = self.python(
            "import sys; print('native output'); print('native error', file=sys.stderr); "
            "sys.exit(7)"
        )
        second = self.python("print('success')")
        self.assertEqual(first["kind"], "process_probe")
        self.assertEqual(first["exit_code"], 7)
        self.assertFalse(first["timed_out"])
        self.assertEqual(first["stdout"], "native output\n")
        self.assertEqual(first["stderr"], "native error\n")
        self.assertFalse(probe.succeeded(first))
        self.assertTrue(probe.succeeded(second))
        self.assertNotEqual(first["invocation_id"], second["invocation_id"])
        self.assertEqual(first["cwd"], str(self.work))
        self.assertGreaterEqual(first["elapsed_seconds"], 0)

    def test_logs_are_bounded_and_credential_previews_are_redacted(self):
        receipt = self.python(
            "import sys; print('sk-secret_preview bearer private-value user@example.com'); "
            "sys.stderr.write('x' * int(sys.argv[1]))",
            str(probe.MAX_LOG_BYTES + 100),
        )
        self.assertTrue(probe.succeeded(receipt))
        self.assertTrue(receipt["stderr_truncated"])
        self.assertEqual(len(receipt["stderr"]), probe.MAX_LOG_BYTES)
        for secret in ("secret_preview", "private-value", "user@example.com"):
            self.assertNotIn(secret, receipt["stdout"])

    def test_missing_executable_is_unknown_authentication(self):
        missing = str(self.work / "unavailable-codex")
        self.assertIsNone(probe.find_codex(missing))
        receipt = probe.run_command([missing, "login", "status"], self.work)
        self.assertIsNone(receipt["exit_code"])
        self.assertIn("FileNotFoundError", receipt["error"])
        self.assertFalse(probe.succeeded(receipt))
        self.assertEqual(probe.auth_status(receipt), "unknown")

    def test_auth_initialization_failure_is_not_a_login_judgment(self):
        receipt = self.python(
            "import sys; print('cannot open /proc/self/exe during initialization', "
            "file=sys.stderr); sys.exit(1)"
        )
        self.assertEqual(probe.auth_status(receipt), "unknown")

    def test_successful_process_cannot_turn_a_negative_login_message_positive(self):
        receipt = self.python("print('Not logged in')")
        self.assertNotEqual(probe.auth_status(receipt), "authenticated")

    def test_timeout_is_captured_with_partial_output(self):
        receipt = self.python(
            "import time; print('started', flush=True); time.sleep(60)", timeout=0.2
        )
        self.assertTrue(receipt["timed_out"])
        self.assertFalse(probe.succeeded(receipt))
        self.assertEqual(receipt["stdout"], "started\n")
        self.assertLess(receipt["elapsed_seconds"], 5)

    @unittest.skipUnless(
        sys.platform.startswith("linux") and os.access("/proc/self/stat", os.R_OK),
        "readable Linux /proc process state is unavailable",
    )
    def test_descendants_do_not_keep_running_after_exit_or_timeout(self):
        # A killed orphan can briefly remain as a zombie until the host reaps it;
        # it must not remain executable or keep the command capture open.
        for parent_sleep in (0, 60):
            with self.subTest(parent_sleep=parent_sleep):
                receipt = self.python(
                    "import subprocess, sys, time; "
                    "child = subprocess.Popen([sys.executable, '-I', '-B', '-c', "
                    "'import time; time.sleep(60)']); "
                    "print(child.pid, flush=True); time.sleep(float(sys.argv[1]))",
                    str(parent_sleep), timeout=0.3,
                )
                self.assertEqual(receipt["timed_out"], bool(parent_sleep))
                pid = int(receipt["stdout"].strip())
                state_path = Path(f"/proc/{pid}/stat")

                def still_running():
                    try:
                        # comm can contain spaces or parentheses; state follows
                        # the final closing parenthesis, rather than token #3.
                        state = state_path.read_text().rsplit(")", 1)[1].split()[0]
                    except FileNotFoundError:
                        return False
                    return state not in {"Z", "X"}

                deadline = time.monotonic() + 2
                while still_running() and time.monotonic() < deadline:
                    time.sleep(0.01)
                running = still_running()
                if running:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                self.assertFalse(running, "probe descendant survived process-group cleanup")


class CanaryAssessmentTests(DisposableCase):
    def setUp(self):
        super().setUp()
        self.spec = {
            "nonce": "fresh-test-nonce",
            "writes": dict.fromkeys(("source", "input", "candidate", "git_head", "receipt"),
                                    "unused-path"),
            "reads": dict.fromkeys(("receipt-canary", "oracle-canary", "other-role-canary"),
                                   "unused-path"),
            "mode_target": "unused-path",
            "scratch_file": str(self.work / "scratch-output"),
            "port": 12345,
        }
        self.observations = {
            "nonce": self.spec["nonce"],
            "writes": dict.fromkeys(self.spec["writes"], "denied"),
            "reads": dict.fromkeys(self.spec["reads"], "denied"),
            "mode_change": "denied", "scratch": True, "network": "denied",
        }

    def receipt(self, observations=None, *, output=None, scratch_nonce=None):
        # These stdout messages are intentionally invented for parser tests.
        # The real diagnostic must never promote them to S0 qualification.
        payload = (json.dumps(self.observations if observations is None else observations)
                   if output is None else output)
        return self.python(
            "from pathlib import Path; import sys; "
            "Path(sys.argv[1]).write_text(sys.argv[2]); print(sys.argv[3])",
            self.spec["scratch_file"],
            self.spec["nonce"] if scratch_nonce is None else scratch_nonce, payload,
        )

    def test_complete_offline_canary_is_only_a_narrow_process_observation(self):
        assessment = probe.assess_canary(self.receipt(), self.spec, unchanged=True)
        self.assertEqual(assessment["status"], "OBSERVED")
        self.assertIn("no model", assessment["scope"])

    def test_native_exit_zero_needs_matching_canary_data(self):
        for output in ("", "everything passed", "{}", "[]", "null",
                       json.dumps({**self.observations, "nonce": "stale-nonce"})):
            with self.subTest(output=output):
                receipt = self.receipt(output=output)
                self.assertTrue(probe.succeeded(receipt))
                self.assertEqual(probe.assess_canary(receipt, self.spec, True)["status"],
                                 "NOT VERIFIED")

    def test_every_missing_or_allowed_boundary_prevents_observed_status(self):
        mutations = []
        for field in ("writes", "reads"):
            for name in self.observations[field]:
                for change in ("missing", "allowed"):
                    result = copy.deepcopy(self.observations)
                    if change == "missing":
                        result[field].pop(name)
                    else:
                        result[field][name] = "allowed"
                    mutations.append((f"{field}/{name}/{change}", result))
        for field in ("mode_change", "scratch", "network"):
            result = copy.deepcopy(self.observations)
            result.pop(field)
            mutations.append((f"missing/{field}", result))
        for field, value in (("mode_change", "allowed"), ("scratch", False),
                             ("network", "allowed"), ("network", "unknown"),
                             ("network", "not_observed"), ("network", "connection_refused"),
                             ("network", "timeout")):
            result = copy.deepcopy(self.observations)
            result[field] = value
            mutations.append((f"{field}/{value}", result))
        for name, observations in mutations:
            with self.subTest(boundary=name):
                self.assertEqual(
                    probe.assess_canary(self.receipt(observations), self.spec, True)["status"],
                    "NOT VERIFIED",
                )

    def test_scratch_must_contain_the_current_nonce(self):
        receipt = self.receipt(scratch_nonce="previous-invocation")
        self.assertEqual(probe.assess_canary(receipt, self.spec, True)["status"],
                         "NOT VERIFIED")
        Path(self.spec["scratch_file"]).unlink()
        self.assertEqual(probe.assess_canary(receipt, self.spec, True)["status"],
                         "NOT VERIFIED")

    def test_missing_network_control_cannot_be_observed(self):
        receipt = self.receipt()
        for port_present in (True, False):
            with self.subTest(port_present=port_present):
                spec = copy.deepcopy(self.spec)
                if port_present:
                    spec["port"] = None
                else:
                    spec.pop("port")
                self.assertEqual(probe.assess_canary(receipt, spec, True)["status"],
                                 "NOT VERIFIED")

    def test_truncated_output_and_changed_inputs_cannot_be_observed(self):
        receipt = self.receipt()
        self.assertEqual(probe.assess_canary(receipt, self.spec, False)["status"],
                         "NOT VERIFIED")
        truncated = self.receipt(output=json.dumps(self.observations)
                                 + " " * probe.MAX_LOG_BYTES)
        self.assertTrue(truncated["stdout_truncated"])
        self.assertEqual(probe.assess_canary(truncated, self.spec, True)["status"],
                         "NOT VERIFIED")


class BoundaryTamperingTests(DisposableCase):
    def test_actual_protected_file_mutations_override_fabricated_denial_messages(self):
        for fault in ("write:source", "write:input", "write:candidate", "write:git_head",
                      "write:receipt", "private-oracle", "mode", "symlink"):
            with self.subTest(fault=fault):
                output = self.work / fault.replace(":", "-")
                output.mkdir()
                inputs = self.make_inputs(output.name + "-inputs")
                result = probe.probe_boundary(self.offline_codex(fault), output, inputs, 5)
                self.assertTrue(probe.succeeded(result["receipt"]), result)
                self.assertEqual(result["assessment"]["status"], "NOT VERIFIED")
                self.assertFalse(result["assessment"]["inputs_unchanged"])

    def test_incomplete_or_allowed_observations_fail_even_without_file_changes(self):
        for fault in ("missing-write", "allowed-read"):
            with self.subTest(fault=fault):
                output = self.work / fault
                output.mkdir()
                inputs = self.make_inputs(fault + "-inputs")
                result = probe.probe_boundary(self.offline_codex(fault), output, inputs, 5)
                self.assertTrue(probe.succeeded(result["receipt"]), result)
                self.assertTrue(result["assessment"]["inputs_unchanged"])
                self.assertEqual(result["assessment"]["status"], "NOT VERIFIED")


class NativeNetworkFailureTests(DisposableCase):
    def bound_loopback_socket(self, *, listen=False):
        connection = socket.socket()
        self.addCleanup(connection.close)
        try:
            connection.bind(("127.0.0.1", 0))
            if listen:
                connection.listen(0)
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EACCES):
                self.skipTest("host does not permit the independent loopback control")
            raise
        return connection

    def run_canary(self, port):
        scratch = self.work / "canary-scratch"
        scratch.mkdir()
        target = self.work / "disposable-target"
        target.write_text("disposable contents")
        spec = {
            "nonce": "network-failure-test",
            "writes": {"disposable": str(target)},
            "reads": {"disposable": str(target)},
            "mode_target": str(target),
            "scratch_file": str(scratch / "output"), "port": port,
        }
        script = self.work / "canary.py"
        script.write_text(probe.CANARY)
        spec_path = self.work / "spec.json"
        spec_path.write_text(json.dumps(spec))
        receipt = probe.run_command(
            [sys.executable, "-I", "-B", str(script), str(spec_path)], scratch, timeout=5
        )
        self.assertTrue(probe.succeeded(receipt), receipt)
        result = json.loads(receipt["stdout"])
        self.assertEqual(result["network"], "unknown", result)
        self.assertEqual(probe.assess_canary(receipt, spec, True)["status"], "NOT VERIFIED")
        return receipt

    def test_real_connection_refusal_is_not_network_denial(self):
        # Holding a bound socket without listening reserves a port whose native
        # loopback connection fails with ECONNREFUSED, not a policy denial.
        connection = self.bound_loopback_socket()
        self.run_canary(connection.getsockname()[1])

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux listen(0) backlog semantics")
    def test_real_connection_timeout_is_not_network_denial(self):
        listener = self.bound_loopback_socket(listen=True)
        # Fill the sole Linux listen(0) pending connection. A second connection
        # receives no answer and hits the canary's one-second socket timeout.
        try:
            pending = socket.create_connection(listener.getsockname(), timeout=1)
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EACCES):
                self.skipTest("host does not permit the independent loopback control")
            raise
        self.addCleanup(pending.close)
        receipt = self.run_canary(listener.getsockname()[1])
        self.assertGreaterEqual(receipt["elapsed_seconds"], 0.8)
        self.assertLess(receipt["elapsed_seconds"], 5)


class DiagnosticTests(DisposableCase):
    def assert_no_qualification(self, report):
        self.assertEqual(report["kind"], "s0_preflight")
        self.assertEqual(report["s0"]["decision"], "NO-GO")
        self.assertEqual(report["s0"]["status"], "NOT VERIFIED")
        self.assertEqual(report["model_dispatches"], 0)
        self.assertIsNone(report["model_usage"])
        self.assertEqual(report["model_receipts"], [])

    def test_missing_codex_and_correct_offline_controls_do_not_qualify_s0(self):
        output = self.work / "missing-host"
        report = probe.diagnose(output, codex=None, timeout=5)
        self.assert_no_qualification(report)
        self.assertEqual(report["authentication"], "unknown")
        self.assertIn("executable not found", report["host_gap"])
        self.assertNotIn("diagnostic_error", report)
        self.assertEqual(report["probes"], {})
        for variant, expected in (("correct", True), ("alternative", True),
                                  ("defective", False)):
            with self.subTest(variant=variant):
                fixture = report["fixtures"][variant]
                self.assertEqual(fixture["oracle"]["matches_expected"], expected)
                self.assertEqual(fixture["oracle"]["scope"], "fixture_behavior_only")
                self.assertTrue(fixture["inputs_unchanged"])
        self.assertEqual(json.loads((output / "report.json").read_text()), report)

    def test_invented_native_receipts_and_logged_in_status_never_qualify_s0(self):
        output = self.work / "offline-transport"
        report = probe.diagnose(output, self.offline_codex(), timeout=5)
        self.assertNotIn("diagnostic_error", report)
        self.assertEqual(report["authentication"], "authenticated")
        self.assertTrue(probe.succeeded(report["probes"]["login"]))
        self.assertTrue(probe.succeeded(report["boundary"]["receipt"]))
        expected = ("OBSERVED" if report["boundary"]["network_control"] != "unavailable"
                    else "NOT VERIFIED")
        self.assertEqual(report["boundary"]["assessment"]["status"], expected)
        self.assert_no_qualification(report)
        self.assertEqual(json.loads((output / "report.json").read_text()), report)

    def test_existing_run_is_refused_without_overwriting_any_bytes(self):
        output = self.work / "existing-record"
        output.mkdir()
        report_path = output / "report.json"
        report_path.write_bytes(b'{"previous": "untouched"}\n')
        evidence = output / "previous-evidence.txt"
        evidence.write_bytes(b"previous evidence\n")
        before = probe.snapshot(output)
        with self.assertRaises(FileExistsError):
            probe.diagnose(output, self.offline_codex(), timeout=5)
        self.assertEqual(probe.snapshot(output), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
