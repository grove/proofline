"""One fixed native campaign for the frozen v1 baseline; no retry/resume path.

Run with Python 3.11+ on macOS: python -B evaluation/live_v1.py qualify|execute.
Raw evidence stays in ignored .proofline/live-baseline-20261013-v1/.
"""
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import proofline as p
from evaluation.v1 import benchmark as b, tasks, variants

REVISION = "6c85055f3159dbc3f334442dd1d7e6782ece51f2"
STORE = ROOT / ".proofline/live-baseline-20261013-v1"
CODEX = "/opt/homebrew/bin/codex"
PREFS = {"model": "gpt-6.1-sol", "model_reasoning_effort": "high"}
SCHEMA = p.live.object_schema({"completed": {"type": "boolean"}, "summary": p.live.STRING})


def now():
    return datetime.now(timezone.utc).isoformat()


def identities():
    b.frozen_inputs()
    names = p.git_bytes(ROOT, "ls-tree", "-r", "--name-only", REVISION).decode().splitlines()
    # Also protect the retained historical evidence and transport dependency closure.
    names = [n for n in names if n.startswith(("evaluation/v1/", "checks/", "docs/", "archive/"))
             or n == "proofline.py"]
    result = {}
    for name in names:
        raw = p.git_bytes(ROOT, "show", REVISION + ":" + name)
        if (ROOT / name).read_bytes() != raw:
            raise ValueError("Pinned input changed: " + name)
        result[name] = p.host.sha256(raw)
    for name, path in (("runner", Path(__file__)), ("codex", Path(CODEX)),
                       ("python", Path(sys.executable).resolve())):
        result[name] = p.host.sha256(path.read_bytes())
    return result


def verify():
    manifest = json.loads((STORE / "manifest.json").read_text())
    if manifest["identities"] != identities():
        raise ValueError("Frozen evaluator/runtime drift")
    return manifest


def initialize(task, inputs):
    product = tasks.seed(task, inputs)
    p.host.git(product, "init", "--quiet", "--template=")
    p.host.git(product, "add", "--all")
    p.host.git(product, "commit", "--quiet", "-m", "Frozen v1 task seed")
    return product


def boundary(inputs, directory, implementer=False):
    directory.mkdir()
    with p.host.boundary_fixture(directory, inputs, target=inputs / "product/app.py",
         denied_reads={"v1_oracle": str(b.HERE / "oracle.py"),
                       "v1_variants": str(b.HERE / "variants.py"),
                       "repository": str(ROOT / "README.md"),
                       "private_results": str(STORE / "integrity.json"),
                       "model_metadata": str(Path.home() / ".codex/models_cache.json"),
                       "other_candidate": str(STORE / "native-probe-inputs/product/app.py")}) as (spec, before, private_before, network):
        if implementer:
            # Qualify exactly the worker profile, without spending a model dispatch.
            argv = p.live.command(CODEX, inputs, directory / "scratch", directory / "private", PREFS, implementer=True)
            config = argv[argv.index("-c") + 1:]
            profile = next(x for x in config if x.startswith("permissions.proofline="))
            command = [CODEX, "--no-daemon", "-c", profile, "sandbox", "--permission-profile", "proofline",
                       "--include-managed-config", "--cd", str(directory / "scratch"), "--",
                       str(Path(sys.executable).resolve()), "-I", "-B", str(inputs / "canary.py"), str(inputs / "canary.json")]
        else:
            command = p.host.sandbox_argv(CODEX, inputs, directory / "scratch", directory / "private")
        receipt = p.host.run_command(command, directory / "scratch", 15)
    unchanged = before == p.host.snapshot(inputs) and private_before == p.host.snapshot(directory / "private")
    if implementer:
        observed = json.loads(receipt["stdout"]) if p.host.succeeded(receipt) else {}
        expected_writes = dict.fromkeys(spec["writes"], "denied")
        expected_writes["candidate"] = "allowed"
        source_unchanged = all(before["entries"][i] == entry for i, entry in enumerate(p.host.snapshot(inputs)["entries"])
                               if entry["path"] != "product/app.py")
        valid = (observed.get("nonce") == spec["nonce"] and observed.get("writes") == expected_writes
                 and observed.get("reads") == dict.fromkeys(spec["reads"], "denied")
                 and observed.get("mode_change") == "allowed" and observed.get("scratch") is True
                 and observed.get("network") == "denied" and spec["port"] is not None
                 and source_unchanged and private_before == p.host.snapshot(directory / "private"))
        assessment = {"status": "OBSERVED" if valid else "NOT VERIFIED", "observations": observed}
    else:
        assessment = p.host.assess_canary(receipt, spec, unchanged)
    result = {"receipt": receipt, "assessment": assessment, "network_control": network}
    p.write_record(directory / "report.json", result)
    for name in ("canary.py", "canary.json"):
        (inputs / name).unlink()
    if assessment["status"] != "OBSERVED":
        raise ValueError("Native isolation unavailable")
    return result


