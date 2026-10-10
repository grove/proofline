#!/usr/bin/env python3
"""Operator-only, predeclared CLI observations; never a live model verdict.

Expose only a single worker directory to each real reviewer/prover. Neither this
file nor its answer-bearing neighbors belong in a worker's accessible tree.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ERROR_TEXT = "username must not be empty or whitespace-only"

# These expected values come from source.md, not from importing or inspecting
# any candidate. Keep the table fixed before judging host/model runs.
BLANK_CASES = (
    ("empty", ""),
    ("spaces", "   "),
    ("tab", "\t"),
    ("line_breaks", "\r\n"),
    ("nonbreaking_space", "\u00a0"),
    ("mixed_unicode_whitespace", "\t \u0085\u2003\u2028\u3000\r\n"),
)
VALID_CASES = (
    ("ordinary", "alice"),
    ("surrounding_spaces", "  Alice  "),
    ("internal_whitespace", "a\t b\nc"),
    ("unicode_name", "\u00c5se\u2603"),
    ("decomposed_unicode", "e\u0301"),
    ("dash_name", "--help"),
    ("zero_width_space", "\u200b"),
)
# POSIX argv may contain bytes that Python preserves through surrogateescape.
# This fixed string represents b"nonblank-\xff"; the expected value must survive
# JSON round-tripping even though it cannot be emitted as literal UTF-8.
POSIX_VALID_CASES = (("posix_undecodable_argument", "nonblank-\udcff"),)


def _probe(script, name, criterion, arguments, kind, expected=None):
    observation = {
        "name": name, "criterion": criterion, "arguments": arguments,
        "status": "NOT_EXECUTED", "failures": [],
    }
    try:
        with tempfile.TemporaryDirectory(prefix="proofline-s0-oracle-") as scratch:
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(script), *arguments],
                cwd=scratch, capture_output=True, text=True, encoding="utf-8",
                timeout=5, check=False,
            )
            unexpected_files = sorted(
                str(path.relative_to(scratch)) for path in Path(scratch).rglob("*")
            )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        observation["error"] = f"{type(error).__name__}: {error}"
        return observation

    observation.update(returncode=result.returncode, stdout=result.stdout,
                       stderr=result.stderr)
    failures = observation["failures"]
    expected_status = 0 if kind in ("valid", "help") else 2
    if result.returncode != expected_status:
        failures.append(f"expected exit status {expected_status}")
    if kind == "valid":
        try:
            payload = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            failures.append("stdout was not one JSON value")
        else:
            if payload != {"username": expected}:
                failures.append("JSON did not preserve exactly the supplied username")
        if result.stderr:
            failures.append("successful command wrote to stderr")
    elif kind == "help":
        if "usage:" not in result.stdout.lower() or "username" not in result.stdout:
            failures.append("help did not describe the username interface")
        if result.stderr:
            failures.append("help wrote to stderr")
    else:
        if result.stdout:
            failures.append("rejected command wrote success output to stdout")
        if kind == "blank" and ERROR_TEXT not in result.stderr:
            failures.append("blank-name error did not explain the validation failure")
        if kind == "usage" and "usage:" not in result.stderr.lower():
            failures.append("argument error did not provide usage on stderr")
    if unexpected_files:
        failures.append("command created files in execution scratch")
        observation["unexpected_scratch_files"] = unexpected_files
    observation["status"] = "MISMATCH" if failures else "MATCH"
    return observation


def inspect_candidate(path: Path) -> dict:
    """Observe the public CLI against fixed expectations, without model calls.

    This function executes product code. The caller owns any sandbox, input
    protection, frozen Git identity, and independent host invocation receipts.
    """
    candidate = Path(path).resolve()
    script = candidate / "username.py"
    report = {
        "oracle": "s0-username-v1", "scope": "fixture_behavior_only",
        "candidate_path": str(candidate), "matches_expected": False,
        "observations": [],
        "limitations": [
            "Offline fixture observations are not live independent review or proof.",
            "No host isolation, immutable identity, or invocation receipt is established.",
            "Scratch is inspected; external file and network effects are not qualified.",
        ],
    }
    if not script.is_file():
        report["error"] = "Required public entry point username.py is unavailable."
        return report

    observations = report["observations"]
    for name, value in BLANK_CASES:
        observations.append(_probe(script, name, "U1", ["--", value], "blank"))
    for name, value in VALID_CASES:
        observations.append(_probe(script, name, "U2", ["--", value], "valid", value))
    if os.name == "posix":
        for name, value in POSIX_VALID_CASES:
            observations.append(_probe(script, name, "U2", ["--", value], "valid", value))
    observations.append(_probe(script, "ordinary_without_terminator", "U3",
                               ["alice"], "valid", "alice"))
    for flag in ("-h", "--help"):
        observations.append(_probe(script, "help_" + flag, "U3", [flag], "help"))
    observations.append(_probe(script, "missing_argument", "U3", [], "usage"))
    observations.append(_probe(script, "extra_argument", "U3", ["alice", "bob"], "usage"))
    report["matches_expected"] = all(item["status"] == "MATCH" for item in observations)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path,
                        help="directory containing one fixture's username.py")
    report = inspect_candidate(parser.parse_args().candidate)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    if report["matches_expected"]:
        return 0
    if not report["observations"] or any(
        item["status"] == "NOT_EXECUTED" for item in report["observations"]
    ):
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
