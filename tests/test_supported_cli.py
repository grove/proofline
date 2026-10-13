"""Only the supported lightweight command surface is public."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "proofline.py"


class SupportedCliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, "-B", str(CLI), *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=20)

    def test_only_run_check_and_status_are_advertised(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{run,check,status}", result.stdout)
        self.assertNotIn("deliver", result.stdout)
        self.assertNotIn("resume", result.stdout)

    def test_retired_commands_are_not_callable(self):
        for cmd in ("deliver", "resume", "inspect-contract", "inspect-intentline"):
            with self.subTest(command=cmd):
                result = self.invoke(cmd)
                self.assertNotEqual(result.returncode, 0)

    def test_check_help_has_check_budgets_without_a_coding_stage(self):
        result = self.invoke("check", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--check-seconds", result.stdout)
        self.assertNotIn("--stage-seconds", result.stdout)
        self.assertNotIn("--correct-once", result.stdout)

    def test_correction_is_explicit_and_only_available_in_run(self):
        self.assertIn('--correct-once',self.invoke('run','--help').stdout)
        result=self.invoke('check','--repo','/tmp/product','--request','request',
                           '--command','/usr/bin/true','--correct-once')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unrecognized arguments: --correct-once',result.stderr)

    def test_old_research_record_is_not_read_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "historical.json"
            path.write_text('{"kind":"historical_delivery","status":"LOCAL ACCEPTED"}')
            result = self.invoke("status", str(path))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported bounded run record", result.stderr)
