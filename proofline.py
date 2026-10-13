#!/usr/bin/env python3
"""Proofline: optional bounded local coding and explicit checks.

No automated source-promise certification, review stages, or remote publication.
Historical S0–S6 experiments are retained in Git history.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import uuid

# The unchanged native host/transport boundary still lives in checks/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
import codex_live as live
import host_probe as host
from checks.native_checks import write_record


class InputGap(ValueError):
    pass


def git_bytes(repo, *args):
    return subprocess.check_output(["git", "-c", "core.hooksPath=" + os.devnull, *args],
        cwd=repo, stderr=subprocess.PIPE, timeout=30,
        env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
             "GIT_OPTIONAL_LOCKS": "0"})


def capture_base(repo, product):
    """Copy exact tracked blobs/modes, without export-ignore, filters, hooks, or user worktree writes."""
    repo = repo.resolve()
    if git_bytes(repo, "rev-parse", "--show-toplevel").decode().strip() != str(repo):
        raise InputGap("--repo must name the Git repository root")
    if git_bytes(repo, "status", "--porcelain", "--untracked-files=normal"):
        raise InputGap("Source repository has local changes. Preserve them in a separate committed snapshot before delivery.")
    source_commit = git_bytes(repo, "rev-parse", "HEAD").decode().strip()
    entries = git_bytes(repo, "ls-tree", "-rz", "--full-tree", source_commit).split(b"\0")
    product.mkdir()
    links = []
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        relative = PurePosixPath(os.fsdecode(raw_path))
        if mode not in {"100644", "100755", "120000"} or kind != "blob":
            raise InputGap("Submodules need a qualified observation path")
        if relative.is_absolute() or any(part in {"..", ".git"} for part in relative.parts):
            raise InputGap("Unsafe Git product path")
        target = product / str(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = git_bytes(repo, "cat-file", "blob", oid)
        if mode == "120000":
            links.append((target, os.fsdecode(raw)))
        else:
            target.write_bytes(raw)
            target.chmod(0o755 if mode == "100755" else 0o644)
    for target, link in links:
        target.symlink_to(link)
    validate_links(product)
    host.git(product, "init", "--quiet", "--template=")
    host.git(product, "add", "--force", "--all")
    host.git(product, "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline comparison base")
    return source_commit, host.git(product, "rev-parse", "HEAD")


def validate_links(product):
    """Permit only aliases to regular files wholly inside this product snapshot."""
    product = product.resolve()
    for path in product.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            link = Path(os.readlink(path))
            lexical = Path(os.path.abspath(path.parent / link)).relative_to(product.resolve())
            target = path.resolve(strict=True)
            relative = target.relative_to(product.resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            raise InputGap("Symlink escapes the candidate, is missing, or is cyclic") from exc
        if (not target.is_file() or link.is_absolute() or
                any(part.casefold() == ".git" for part in (*lexical.parts, *relative.parts))):
            raise InputGap("Symlinks must be relative aliases to regular product files outside Git metadata")


def freeze(product):
    # Reject unsafe aliases and special files before Git processes model-produced content.
    validate_links(product)
    for path in product.rglob("*"):
        parts = path.relative_to(product).parts
        if parts[0] == ".git":
            continue
        if any(part.casefold() == ".git" for part in parts):
            raise InputGap("Nested Git repositories cannot be frozen as regular product files")
        if not (path.is_file() or path.is_dir()):
            raise InputGap("Candidate introduced a link or special file; its execution boundary is not qualified")
    host.git(product, "add", "--force", "--all")
    host.git(product, "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline implementation candidate")
    return host.git(product, "rev-parse", "HEAD"), host.git(product, "rev-parse", "HEAD^{tree}")



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