def grade(product, task, directory, seconds=120):
    """Use the exact frozen comparisons, replacing EVERY candidate invocation.

    Expected outputs remain in this coordinator; only each probe's input crosses
    the native boundary. The offline unsandboxed _invoke is never used here.
    """
    directory.mkdir()
    private = directory / "private"
    private.mkdir()
    receipts = []
    started = time.monotonic()
    before = p.host.snapshot(product)

    def protected(args, payload, cwd, timeout=5):
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise OSError("Independent verification allowance exhausted")
        scratch = directory / ("probe-" + str(len(receipts)))
        scratch.mkdir()
        argv = p.host.sandbox_argv(CODEX, product.parent, scratch, private)
        # A tiny stdin pipe preserves the frozen CLI/library input path.
        shim = "import os,sys,json; r,w=os.pipe(); os.write(w,sys.argv[2].encode()); os.close(w); os.dup2(r,0); os.close(r); a=json.loads(sys.argv[1]); os.execv(a[0],a)"
        argv = argv[:argv.index("--") + 1] + [str(Path(sys.executable).resolve()), "-I", "-B", "-c", shim,
                                             json.dumps(args), json.dumps(payload, ensure_ascii=False)]
        receipt = p.host.run_command(argv, scratch, min(timeout, 5, remaining),
                                     env={"PATH": "/usr/bin:/bin", "TMPDIR": str(scratch), "PYTHONDONTWRITEBYTECODE": "1"})
        receipts.append(receipt)
        if (receipt.get("error") or receipt["timed_out"] or receipt.get("stdout_truncated")
                or receipt.get("stderr_truncated") or "sandbox-exec: sandbox_apply:" in receipt["stderr"]):
            raise OSError("Protected grader observation unavailable")
        return subprocess.CompletedProcess(args, receipt["exit_code"], receipt["stdout"], receipt["stderr"])

    original = b._invoke
    try:
        b._invoke = protected
        result = b.grade_trusted_control(product, task)
        result["available"] = True
    except (OSError, ValueError) as error:
        result = {"available": False, "passed": None, "error": str(error)}
    finally:
        b._invoke = original
    if before != p.host.snapshot(product):
        raise ValueError("Candidate mutated during grading")
    result.update(elapsed_seconds=time.monotonic() - started, receipts=receipts)
    p.write_record(directory / "grade.json", result)
    return result


def outcome(handoff, correct):
    if correct is None:
        return "UNAVAILABLE"
    return ("CORRECT_DELIVERY" if handoff else "UNNECESSARY_BLOCKING") if correct else (
        "FALSE_ACCEPTANCE" if handoff else "FAILED_IMPLEMENTATION")


def qualify():
    if platform.system() != "Darwin":
        raise ValueError("Requires native macOS")
    folder = STORE / "qualification"
    folder.mkdir()
    began = time.monotonic()
    version = p.host.run_command([CODEX, "--version"], folder)
    login = p.host.run_command([CODEX, "login", "status"], folder)
    if not p.host.succeeded(version) or version["stdout"].strip() != "codex-cli 0.162.1" or p.host.auth_status(login) != "authenticated":
        raise ValueError("Specified CLI/authentication unavailable")
    model_cache = json.loads((Path.home() / ".codex/models_cache.json").read_text())
    model = next(m for m in model_cache["models"] if m["slug"] == PREFS["model"])
    if "high" not in [x["effort"] for x in model["supported_reasoning_levels"]]:
        raise ValueError("Specified reasoning effort unavailable")
    ids = identities()
    inputs = folder / "grading-inputs"
    initialize("collision-slugs", inputs)
    boundary(inputs, folder / "grading-boundary")
    inputs = folder / "worker-inputs"
    initialize("collision-slugs", inputs)
    boundary(inputs, folder / "worker-boundary", implementer=True)
    controls = []
    control_started = time.monotonic()
    for task in tasks.TASKS:
        for variant in ("reference", "alternative", "defective"):
            target = folder / "controls" / task / variant
            product = initialize(task, target / "inputs")
            (product / "app.py").write_text(variants.candidate_code(task, variant))
            p.freeze(product)
            result = grade(product, task, target / "evaluation")
            matched = result["available"] and result["passed"] == (variant != "defective")
            controls.append({"task": task, "variant": variant, "matched": matched,
                             "passed": result["passed"], "seconds": result["elapsed_seconds"]})
            p.write_record(folder / "controls.json", controls)
            print("CONTROL", task, variant, matched, flush=True)
            if not matched:
                raise ValueError("Native grader control mismatch; stop original study")
    manifest = {"declared_at": now(), "revision": REVISION, "identities": ids,
                "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
                         "python": platform.python_version()}, "version_receipt": version, "login_receipt": login,
                "model": PREFS, "model_metadata_timestamp": model_cache.get("fetched_at"),
                "model_availability": "listed in native cache; dispatch capacity not yet observed",
                "limits": {"episode_seconds": 900, "coding_seconds": 600, "verification_seconds": 120, "per_probe_seconds": 5},
                "assignments": list(tasks.TASKS), "concurrency": 1, "retries": 0,
                "controls_seconds": time.monotonic() - control_started,
                "qualification_seconds": time.monotonic() - began}
    p.write_record(STORE / "manifest.json", manifest)
    p.write_record(STORE / "results.json", {"status": "QUALIFIED_NOT_DISPATCHED", "assignments": [
        {"sequence": i + 1, "task": task, "status": "NOT_EXECUTED"} for i, task in enumerate(tasks.TASKS)]})


