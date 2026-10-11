"""Existing public-interface regression tests."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class UsernameTests(unittest.TestCase):
    def run_cli(self, *arguments):
        with tempfile.TemporaryDirectory(prefix="username-test-") as scratch:
            return subprocess.run(
                [sys.executable, "-I", "-B", str(Path(__file__).with_name("username.py")),
                 *arguments],
                cwd=scratch, capture_output=True, text=True, encoding="utf-8",
                timeout=5, check=False,
            )

    def test_regular_name(self):
        result = self.run_cli("alice")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"username": "alice"})
        self.assertEqual(result.stderr, "")

    def test_preserves_surrounding_whitespace(self):
        result = self.run_cli("  Alice  ")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"username": "  Alice  "})
        self.assertEqual(result.stderr, "")

    def test_help(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("username", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
