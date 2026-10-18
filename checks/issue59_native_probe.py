#!/usr/bin/env python3
"""One-shot, evidence-only live probe for Proofline #59. Not a new runner.

Runs on a GitHub-hosted macOS job after its tool and frozen source checkouts.
It never dispatches a model or enables an unsandboxed fallback.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tarfile
import time

root = Path(os.environ["GITHUB_WORKSPACE"]) / "proofline-59-records"
root.mkdir(exist_ok=True)
tool = Path(os.environ["GITHUB_WORKSPACE"]) / "tool"
src = Path(os.environ["GITHUB_WORKSPACE"]) / "source"
evidence = Path(os.environ["GITHUB_WORKSPACE"]) / "evidence/docs/evidence/issue-15"
sys.path.insert(0, str(tool))
from checks import host_probe as host


def save(name, obj):
    (root / name).write_text(json.dumps(obj, indent=2) + "\n")


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def git(where, ref):
    return subprocess.check_output(
        ["git", "-C", str(where), "rev-parse", ref], text=True).strip()


def command(name, argv, cwd, timeout):
    save(name + "-invocation.json", {"argv": argv, "cwd": str(cwd)})
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
        (root / (name + ".stdout")).write_bytes(p.stdout)
        (root / (name + ".stderr")).write_bytes(p.stderr)
        save(name + "-result.json", {"exit": p.returncode, "elapsed": time.monotonic() - start})
        return p
    except subprocess.TimeoutExpired as e:
        (root / (name + ".stdout")).write_bytes(e.stdout or b"")
        (root / (name + ".stderr")).write_bytes(e.stderr or b"")
        save(name + "-result.json", {"timeout": True, "elapsed": time.monotonic() - start})
        raise


expected = "ead77fde6a5a7ba33e54cc81deb76fced8dbc333"
expected_tree = "544421686de4112ca1ac8bfb118cde750821e3ef"
assert git(src, "HEAD") == expected
assert git(src, "HEAD^{tree}") == expected_tree
assert not subprocess.check_output(["git", "-C", str(src), "status", "--porcelain"])
manifest = json.loads((evidence / "manifest.json").read_bytes())
archive = evidence / manifest["archive"]
assert sha(archive) == manifest["archive_sha256"]

original = root / "original"
original.mkdir(mode=0o700)
seen = set()
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        parts = PurePosixPath(member.name)
        assert not parts.is_absolute() and ".." not in parts.parts
        if member.isdir():
            continue
        assert member.isfile() and member.name in manifest["files"]
        item = tar.extractfile(member)
        assert item is not None
        assert hashlib.sha256(item.read()).hexdigest() == manifest["files"][member.name]
        seen.add(member.name)
    assert seen == set(manifest["files"])
    tar.extractall(original, filter="data")

export = original / "export"
before = {file.name: sha(file) for file in export.iterdir()}
assert before["source-S1.txt"] == "e1d61d83be03e8c442d05d1953bd2de47cd3a5a17a755c87d81826c56cb163f8"
python = str(Path(sys.executable).resolve())
node = str(Path(shutil.which("node")).resolve())
codex = str(Path(shutil.which("codex")).resolve())
assert subprocess.check_output([node, "--version"], text=True).strip() == "v22.16.0"
assert subprocess.check_output([codex, "--version"], text=True).strip() == "codex-cli 0.162.1"

openssl = Path("/System/Library/OpenSSL/openssl.cnf")
inputs = root / "startup-inputs"
scratch = root / "startup-scratch"
private = root / "startup-private"
for directory in (inputs, scratch, private):
    directory.mkdir()
profile = host.permission_profile(inputs, scratch, private)
save("identity.json", {
    "host": platform.platform(), "python": python, "node": node, "codex": codex,
    "tool_sha": git(tool, "HEAD"), "source_sha": expected, "source_tree": expected_tree,
    "tool_clean": not bool(subprocess.check_output(["git", "-C", str(tool), "status", "--porcelain"])),
    "run_id": os.environ["GITHUB_RUN_ID"], "event": os.environ["GITHUB_EVENT_NAME"],
    "openssl_path": str(openssl), "openssl_exists": openssl.exists(),
    "openssl_is_file": openssl.is_file(), "openssl_symlink": openssl.is_symlink(),
    "openssl_resolved": str(openssl.resolve(strict=False)),
    "openssl_read_scope": profile["filesystem"].get(str(openssl)),
    "scope": profile, "export_sha256": before, "check_model_dispatches": 0,
})

# Direct native Node bootstrap in the exact same Codex permission construction.
sandbox = host.sandbox_argv(codex, inputs, scratch, private)
tail = sandbox.index("--")
user = [node, "-e", "console.log('NODE_BOOTSTRAPPED')"]
exec_argv = [python, "-I", "-B", "-c",
             "import json,os,sys; a=json.loads(sys.argv[1]); os.execv(a[0],a)",
             json.dumps(user)]
startup = host.run_command(
    sandbox[:tail + 1] + exec_argv, scratch, timeout=25,
    env={"PATH": "/usr/bin:/bin", "TMPDIR": str(scratch)})
save("node-startup-receipt.json", startup)
node_started = startup.get("exit_code") == 0 and "NODE_BOOTSTRAPPED" in startup.get("stdout", "")

r1 = [node, "--test", "--test-name-pattern=^R1", "test/audit-cli.test.mjs"]
r2 = [node, "--test", "--test-name-pattern=^R2", "test/audit-cli.test.mjs"]
scenarios = [
    ("invalid-map", [r1], {"R1": [{"index": 0, "argv": r2}]}),
    ("r1-only", [r1], {"R1": [{"index": 0, "argv": r1}]}),
    ("r1-r2", [r1, r2], {"R1": [{"index": 0, "argv": r1}], "R2": [{"index": 1, "argv": r2}]}),
]
results = {}
for name, checks, links in scenarios:
    save(name + "-checks.json", checks)
    save(name + "-links.json", links)
    argv = [python, "-B", str(tool / "proofline.py"), "check",
            "--repo", str(src),
            "--source", str(export / "source-S1.txt"),
            "--intentline-export", str(export),
            "--checks", str(root / (name + "-checks.json")),
            "--intentline-links", str(root / (name + "-links.json")),
            "--seconds", "200", "--check-seconds", "40",
            "--output", str(root / (name + "-record"))]
    p = command(name, argv, tool, 240)
    report = root / (name + "-record/report.json")
    entry = {"exit": p.returncode, "report_exists": report.is_file()}
    if report.is_file():
        data = json.loads(report.read_bytes())
        entry.update({
            "status": data.get("status"), "tree": data.get("candidate_tree"),
            "canaries": data.get("boundary", {}).get("assessment", {}).get("status"),
            "requirements": [
                {"id": row.get("id"), "status": row.get("status")}
                for row in data.get("promise_evidence", {}).get("requirements", [])],
        })
        st = command(name + "-status",
                     [python, "-B", str(tool / "proofline.py"),
                      "status", str(report), "--show-source"], tool, 70)
        entry["status_exit"] = st.returncode
    results[name] = entry
after = {file.name: sha(file) for file in export.iterdir()}
save("export-after.json", after)
assert before == after
assert not subprocess.check_output(["git", "-C", str(src), "status", "--porcelain"])
save("summary.json", {"node_bootstrapped": node_started, "results": results,
                      "coverage_completeness": "UNKNOWN"})
print(json.dumps({"node_bootstrapped": node_started, "results": results}, indent=2), flush=True)
assert node_started, "Node did not start inside the native protected process"
assert results["invalid-map"]["exit"] == 1, results["invalid-map"]
for name in ("r1-only", "r1-r2"):
    record = results[name]
    assert record["exit"] == 0 and record["status"] == "CHECKS PASSED", record
    assert record["canaries"] == "OBSERVED", record
    assert record["tree"] == expected_tree