def execute():
    verify()
    report = json.loads((STORE / "results.json").read_text())
    if report["status"] != "QUALIFIED_NOT_DISPATCHED":
        raise ValueError("No retry or resume is permitted")
    report.update(status="RUNNING", started_at=now())
    p.write_record(STORE / "results.json", report)
    began = time.monotonic()
    try:
        for row in report["assignments"]:
            verify()
            started = time.monotonic()
            folder = STORE / "assignments" / (str(row["sequence"]) + "-" + row["task"])
            inputs = folder / "inputs"
            product = initialize(row["task"], inputs)
            base = p.host.git(product, "rev-parse", "HEAD")
            row.update(source_sha256=p.host.sha256((inputs / "source.md").read_bytes()), base_commit=base,
                       base_tree=p.host.git(product, "rev-parse", "HEAD^{tree}"), started_at=now())
            boundary(inputs, folder / "preflight")
            (inputs / "response.schema.json").write_text(json.dumps(SCHEMA))
            source_before = p.host.sha256((inputs / "source.md").read_bytes())
            schema_before = p.host.sha256((inputs / "response.schema.json").read_bytes())
            git_before = p.host.snapshot(product / ".git")
            scratch, private = folder / "scratch", folder / "private"
            scratch.mkdir(); private.mkdir()
            remaining = 600 - (time.monotonic() - started)
            if remaining <= 0:
                raise ValueError("Coding allocation exhausted before dispatch")
            prompt = (f"Implement the entire original request in {inputs / 'source.md'} in {product}. "
                      "Use your ordinary autonomous coding approach, tests and debugging. Only product code and disposable scratch "
                      "are writable; do not commit. Network and external tools are unavailable. Source and Git metadata are protected. "
                      f"Python is {Path(sys.executable).resolve()}. Your cwd/TMPDIR is scratch; use the product path for changes/checks. "
                      "Return completed=true when implementation is finished, otherwise false, with a short summary. "
                      f"You have at most {remaining:.1f} seconds including self-checks and final response.\n")
            row.update(status="DISPATCHED", model_dispatches=1)
            p.write_record(STORE / "results.json", report)
            print("DISPATCH", row["task"], flush=True)
            receipt = p.live.launch(p.live.command(CODEX, inputs, scratch, private, PREFS, implementer=True), prompt, private, remaining)
            row.update(receipt=receipt, handoff=False, usage=None, native_status="UNAVAILABLE")
            if (p.host.snapshot(product / ".git") != git_before or p.host.sha256((inputs / "source.md").read_bytes()) != source_before
                    or p.host.sha256((inputs / "response.schema.json").read_bytes()) != schema_before):
                raise ValueError("Protected worker inputs changed")
            try:
                native = p.live.read_events(receipt)
                response = native["report"]
                if set(response) != {"completed", "summary"} or type(response["completed"]) is not bool or not isinstance(response["summary"], str):
                    raise ValueError("Invalid implementation handoff")
                row.update(native_status="OBSERVED", thread_id=native["thread_id"], usage=native["usage"],
                           completion_response=response, handoff=response["completed"], command_count=len(native["commands"]))
            except (OSError, ValueError, KeyError, TypeError) as error:
                row["native_error"] = str(error)
            row["candidate_commit"], row["candidate_tree"] = p.freeze(product)
            row["candidate_snapshot"] = p.host.snapshot(product)
            row["workflow_seconds"] = time.monotonic() - started
            grade_result = grade(product, row["task"], folder / "evaluation", min(120, 900 - (time.monotonic() - started)))
            row.update(grade=grade_result, correct=grade_result["passed"], finished_at=now(),
                       episode_with_evaluation_seconds=time.monotonic() - started, operator_candidate_edits=0)
            row["status"] = outcome(row["handoff"], row["correct"]) if row["native_status"] == "OBSERVED" else "UNAVAILABLE"
            p.live.reconcile_worker(private)
            verify()
            p.write_record(folder / "result.json", row)
            p.write_record(STORE / "results.json", report)
            print("RESULT", row["task"], row["status"], round(row["workflow_seconds"], 3), flush=True)
            if row["native_status"] != "OBSERVED":
                raise ValueError("Unreliable native worker receipt; no later assignments dispatched")
        report["status"] = "COMPLETE"
    except Exception as error:
        report.update(status="STOPPED", blocker=str(error))
        raise
    finally:
        report.update(finished_at=now(), campaign_seconds=time.monotonic() - began)
        p.write_record(STORE / "results.json", report)


if __name__ == "__main__":
    {"qualify": qualify, "execute": execute}[sys.argv[1]]()
