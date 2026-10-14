"""Offline CLI-input contract tests: model calls and native check execution are mocked.

These tests verify input fidelity and backward compatibility, not macOS sandbox
qualification or actual delivery correctness.
"""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

import proofline as cli
from checks import local_run


class DirectCliInputs(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="proofline-direct-cli-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "product"
        self.repo.mkdir()
        self.out = self.root / "record"
        self.request = 'Original request:\r\n  Keep Unicode: "José" 🧪\n\n'
        self.commands = [
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
            [sys.executable, "-B", "-c", 'print("$HOME; not a shell pipeline")'],
        ]
        self.source_file = self.root / "request.md"
        self.source_file.write_bytes(self.request.encode("utf-8"))
        self.checks_file = self.root / "checks.json"
        self.checks_file.write_text(json.dumps(self.commands, ensure_ascii=False))

    def invoke(self, *arguments, mode="check", stdin=None):
        calls = []
        def recording(*args):
            calls.append(args)
            return {
                "status": "CHECKS PASSED",
                "assurance": "Synthetic CLI forwarding test; no checks executed.",
                "candidate_path": str(self.repo),
            }
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(local_run, mode, side_effect=recording) as invoked, \
             patch.object(local_run.live, "launch",
                          side_effect=AssertionError("unexpected model dispatch")), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            if stdin is None:
                status = cli.main([mode, "--repo", str(self.repo),
                                   "--output", str(self.out), *arguments])
            else:
                # TextIOWrapper exposes .buffer; universal-newline normalization
                # is deliberately disabled to preserve every UTF-8 source byte.
                stream = io.TextIOWrapper(io.BytesIO(stdin), encoding="utf-8", newline="")
                with patch.object(sys, "stdin", stream):
                    status = cli.main([mode, "--repo", str(self.repo),
                                       "--output", str(self.out), *arguments])
        return status, calls, stdout.getvalue(), stderr.getvalue()

    def file_args(self):
        return ("--source", str(self.source_file),
                "--checks", str(self.checks_file))

    def direct_args(self):
        values = ["--request", self.request]
        for argv in self.commands:
            values.extend(("--command", shlex.join(argv)))
        return tuple(values)

    def test_check_direct_and_existing_files_forward_identical_full_input(self):
        file_result = self.invoke(*self.file_args())
        direct_result = self.invoke(*self.direct_args())
        for status, calls, stdout, stderr in (file_result, direct_result):
            self.assertEqual(status, 0, stderr)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], self.repo.resolve())
            self.assertEqual(calls[0][1], self.request)
            self.assertEqual(calls[0][1].encode("utf-8"), self.source_file.read_bytes())
            self.assertEqual(calls[0][2], self.commands)
            self.assertEqual(calls[0][3], self.out.resolve())
            self.assertEqual(calls[0][4:], (900, 120))
            self.assertIn("CHECKS PASSED", stdout)
        self.assertEqual(file_result[1], direct_result[1])
        self.assertFalse(self.out.exists(), "mocked invocation must not mutate the repo")

    def test_managed_run_supports_same_direct_and_file_inputs(self):
        option = ("--seconds", "90", "--stage-seconds", "60", "--check-seconds", "8")
        a = self.invoke(*self.file_args(), *option, mode="run")
        b = self.invoke(*self.direct_args(), *option, mode="run")
        self.assertEqual(a[0], 0, a[3])
        self.assertEqual(b[0], 0, b[3])
        self.assertEqual(a[1], b[1])
        self.assertEqual(a[1][0][4:], (90.0, 60.0, 8.0))

    def test_tokenization_does_not_execute_shell_metacharacters(self):
        # The quoted program text is one literal argv string: no shell expansion.
        sentinel = self.root / "DO_NOT_CREATE"
        payload = 'print("$(touch ' + str(sentinel) + '); $HOME; *")'
        command = shlex.join([sys.executable, "-c", payload])
        code, calls, _, errors = self.invoke(
            "--request", "Literal argv test", "--command", command)
        self.assertEqual(code, 0, errors)
        self.assertEqual(calls[0][2], [[sys.executable, "-c", payload]])
        self.assertFalse(sentinel.exists())

    def test_invalid_direct_commands_fail_before_any_dispatch(self):
        cases = [
            ("--request", "task", "--command", ""),
            ("--request", "task", "--command", "'unterminated"),
            ("--request", "task", "--command", "python -B -m pytest"),
            ("--request", "task", "--command", "/bin/echo word", "--command", "relative -V"),
            ("--request", "task", "--command", " /bin/echo \0 invalid"),
            ("--request", "  ", "--command", "/bin/echo ok"),
        ]
        for case in cases:
            with self.subTest(case=case):
                status, calls, output, error = self.invoke(*case)
                self.assertNotEqual(status, 0)
                self.assertEqual(calls, [])
                self.assertFalse(self.out.exists())
                self.assertNotEqual(error.strip(), "")

    def test_invalid_file_inputs_fail_before_any_dispatch(self):
        invalid_utf8 = self.root / "bad-request.md"
        invalid_utf8.write_bytes(b"\xff")
        invalid_json = self.root / "bad-checks.json"
        invalid_json.write_text("{broken")
        cases = [
            ("--source", str(invalid_utf8), "--checks", str(self.checks_file)),
            ("--source", str(self.source_file), "--checks", str(invalid_json)),
            ("--source", str(self.source_file), "--checks", str(self.root / "missing")),
        ]
        for case in cases:
            with self.subTest(case=case):
                status, calls, _, stderr = self.invoke(*case)
                self.assertNotEqual(status, 0)
                self.assertEqual(calls, [])
                self.assertNotEqual(stderr.strip(), "")

    def test_cli_reports_unavailable_host_without_pretending_success(self):
        with patch.object(local_run, "check",
                          side_effect=ValueError("The supported native boundary is macOS")) as runner, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
            code = cli.main(["check", "--repo", str(self.repo),
                             "--request", self.request, "--command", "/bin/echo ok"])
        self.assertNotEqual(code, 0)
        self.assertEqual(runner.call_count, 1)
        self.assertIn("macOS", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
