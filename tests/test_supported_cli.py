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

    def test_only_run_and_status_are_advertised(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{run,status}", result.stdout)
        self.assertNotIn("deliver", result.stdout)
        self.assertNotIn("resume", result.stdout)

    def test_retired_commands_are_not_callable(self):
        for cmd in ("deliver", "resume", "inspect-contract", "inspect-intentline", "check"):
            with self.subTest(command=cmd):
                result = self.invoke(cmd)
                self.assertNotEqual(result.returncode, 0)

    def test_old_research_record_is_not_read_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "historical.json"
            path.write_text('{"kind":"historical_delivery","status":"LOCAL ACCEPTED"}')
            result = self.invoke("status", str(path))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported bounded run record", result.stderr)
