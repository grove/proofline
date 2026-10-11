#!/usr/bin/env python3
"""Sanity-check the fixed answer key and the deliberately limited old tests."""

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest

from oracle import inspect_candidate


FIXTURES = Path(__file__).resolve().parent / "workers"


def tree_identity(root):
    """Observe fixture contents and modes before/after ordinary execution."""
    return {
        str(path.relative_to(root)): (
            stat.S_IMODE(path.stat().st_mode),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in root.rglob("*") if path.is_file()
    }


class OracleControls(unittest.TestCase):
    def test_fixed_controls_through_public_cli(self):
        for name, expected in (("baseline", False), ("correct", True),
                               ("alternative", True), ("defective", False)):
            with self.subTest(candidate=name):
                candidate = FIXTURES / name
                before = tree_identity(candidate)
                report = inspect_candidate(candidate)
                self.assertEqual(report["matches_expected"], expected, report)
                self.assertEqual(report["scope"], "fixture_behavior_only")
                self.assertEqual(len(report["observations"]), 19 if os.name == "posix" else 18)
                self.assertNotIn("NOT_EXECUTED", {
                    item["status"] for item in report["observations"]
                })
                by_name = {item["name"]: item for item in report["observations"]}
                if os.name == "posix":
                    argument_probe = by_name["posix_undecodable_argument"]
                    self.assertEqual(argument_probe["status"], "MATCH")
                    self.assertEqual(
                        json.loads(argument_probe["stdout"]),
                        {"username": "nonblank-\udcff"},
                    )
                if not expected:
                    self.assertEqual({
                        item["criterion"] for item in report["observations"]
                        if item["status"] != "MATCH"
                    }, {"U1"})
                if name == "defective":
                    self.assertEqual(by_name["empty"]["status"], "MATCH")
                    self.assertEqual(by_name["spaces"]["status"], "MISMATCH")
                    self.assertEqual(by_name["nonbreaking_space"]["status"], "MISMATCH")
                self.assertEqual(tree_identity(candidate), before)

    def test_existing_tests_are_green_even_on_the_defect(self):
        for name in ("baseline", "correct", "alternative", "defective"):
            with self.subTest(candidate=name):
                candidate = FIXTURES / name
                before = tree_identity(candidate)
                result = subprocess.run(
                    [sys.executable, "-I", "-B", str(candidate / "test_username.py")],
                    capture_output=True, text=True, timeout=30, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(tree_identity(candidate), before)

    def test_missing_entry_point_cannot_match(self):
        report = inspect_candidate(FIXTURES / "unavailable")
        self.assertFalse(report["matches_expected"])
        self.assertEqual(report["observations"], [])
        self.assertIn("unavailable", report["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
