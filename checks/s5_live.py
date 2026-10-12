#!/usr/bin/env python3
"""Explicitly authorized S5 remote qualification, including separate-process recovery."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as p

MARKER = "proofline-s5-qualification.txt"
CONTENT = "Proofline S5 remote qualification.\n"


def episode(repo, output, grant, seconds, stage_seconds):
    if (repo / MARKER).exists():
        raise ValueError("Qualification marker already exists; use a fresh disposable repository")
    source = ("Add a new root file " + MARKER + " with exactly " + repr(CONTENT) +
              ". Preserve every existing tracked file and its mode. No new dependencies or other changes. "
              "Local workers have no external effect authority; the host owns separately authorized publication.")
    brief = ("| D1 | The new root qualification file contains the exact promised bytes. |\n"
             "| D2 | All existing tracked bytes and modes are preserved, with no other additions or dependencies. |\n")
    return p.deliver(repo, source, brief, output, seconds, stage_seconds, 120,
                     execution_map="Inspect the new root text file and use Git diff to verify existing files are preserved. No product execution or dependencies are needed.",
                     effect_grant=grant)


def qualify(repo, output, grant, seconds=900, stage_seconds=240):
    p.publication.validate_grant(grant)
    if grant["target"] != "pr-merged":
        raise ValueError("Full S5 qualification requires explicit push/create-pr/merge authority")
    output.mkdir(parents=True, exist_ok=False)
    original = p.host.snapshot(repo)
    request = {"repo": str(repo), "output": str(output / "run"), "grant": grant,
               "seconds": seconds, "stage_seconds": stage_seconds}
    p.write_record(output / "request.json", request)
    record = {"kind": "s5_live_publication", "status": "NOT VERIFIED", "usage": None,
              "run_record": str(output / "run" / "report.json"), "authorization": grant,
              "intervention": "Child controller exits after PR creation, before readback; another process resumes the same episode"}
    try:
        child = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                "--interrupt-request", str(output / "request.json")], check=False)
        if child.returncode != 75:
            raise ValueError("Qualification did not reach the controlled post-creation interruption")
        result = p.resume(output / "run" / "report.json")
        confirmed = p.inspect_record(output / "run" / "report.json")
        product = Path(result["candidate_path"])
        publication = output / "run" / "publication" / "git"
        commit = result["delivery"]["publication_commit"]
        diff = p.host.git(publication, "diff", "--name-status", result["source_repository"]["commit"], commit)
        actions = [command["action"] for command in result["delivery"]["commands"] if command["action"]]
        record.update(local_status=confirmed["status"], remote_status=confirmed["delivery"]["status"],
                      dispatches=result["model_dispatches"], elapsed_seconds=result["elapsed_seconds"],
                      usage=[s.get("usage") for s in result["stages"]], actions=actions,
                      remote_readback=confirmed["delivery"]["readback"],
                      private_oracle={"only_expected_addition": diff == "A\t" + MARKER,
                                      "exact_bytes": (product / MARKER).read_bytes() == CONTENT.encode(),
                                      "original_repository_preserved": p.host.snapshot(repo) == original})
        if (confirmed["status"] == "LOCAL ACCEPTED" and confirmed["delivery"]["status"] == "PR MERGED" and
                actions == ["push", "create-pr", "merge"] and all(record["private_oracle"].values())):
            record["status"] = "OBSERVED"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        record["error"] = str(exc) or type(exc).__name__
    finally:
        p.write_record(output / "report.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--github-repo")
    parser.add_argument("--base")
    parser.add_argument("--branch")
    parser.add_argument("--authorize", choices=("push", "create-pr", "merge"), action="append", default=[])
    parser.add_argument("--effect-reference")
    parser.add_argument("--merge-method", choices=("merge", "squash", "rebase"), default="merge")
    parser.add_argument("--seconds", type=p.positive_seconds, default=900)
    parser.add_argument("--stage-seconds", type=p.positive_seconds, default=240)
    parser.add_argument("--output", type=Path, default=p.host.ROOT / ".proofline" / "s5-live" / uuid.uuid4().hex)
    parser.add_argument("--interrupt-request", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.interrupt_request:
            request = json.loads(args.interrupt_request.read_text())
            native = p.publication.Remote.command
            def interrupt(self, argv, **kwargs):
                result = native(self, argv, **kwargs)
                if kwargs.get("action") == "create-pr":
                    os._exit(75)
                return result
            with patch.object(p.publication.Remote, "command", interrupt):
                episode(Path(request["repo"]), Path(request["output"]), request["grant"], request["seconds"], request["stage_seconds"])
            return 2
        if not args.repo:
            raise ValueError("Name a clean local checkout of the explicitly authorized disposable GitHub repository")
        grant = {"target": "pr-merged", "repository": args.github_repo, "base": args.base, "branch": args.branch,
                 "actions": args.authorize, "reference": args.effect_reference, "merge_method": args.merge_method}
        result = qualify(args.repo.resolve(), args.output.resolve(), grant, args.seconds, args.stage_seconds)
        print(result["status"] + ": " + str(args.output / "report.json"))
        return 0 if result["status"] == "OBSERVED" else 2
    except (OSError, ValueError, TypeError) as exc:
        print("NOT VERIFIED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
