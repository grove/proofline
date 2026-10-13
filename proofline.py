#!/usr/bin/env python3
"""Proofline: optional bounded local coding and explicit checks.

No automated source-promise certification, review stages, or remote publication.
Historical S0–S6 experiments are retained in Git history.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import uuid

from checks import codex_live as live, host_probe as host
from checks.candidate_snapshot import InputGap, git_bytes, capture_base, validate_links, freeze
from checks.native_checks import write_record


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > 3600:
        raise argparse.ArgumentTypeError("seconds must be finite, positive, and at most 3600")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="One isolated coding attempt and explicit checks")
    run.add_argument("--repo", type=Path, required=True)
    run.add_argument("--source", type=Path, required=True)
    run.add_argument("--checks", type=Path, required=True, help="JSON list of command argv arrays")
    run.add_argument("--output", type=Path)
    run.add_argument("--seconds", type=positive_seconds, default=900)
    run.add_argument("--stage-seconds", type=positive_seconds, default=600)
    run.add_argument("--check-seconds", type=positive_seconds, default=120)
    status = sub.add_parser("status", help="Read back exact frozen check receipts")
    status.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    from checks import local_run
    try:
        if args.command == "run":
            output = (args.output or host.ROOT / ".proofline" / "run" / uuid.uuid4().hex).resolve()
            record = local_run.run(args.repo.resolve(), args.source.read_text(),
                json.loads(args.checks.read_text()), output,
                args.seconds, args.stage_seconds, args.check_seconds)
            print(record["status"])
            print(record["assurance"])
            if record.get("candidate_path"):
                print("Candidate: " + record["candidate_path"])
            print("Record: " + str(output / "report.json"))
        else:
            record = local_run.inspect(args.record.resolve())
            print(record["status"])
            print(record["assurance"])
            print("Record: " + str(args.record))
        return 0 if record["status"] == "CHECKS PASSED" else 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
