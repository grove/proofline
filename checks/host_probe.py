#!/usr/bin/env python3
"""S0 diagnostic workbench. Mechanical preflight is never live qualification.

Uses only Python's standard library, Git, and the installed Codex sandbox.
It does not launch models, change authentication, or accept supplied verdicts.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "checks" / "fixtures" / "s0"
MAX_LOG_BYTES = 16_384


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path) -> dict:
    """Hash bytes, paths, modes, and link targets without following symlinks."""
    entries = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        entry = {"path": path.relative_to(root).as_posix(),
                 "mode": stat.S_IMODE(info.st_mode)}
        if stat.S_ISLNK(info.st_mode):
            entry.update(kind="symlink", target=os.readlink(path))
        elif stat.S_ISREG(info.st_mode):
            entry.update(kind="file", sha256=sha256(path.read_bytes()))
        elif stat.S_ISDIR(info.st_mode):
            entry.update(kind="directory")
        else:
            raise ValueError(f"Unsupported fixture entry: {path}")
        entries.append(entry)
    digest = sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode())
    return {"sha256": digest, "entries": entries}


def redact(text: str) -> str:
    # Login status may include an API key preview. Do not retain even previews.
    text = re.sub(r"(?i)(?:sk-|gh[pousr]_)[A-Za-z0-9_*.-]+", "[redacted]", text)
    text = re.sub(r"(?i)(bearer\s+)\S+", r"\1[redacted]", text)
    text = re.sub(r"(?i)(api key\s*[-:=]\s*)[^\r\n]+", r"\1[redacted]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted email]", text)
    return text


def run_command(argv: list[str], cwd: Path, timeout: float = 15,
                env: dict | None = None) -> dict:
    """Capture a bounded native process receipt, never a model attestation."""
    started = time.monotonic()
    result = {"kind": "process_probe", "invocation_id": str(uuid.uuid4()),
              "argv": argv, "cwd": str(cwd), "exit_code": None,
              "timed_out": False, "stdout": "", "stderr": ""}
    with tempfile.TemporaryFile(dir=cwd) as stdout, tempfile.TemporaryFile(dir=cwd) as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, env=env,
                                       start_new_session=True)
        except OSError as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        else:
            try:
                result["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
            finally:
                # Also reap descendants left behind by an exited probe process.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            for name, stream in (("stdout", stdout), ("stderr", stderr)):
                stream.seek(0)
                raw = stream.read(MAX_LOG_BYTES + 1)
                result[name] = redact(raw[:MAX_LOG_BYTES].decode("utf-8", errors="replace"))
                if len(raw) > MAX_LOG_BYTES:
                    result[name + "_truncated"] = True
    result["elapsed_seconds"] = round(time.monotonic() - started, 6)
    return result


def succeeded(receipt: dict) -> bool:
    return (receipt.get("exit_code") == 0 and receipt.get("timed_out") is False
            and not receipt.get("error"))


def git(product: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="Proofline fixture", GIT_COMMITTER_NAME="Proofline fixture",
               GIT_AUTHOR_EMAIL="fixture@proofline.invalid",
               GIT_COMMITTER_EMAIL="fixture@proofline.invalid",
               GIT_AUTHOR_DATE="2026-10-10T00:00:00+00:00",
               GIT_COMMITTER_DATE="2026-10-10T00:00:00+00:00")
    receipt = run_command(["git", "-c", "core.hooksPath=" + os.devnull,
                           "-c", "commit.gpgSign=false", *args], product, env=env)
    if not succeeded(receipt):
        raise RuntimeError(f"Fixture Git command failed: {receipt}")
    return receipt["stdout"].strip()


def write_diff(product: Path, base: str, destination: Path):
    # Capture complete bytes without diagnostic truncation/redaction or repository diff drivers.
    with destination.open("wb") as output:
        subprocess.run(["git", "--no-pager", "diff", "--no-ext-diff", "--no-textconv",
                        "--no-color", base, "HEAD", "--"], cwd=product, stdout=output,
                       stderr=subprocess.PIPE, check=True, timeout=30,
                       env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1",
                            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_OPTIONAL_LOCKS": "0"})


def freeze_fixture(destination: Path, variant: str) -> dict:
    """Create a disposable Git base/candidate; never edit the user's repository."""
    destination.mkdir()
    for name in ("source.md", "accepted-input.md"):
        shutil.copy2(FIXTURES / name, destination / name)
    product = destination / "product"
    shutil.copytree(FIXTURES / "workers" / "baseline", product,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    git(product, "init", "--quiet", "--template=")
    git(product, "add", "--all")
    git(product, "commit", "--quiet", "-m", "Frozen fixture comparison base")
    base = git(product, "rev-parse", "HEAD")
    # Copy exactly one variant under a neutral product name. Siblings and the
    # private oracle stay outside the sandbox's read allowlist.
    for child in product.iterdir():
        if child.name != ".git":
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    shutil.copytree(FIXTURES / "workers" / variant, product, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    git(product, "add", "--all")
    git(product, "commit", "--quiet", "--allow-empty", "-m", "Frozen fixture candidate")
    return {"source_sha256": sha256((destination / "source.md").read_bytes()),
            "input_sha256": sha256((destination / "accepted-input.md").read_bytes()),
            "base_commit": base, "candidate_commit": git(product, "rev-parse", "HEAD"),
            "candidate_tree": git(product, "rev-parse", "HEAD^{tree}"),
            "candidate_path": str(product)}


CANARY = '''import errno, json, os, socket, stat, sys
from pathlib import Path
spec = json.loads(Path(sys.argv[1]).read_text())
result = {"nonce": spec["nonce"], "writes": {}, "reads": {}, "mode_change": None,
          "scratch": False, "network": "not_observed"}
def denied(exc):
    return "denied" if exc.errno in (errno.EPERM, errno.EACCES, errno.EROFS) else "unknown"
for name, filename in spec["writes"].items():
    try:
        Path(filename).write_text("disposable S0 write canary\\n")
        result["writes"][name] = "allowed"
    except OSError as exc:
        result["writes"][name] = denied(exc)
for name, filename in spec["reads"].items():
    try:
        Path(filename).read_bytes()
        result["reads"][name] = "allowed"
    except OSError as exc:
        result["reads"][name] = denied(exc)
try:
    path = Path(spec["mode_target"])
    path.chmod(stat.S_IMODE(path.stat().st_mode) ^ stat.S_IXUSR)
    result["mode_change"] = "allowed"
except OSError as exc:
    result["mode_change"] = denied(exc)
try:
    Path(spec["scratch_file"]).write_text(spec["nonce"])
    result["scratch"] = True
except OSError:
    pass
if spec["port"] is not None:
    try:
        with socket.create_connection(("127.0.0.1", spec["port"]), timeout=1):
            result["network"] = "allowed"
    except OSError as exc:
        result["network"] = denied(exc)
print(json.dumps(result))
'''


def permission_profile(inputs: Path, scratch: Path, private: Path) -> dict:
    profile = {"filesystem": {":minimal": "read", str(Path(sys.base_prefix).resolve()): "read",
             sys.base_prefix: "read", sys.executable: "read",
             str(Path(sys.executable).resolve()): "read",
             str(inputs): "read", str(scratch): "write", str(private): "deny"},
            "network": {"enabled": False}}
    # Homebrew framework launchers and Codex helpers traverse symlinks outside their resolved binary.
    if platform.system() == "Darwin" and Path("/opt/homebrew").is_dir():
        profile["filesystem"]["/opt/homebrew"] = "read"
    if platform.system() == "Darwin":
        for path in ("/Library/Developer/CommandLineTools/usr/bin",
                     "/Library/Developer/CommandLineTools/usr/libexec/git-core"):
            if Path(path).is_dir():
                profile["filesystem"][path] = "read"
    return profile


def toml(value) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + "=" + toml(v) for k, v in value.items()) + "}"
    return json.dumps(value)


def sandbox_argv(codex: str, inputs: Path, scratch: Path, private: Path) -> list[str]:
    # No user config file is rewritten and managed restrictions remain in force.
    name = "proofline_s0_" + uuid.uuid4().hex
    return [codex, "--no-daemon", "-c", "permissions." + name + "=" +
            toml(permission_profile(inputs, scratch, private)),
            "sandbox", "--permission-profile", name, "--include-managed-config",
            "--cd", str(scratch), "--", str(Path(sys.executable).resolve()), "-I", "-B",
            str(inputs / "canary.py"), str(inputs / "canary.json")]


def assess_canary(receipt: dict, spec: dict, unchanged: bool) -> dict:
    """Exit 0 or a connectivity error alone does not prove a permission boundary."""
    if not succeeded(receipt) or receipt.get("stdout_truncated"):
        return {"status": "NOT VERIFIED", "reason": "Native sandbox probe did not complete."}
    try:
        result = json.loads(receipt["stdout"])
        valid = (isinstance(result, dict) and result.get("nonce") == spec["nonce"]
                 and result.get("writes") == dict.fromkeys(spec["writes"], "denied")
                 and result.get("reads") == dict.fromkeys(spec["reads"], "denied")
                 and result.get("mode_change") == "denied"
                 and result.get("scratch") is True
                 and spec.get("port") is not None
                 and result.get("network") == "denied" and unchanged
                 and Path(spec["scratch_file"]).read_text() == spec["nonce"])
    except (ValueError, KeyError, OSError, TypeError):
        result, valid = None, False
    return {"status": "OBSERVED" if valid else "NOT VERIFIED", "observations": result,
            "inputs_unchanged": unchanged,
            "scope": "native process canaries only; no model or external-tool qualification"}


@contextmanager
def boundary_fixture(output: Path, inputs: Path, target: Path | None = None):
    scratch, private = output / "scratch", output / "private"
    scratch.mkdir()
    private.mkdir()
    for name in ("receipt-canary", "oracle-canary", "other-role-canary"):
        (private / name).write_text("Disposable inaccessible canary, not actual evidence.\n")
    spec = {"nonce": uuid.uuid4().hex,
            "writes": {"source": str(inputs / "source.md"),
                       "input": str(inputs / "accepted-input.md"),
                       "candidate": str(target or inputs / "product" / "username.py"),
                       "git_head": str(inputs / "product" / ".git" / "HEAD"),
                       "receipt": str(private / "receipt-canary")},
            "reads": {name: str(private / name) for name in
                      ("receipt-canary", "oracle-canary", "other-role-canary")},
            "mode_target": str(target or inputs / "product" / "username.py"),
            "scratch_file": str(scratch / "output.txt"), "port": None}
    spec["reads"]["actual_oracle"] = str(FIXTURES / "oracle.py")
    listener = None
    network_control = "unavailable"
    try:
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(4)
        spec["port"] = listener.getsockname()[1]
        with socket.create_connection(("127.0.0.1", spec["port"]), timeout=1):
            network_control = "loopback reachable before sandbox"
    except OSError:
        spec["port"] = None
    (inputs / "canary.py").write_text(CANARY)
    (inputs / "canary.json").write_text(json.dumps(spec))
    before = snapshot(inputs)
    private_before = snapshot(private)
    try:
        yield spec, before, private_before, network_control
    finally:
        if listener is not None:
            listener.close()


def probe_boundary(codex: str, output: Path, inputs: Path, timeout: float, target: Path | None = None) -> dict:
    scratch, private = output / "scratch", output / "private"
    with boundary_fixture(output, inputs, target=target) as (spec, before, private_before, network_control):
        receipt = run_command(sandbox_argv(codex, inputs, scratch, private), scratch, timeout)
    unchanged = before == snapshot(inputs) and private_before == snapshot(private)
    assessment = assess_canary(receipt, spec, unchanged)
    return {"receipt": receipt, "assessment": assessment, "network_control": network_control}


def auth_status(receipt: dict) -> str:
    text = (receipt.get("stdout", "") + receipt.get("stderr", "")).lower()
    if "not logged in" in text:
        return "not authenticated"
    if succeeded(receipt) and "logged in" in text:
        return "authenticated"
    return "unknown"


def find_codex(requested: str | None) -> str | None:
    if requested:
        return shutil.which(requested)
    found = shutil.which("codex")
    return found or shutil.which("/opt/codex/bin/codex")


def diagnose(output: Path, codex: str | None, timeout: float) -> dict:
    """Persist one new diagnostic episode, without manufacturing S0 evidence."""
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {"schema_version": 1, "kind": "s0_preflight", "started_at":
              datetime.now(timezone.utc).isoformat(), "host": {
                  "system": platform.system(), "release": platform.release(),
                  "machine": platform.machine(), "python": platform.python_version(),
                  "codex": codex, "proc_self_exe_available": Path("/proc/self/exe").exists()},
              "model_dispatches": 0, "model_usage": None, "model_receipts": [],
              "fixtures": {}, "probes": {}, "authentication": "unknown"}
    try:
        module_spec = importlib.util.spec_from_file_location("s0_oracle", FIXTURES / "oracle.py")
        oracle = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(oracle)
        for variant in ("correct", "alternative", "defective"):
            inputs = output / ("control-" + variant)
            identities = freeze_fixture(inputs, variant)
            before = snapshot(inputs)
            observation = oracle.inspect_candidate(inputs / "product")
            report["fixtures"][variant] = {
                "identities": identities, "oracle": observation,
                "inputs_unchanged": before == snapshot(inputs)}
        if codex:
            for name, args in (("version", ["--version"]), ("login", ["login", "status"])):
                report["probes"][name] = run_command([codex, *args], output, timeout)
            report["authentication"] = auth_status(report["probes"]["login"])
            report["boundary"] = probe_boundary(codex, output, output / "control-correct", timeout)
        else:
            report["host_gap"] = "Codex executable not found; pass --codex /absolute/path/to/codex."
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report["diagnostic_error"] = redact(f"{type(exc).__name__}: {exc}")
    # There is intentionally no imported-report or fake-host route to qualification.
    report["s0"] = {"decision": "NO-GO", "status": "NOT VERIFIED",
                    "reason": "Fresh live implementer/reviewer/prover receipts and independent "
                              "judgment controls have not been obtained.",
                    "next_action": "Run S0 live qualification on a working authenticated Codex host; "
                                   "do not start S1 until H1–H5 are demonstrated."}
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def positive_timeout(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 < number <= 60:
        raise argparse.ArgumentTypeError("timeout must be finite and between 0 and 60 seconds")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", help="Installed Codex executable (default: PATH, then /opt/codex/bin/codex)")
    parser.add_argument("--output", type=Path, help="New run directory; existing directories are never overwritten")
    parser.add_argument("--timeout", type=positive_timeout, default=15.0, help="Seconds per native probe (default: 15)")
    args = parser.parse_args(argv)
    output = (args.output or ROOT / ".proofline" / "s0" /
              (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])).resolve()
    try:
        report = diagnose(output, find_codex(args.codex), args.timeout)
    except OSError as exc:
        print(f"Could not create a new diagnostic record: {exc}", file=sys.stderr)
        return 1
    print("S0: NOT VERIFIED (NO-GO). No models were invoked.")
    print(f"Authentication: {report['authentication']}.")
    if "diagnostic_error" in report:
        print("Diagnostic error: " + report["diagnostic_error"])
    if "host_gap" in report:
        print(report["host_gap"])
    if "boundary" in report:
        print("Native boundary: " + report["boundary"]["assessment"]["status"] + ".")
        receipt = report["boundary"]["receipt"]
        detail = receipt.get("error") or next(
            (line for line in reversed(receipt.get("stderr", "").splitlines()) if line.strip()), "")
        if detail and not succeeded(receipt):
            print("Host gap: " + detail)
    print(f"Record: {output / 'report.json'}")
    print(report["s0"]["next_action"])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
