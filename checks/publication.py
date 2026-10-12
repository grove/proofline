"""Scoped GitHub publication. Models never receive this authority or credentials."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import uuid

import codex_live as live
import host_probe as host

PR_FIELDS = "number,url,state,headRefName,headRefOid,baseRefName,baseRefOid,isCrossRepository,mergeCommit,mergeable,mergeStateStatus"


def validate_grant(grant):
    if not isinstance(grant, dict) or set(grant) != {"target", "repository", "base", "branch", "actions", "reference", "merge_method"}:
        raise ValueError("Publication requires an exact repository/action-scoped user grant")
    if not isinstance(grant["target"], str) or grant["target"] not in {"pr-created", "pr-merged"} or not isinstance(grant["repository"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", grant["repository"]):
        raise ValueError("Unsupported publication target or GitHub repository")
    if any(part in {".", ".."} for part in grant["repository"].split("/")):
        raise ValueError("Invalid GitHub repository")
    for key in ("base", "branch"):
        value = grant[key]
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", value) or any(
                bad in value for bad in ("..", "//", "/.", ".lock/")) or value.endswith(("/", ".", ".lock")):
            raise ValueError("Invalid publication branch")
    required = {"push", "create-pr"} | ({"merge"} if grant["target"] == "pr-merged" else set())
    if not isinstance(grant["actions"], list) or any(not isinstance(action, str) for action in grant["actions"]) or set(grant["actions"]) != required or len(grant["actions"]) != len(required):
        raise ValueError("Explicit push/create-pr/merge actions must match the target")
    if not isinstance(grant["reference"], str) or not grant["reference"].strip():
        raise ValueError("Record the actual initiating user authorization reference")
    if grant["base"] == grant["branch"] or not isinstance(grant["merge_method"], str) or grant["merge_method"] not in {"merge", "squash", "rebase"}:
        raise ValueError("Invalid publication branches or merge method")
    return grant


def confirm_grant(record, output):
    raw = (output / "effect-grant.json").read_bytes()
    if host.sha256(raw) != record["effect_grant_sha256"]:
        raise ValueError("Initial effect authority changed; resume cannot grant new effects")
    grant = validate_grant(json.loads(raw))
    if grant != record["delivery"]["grant"]:
        raise ValueError("Saved publication scope differs from the initial user grant")
    return grant


class Remote:
    def __init__(self, record, output, save, remaining):
        self.record, self.output, self.save, self.remaining = record, output, save, remaining
        self.grant = confirm_grant(record, output)
        self.directory = output / "publication"
        self.directory.mkdir(exist_ok=True)
        self.repo = self.directory / "git"
        if not self.repo.exists():
            self.repo.mkdir()
            host.git(self.repo, "init", "--quiet", "--template=")
        self.url = "git@github.com:" + self.grant["repository"] + ".git"

    def command(self, argv, *, action=None, exit_codes=(0,)):
        if action and action not in self.grant["actions"]:
            raise ValueError("External action is outside the initial grant")
        if action and self.record["delivery"].get("active_effect"):
            raise ValueError("Reconcile the pending effect before any new mutation")
        allowance = min(30, self.remaining())
        if allowance <= 0:
            raise ValueError("Episode budget exhausted before remote operation; work is preserved")
        directory = self.directory / uuid.uuid4().hex
        directory.mkdir()
        attempt = {"argv": argv, "action": action, "directory": str(directory)}
        self.record["delivery"].setdefault("commands", []).append(attempt)
        if action:
            self.record["delivery"]["active_effect"] = attempt
        self.save()
        live.save_worker(directory, {"state": "launching"})
        env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT="0", GH_HOST="github.com", GH_PROMPT_DISABLED="1")
        process = None
        result = {"exit_code": None, "timed_out": False}
        began = time.monotonic()
        try:
            with (directory / "stdout").open("wb") as out, (directory / "stderr").open("wb") as err:
                process = subprocess.Popen(argv, cwd=self.repo, env=env, stdin=subprocess.DEVNULL,
                                           stdout=out, stderr=err, start_new_session=True)
                live.save_worker(directory, {"state": "running", "pid": process.pid,
                                             "process_start": live.process_start(process.pid)})
                try:
                    result["exit_code"] = process.wait(timeout=allowance)
                except subprocess.TimeoutExpired:
                    result["timed_out"] = True
        finally:
            if process:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            result["elapsed_seconds"] = time.monotonic() - began
            live.save_worker(directory, {"state": "finished", "receipt": result})
            attempt["receipt"] = result
            self.save()
        raw = (directory / "stdout").read_bytes()
        if len(raw) > 2_000_000:
            raise ValueError("Remote readback exceeded its limit")
        result["stdout"] = raw.decode("utf-8")
        if result["exit_code"] not in exit_codes or result["timed_out"]:
            raise ValueError("Remote command failed or timed out; reconcile its retained receipt before retrying")
        return result["stdout"].strip()

    def git(self, *args, action=None):
        required = "push" if args[0] == "push" else None
        if args[0] not in {"push", "fetch", "ls-remote", "rev-parse", "rev-list", "merge-base"} or action != required:
            raise ValueError("Git operation is outside the scoped publication boundary")
        return self.command(["git", "-c", "core.hooksPath=" + os.devnull, *args], action=action)

    def gh(self, *args, action=None):
        required = {"list": None, "checks": None, "create": "create-pr", "merge": "merge"}
        if args[0] not in required or action != required[args[0]]:
            raise ValueError("GitHub operation is outside the scoped publication boundary")
        result = self.command(["gh", "pr", *args, "--repo", "github.com/" + self.grant["repository"]], action=action,
                              exit_codes=(0, 1, 8) if args[0] == "checks" else (0,))
        if args[0] == "checks" and not result:
            attempt = self.record["delivery"]["commands"][-1]
            error = (Path(attempt["directory"]) / "stderr").read_text().strip()
            if attempt["receipt"]["exit_code"] == 1 and error in {
                    "no checks reported on the '" + self.grant["branch"] + "' branch",
                    "no required checks reported on the '" + self.grant["branch"] + "' branch"}:
                return "[]"
            raise ValueError("Required-check readback unavailable; merge cannot proceed")
        return result

    def refs(self):
        rows = self.git("ls-remote", "--refs", self.url,
                        "refs/heads/" + self.grant["base"], "refs/heads/" + self.grant["branch"])
        return {ref: oid for oid, ref in (row.split() for row in rows.splitlines())}

    def pull_request(self):
        rows = json.loads(self.gh("list", "--state", "all", "--head", self.grant["branch"],
                                  "--limit", "100", "--json", PR_FIELDS))
        if len(rows) > 1:
            raise ValueError("Ambiguous remote PRs; reconcile them before continuing")
        return rows[0] if rows else None

    def fetch_tree(self, oid):
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise ValueError("Invalid remote commit identity")
        self.git("fetch", "--no-tags", self.url, oid)
        return self.git("rev-parse", oid + "^{tree}")

    def reconcile(self, observed):
        effect = self.record["delivery"].get("active_effect")
        if not effect:
            return
        worker = live.reconcile_worker(Path(effect["directory"]))
        receipt = worker.get("receipt", {})
        if not observed and (not receipt or receipt.get("timed_out") or receipt.get("exit_code") in (0, None)):
            raise ValueError("Remote effect remains uncertain; read back its result before any retry")
        self.record["delivery"].pop("active_effect")
        self.save()

    def readback(self):
        delivery = self.record["delivery"]
        expected = delivery.get("publication_commit")
        self.record["published"], self.record["merged"] = False, False
        delivery["status"] = "NOT VERIFIED"
        refs, pr = self.refs(), self.pull_request()
        delivery["readback"] = {"refs": refs, "pr": pr, "at": time.time()}
        if not expected or not pr:
            return refs, pr
        if (pr["headRefName"] != self.grant["branch"] or pr["baseRefName"] != self.grant["base"] or
                pr["isCrossRepository"] or pr["headRefOid"] != expected or
                self.fetch_tree(expected) != self.record["identities"]["candidate_tree"] or
                self.git("rev-list", "--parents", "-n", "1", expected).split() !=
                [expected, self.record["source_repository"]["commit"]]):
            raise ValueError("Remote PR candidate or scope changed; fresh independent judgments are required")
        base = refs.get("refs/heads/" + self.grant["base"])
        if pr["state"] == "MERGED":
            merge = pr.get("mergeCommit", {}).get("oid")
            if not merge or self.fetch_tree(merge) != self.record["identities"]["candidate_tree"]:
                raise ValueError("Merged tree differs from the independently accepted candidate")
            if not base or self.fetch_tree(base) != self.record["identities"]["candidate_tree"]:
                raise ValueError("Current remote base differs from the accepted merged tree")
            self.git("merge-base", "--is-ancestor", merge, base)
            self.record["published"], self.record["merged"] = True, True
            delivery["status"] = "PR MERGED"
        else:
            if (pr["state"] != "OPEN" or base != self.record["source_repository"]["commit"] or
                    pr["baseRefOid"] != base or refs.get("refs/heads/" + self.grant["branch"]) != expected):
                raise ValueError("Remote base/head changed or PR closed; publication target is not currently verified")
            self.record["published"] = True
            delivery["status"] = "PR CREATED"
        return refs, pr


def publish(record, output, save, remaining):
    """Reconcile first, execute only granted effects, then read back exact Git objects."""
    if not record.get("delivery") or record["status"] != "LOCAL ACCEPTED":
        return
    record.setdefault("local_acceptance_seconds", record["elapsed_seconds"])
    delivery = record["delivery"]
    try:
        record["published"], record["merged"] = False, False
        delivery["status"] = "NOT VERIFIED"
        remote = Remote(record, output, save, remaining)
        refs, pr = remote.readback()
        active = delivery.get("active_effect")
        if active:
            action = active["action"]
            observed = {"push": refs.get("refs/heads/" + remote.grant["branch"]) == delivery.get("publication_commit"),
                        "create-pr": pr is not None, "merge": pr is not None and pr["state"] == "MERGED"}[action]
            remote.reconcile(observed)
        if record["merged"] or record["published"] and remote.grant["target"] == "pr-created":
            record["next_action"] = "Authorized target confirmed by current remote readback: " + pr["url"]
            return
        source = record["source_repository"]["commit"]
        if refs.get("refs/heads/" + remote.grant["base"]) != source:
            raise ValueError("Remote base moved from the frozen source commit; obtain fresh acceptance before publication/merge")
        if not delivery.get("publication_commit"):
            product = Path(record["candidate_path"])
            remote.git("fetch", "--no-tags", str(product), record["identities"]["candidate_commit"])
            if remote.fetch_tree(source) != host.git(product, "rev-parse", record["base_commit"] + "^{tree}"):
                raise ValueError("Original source and frozen comparison base differ")
            commit = host.git(remote.repo, "commit-tree", record["identities"]["candidate_tree"], "-p", source,
                              "-m", "Independently accepted Proofline candidate")
            delivery["publication_commit"] = commit
            save()
        expected = delivery["publication_commit"]
        if (remote.git("rev-parse", expected + "^{tree}") != record["identities"]["candidate_tree"] or
                remote.git("rev-list", "--parents", "-n", "1", expected).split() != [expected, source]):
            raise ValueError("Publication commit no longer matches the accepted tree and frozen source parent")
        head_ref = "refs/heads/" + remote.grant["branch"]
        if refs.get(head_ref) not in {None, expected}:
            raise ValueError("Publication branch already contains another candidate; no overwrite is authorized")
        if not refs.get(head_ref):
            remote.git("push", remote.url, expected + ":" + head_ref, action="push")
            refs = remote.refs()
            remote.reconcile(refs.get(head_ref) == expected)
            if refs.get(head_ref) != expected:
                raise ValueError("Push was not confirmed by remote readback")
        if not pr:
            body = remote.directory / "pr-body.md"
            body.write_text("Independent local review and behavioral proof accepted this exact product tree.\n\n"
                            + "Candidate tree: `" + record["identities"]["candidate_tree"] + "`\n")
            remote.gh("create", "--base", remote.grant["base"], "--head", remote.grant["branch"],
                      "--title", "Proofline: independently accepted candidate", "--body-file", str(body),
                      "--no-maintainer-edit", action="create-pr")
        refs, pr = remote.readback()
        remote.reconcile(pr is not None)
        if not record["published"]:
            raise ValueError("PR creation not confirmed by remote readback")
        if remote.grant["target"] == "pr-merged" and not record["merged"]:
            while True:
                refs, pr = remote.readback()
                if record["merged"]:
                    break
                checks = json.loads(remote.gh("checks", str(pr["number"]), "--required", "--json", "name,bucket"))
                if not isinstance(checks, list) or any(not isinstance(row, dict) or
                        row.get("bucket") not in {"pass", "fail", "cancel", "skipping", "pending"} for row in checks):
                    raise ValueError("Invalid required-check readback; merge cannot proceed")
                if any(row["bucket"] in {"fail", "cancel"} for row in checks):
                    raise ValueError("Required CI failed; PR remains published and unmerged")
                if all(row["bucket"] in {"pass", "skipping"} for row in checks) and pr["mergeable"] == "MERGEABLE" and pr["mergeStateStatus"] == "CLEAN":
                    break
                pending = any(row["bucket"] == "pending" for row in checks)
                if pr["mergeStateStatus"] in {"DIRTY", "DRAFT"} or not pending and pr["mergeStateStatus"] in {"BLOCKED", "UNSTABLE", "BEHIND"}:
                    raise ValueError("GitHub protections, reviews, CI or conflicts block merge; PR remains published")
                time.sleep(min(2, max(0, remaining())))
            if not record["merged"]:
                remote.gh("merge", str(pr["number"]), "--" + remote.grant["merge_method"],
                          "--match-head-commit", expected, action="merge")
                refs, pr = remote.readback()
                remote.reconcile(pr is not None and pr["state"] == "MERGED")
                if not record["merged"]:
                    raise ValueError("Merge is queued or uncertain; resume to read back completion without redispatch")
        record["next_action"] = "Authorized target confirmed by current remote readback: " + pr["url"]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        delivery["status"] = "PR CREATED" if record["published"] and not record["merged"] else "NOT VERIFIED"
        record["next_action"] = str(exc) or type(exc).__name__
    finally:
        save()


def inspect_remote(record, output):
    if not record.get("delivery"):
        return record
    delivery = record["delivery"]
    started = time.monotonic()
    try:
        _, pr = Remote(record, output, lambda: None, lambda: 30 - (time.monotonic() - started)).readback()
        if record["published"]:
            record["next_action"] = "Current remote readback: " + pr["url"]
        else:
            record["next_action"] = "Remote target is not verified. Resume to reconcile the recorded effects."
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        record["published"], record["merged"] = False, False
        delivery["status"] = "NOT VERIFIED"
        record["next_action"] = str(exc)
    return record
