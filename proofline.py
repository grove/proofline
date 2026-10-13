#!/usr/bin/env python3
"""Proofline: optional bounded local coding and explicit checks.

No automated source-promise certification, review stages, or remote publication.
Historical S0–S6 experiments are retained in Git history.
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
from pathlib import Path
import sys
import tempfile
import uuid

from checks import codex_live as live, host_probe as host
from checks.candidate_snapshot import InputGap, git_bytes, capture_base, validate_links, freeze
from checks.native_checks import write_record


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > 3600:
        raise argparse.ArgumentTypeError("seconds must be finite, positive, and at most 3600")
    return number


def original_request(args):
    """Return the original UTF-8 request verbatim, without summaries or cleanup."""
    if args.request is not None:
        return args.request
    if args.request_stdin:
        return sys.stdin.buffer.read().decode("utf-8")
    return args.source.read_bytes().decode("utf-8")


def explicit_checks(args):
    """Turn repeated shell-quoted argument strings into argv, never a shell command.

    The existing JSON-file form remains authoritative for exact argv lists;
    shlex only tokenizes the direct convenience form. Neither path invokes
    a shell or expands variables, substitutions, redirections or glob patterns.
    """
    from checks.local_run import validate_checks
    if args.checks is not None:
        return validate_checks(json.loads(args.checks.read_text(encoding="utf-8")))
    checks = []
    for number, command in enumerate(args.check_commands, 1):
        try:
            argv = shlex.split(command, posix=True)
        except ValueError as error:
            raise ValueError(f"--command #{number}: invalid quoting: {error}") from error
        if not argv:
            raise ValueError(f"--command #{number} is empty; provide an absolute executable and arguments")
        checks.append(argv)
    try:
        return validate_checks(checks)
    except ValueError as error:
        raise ValueError(
            "--command requires an absolute executable path and argument tokens; "
            "use repeated --command options or --checks FILE for exact argv: "
            + str(error)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="One isolated coding attempt and explicit checks")
    check = sub.add_parser("check", help="Model-free protected checks on an existing working candidate")
    for command in (run, check):
        command.add_argument("--repo", type=Path, required=True)
        source_group = command.add_mutually_exclusive_group(required=True)
        source_group.add_argument("--source", type=Path, help="UTF-8 original request file (existing interface)")
        source_group.add_argument("--request", help="Full original request text, including newlines")
        source_group.add_argument("--request-stdin", action="store_true", help="Read exact UTF-8 original request from stdin")
        checks_group = command.add_mutually_exclusive_group(required=True)
        checks_group.add_argument("--checks", type=Path, help="JSON list of argv arrays (existing interface)")
        checks_group.add_argument("--command", dest="check_commands", action="append", help="One quoted executable + arguments; repeat for each check, no shell")
        command.add_argument("--failure-details", type=Path, help="Optional JSON check-indexed expected/observed snippets and R IDs")
        command.add_argument("--output", type=Path)
        command.add_argument("--seconds", type=positive_seconds, default=900)
        command.add_argument("--check-seconds", type=positive_seconds, default=120)
    run.add_argument("--stage-seconds", type=positive_seconds, default=600)
    run.add_argument("--correct-once", action="store_true",
                     help="Opt in to one same-thread correction after a trusted assertion failure")
    advisory = check.add_mutually_exclusive_group()
    advisory.add_argument("--promises", type=Path,
                          help="Optional direct source-quoted R requirements and check links")
    advisory.add_argument("--intentline-export", type=Path,
                          help="Optional completed original-request Intentline --format json export")
    check.add_argument("--intentline-links", type=Path,
                       help="Optional JSON exact R-to-selected-argv links, only with --intentline-export")
    status = sub.add_parser("status", help="Read back exact frozen check receipts")
    status.add_argument("record", type=Path)
    status.add_argument("--show-source", action="store_true",
                        help="Display the complete verified original request (check-only records)")
    args = parser.parse_args(argv)
    from checks import local_run, feedback, promise_evidence, intentline_advisory
    try:
        if args.command in ("run", "check"):
            default = (Path(tempfile.gettempdir()) / "proofline-check" if args.command == "check"
                       else host.ROOT / ".proofline" / "run")
            output = (args.output or default / uuid.uuid4().hex).resolve()
            budgets = ((args.seconds, args.stage_seconds, args.check_seconds) if args.command == "run"
                       else (args.seconds, args.check_seconds))
            source = original_request(args)
            if not source.strip():
                raise ValueError("Original request is empty; use --request TEXT, --request-stdin or --source FILE")
            checks = explicit_checks(args)
            optional = {}
            if args.command == "run":
                optional["correct_once"] = args.correct_once
            if args.failure_details is not None:
                details = json.loads(args.failure_details.read_text(encoding="utf-8"))
                optional["failure_details"] = feedback.validate_failure_details(details,checks)
            if args.command == "check":
                if args.intentline_links is not None and args.intentline_export is None:
                    raise ValueError("--intentline-links requires --intentline-export")
                if args.promises is not None:
                    optional["promise_mapping"] = promise_evidence.read_mapping(args.promises)
                elif args.intentline_export is not None:
                    links = intentline_advisory.read_links(args.intentline_links)
                    optional["intentline_package"] = intentline_advisory.load_export(
                        args.intentline_export,source,checks,links,
                        optional.get("failure_details",[]))
            record = getattr(local_run, args.command)(args.repo.resolve(), source,
                checks, output, *budgets, **optional)
            print(record["status"])
            for line in feedback.format_lines(record):
                print(line)
            for line in promise_evidence.format_lines(record):
                print(line)
            print(record["assurance"])
            if record.get("candidate_path"):
                print("Candidate: " + record["candidate_path"])
            print("Record: " + str(output / "report.json"))
        else:
            record = local_run.inspect(args.record.resolve())
            original = None
            if args.show_source:
                if record.get("kind") != "bounded_local_check" or (
                        record["status"] == "STALE CHECKS" or "snapshot" not in record):
                    raise ValueError("--show-source requires an intact frozen check-only record")
                source_path = args.record.resolve().parent / "inputs" / "source.md"
                if source_path.is_symlink():
                    raise ValueError("Frozen original request is a symbolic link")
                raw = source_path.read_bytes()
                if host.sha256(raw) != record.get("source_sha256"):
                    raise ValueError("Frozen original request differs from the recorded source")
                original = raw.decode("utf-8")
            print(record["status"])
            for line in feedback.format_lines(record):
                print(line)
            for line in promise_evidence.format_lines(record):
                print(line)
            print(record["assurance"])
            print("Record: " + str(args.record))
            if original is not None:
                print("Original request (verbatim UTF-8):")
                sys.stdout.write(original)
        return 0 if record["status"] == "CHECKS PASSED" else 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
