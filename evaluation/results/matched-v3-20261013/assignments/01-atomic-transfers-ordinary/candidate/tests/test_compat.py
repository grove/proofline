import pathlib
import subprocess
import sys
import unittest


class Compatibility(unittest.TestCase):
    def test_existing_version_flag(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", str(repo / "cli.py"),
                                 "--version"], cwd=repo,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, "api-v1\n", ""))
