"""Reuse native protected commands; bare subprocesses are for authored controls."""
import json
from pathlib import Path
import sys
import time

from checks import candidate_snapshot as snapshots, host_probe as host
from checks.native_checks import oracle_runner, write_record
from evaluation.recovery import corpus, oracle, probes

CODEX = "/opt/homebrew/bin/codex"
PYTHON = str(Path(sys.executable).resolve())


def invoke(product, script, directory, *, trusted=False, seconds=30):
    directory.mkdir(parents=True, exist_ok=False)
    inputs = directory / "inputs"
    inputs.mkdir()
    if trusted:
        # Only our bundled controls use this path.
        import shutil
        shutil.copytree(product, inputs / "product", ignore=shutil.ignore_patterns(".git"))
    else:
        snapshots.capture_worktree(product, inputs / "product")
    (inputs / "probe.py").write_text(script, encoding="utf-8")
    scratch, private = directory / "scratch", directory / "private"
    scratch.mkdir(); private.mkdir()
    # A read-only candidate uses scratch for temporary output and nested CLI cwd.
    shim = "import os,runpy,sys; sys.path.insert(0,sys.argv[1]); runpy.run_path(sys.argv[2],run_name='__main__')"
    script = (inputs / "probe.py").read_text().replace(
        "'cli.py'", repr(str(inputs / "product/cli.py"))).replace(str(product),str(inputs / "product"))
    (inputs / "probe.py").write_text(script)
    before = host.snapshot(inputs)
    argv = [PYTHON, "-I", "-B", "-c", shim, str(inputs / "product"), str(inputs / "probe.py")]
    receipts = []
    if trusted:
        receipt = host.run_command(argv, scratch, seconds,
                                   env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
        receipts.append(receipt)
    else:
        try:
            oracle_runner(CODEX, inputs, private, receipts)(argv, cwd=scratch, timeout=seconds)
        except OSError:
            pass
    intact = before == host.snapshot(inputs)
    receipt = receipts[0] if len(receipts) == 1 else {}
    available = intact and bool(receipt) and not any(receipt.get(k) for k in
        ("error", "timed_out", "stdout_truncated", "stderr_truncated")) and receipt.get("exit_code") is not None and "sandbox-exec: sandbox_apply:" not in receipt.get("stderr", "")
    result = {"available": available, "receipt": receipt, "inputs_unchanged": intact}
    write_record(directory / "result.json", result)
    return result


def grade(product, task, directory, *, trusted=False, seconds=60):
    started = time.monotonic()
    result = invoke(product, oracle.script(task), directory, trusted=trusted, seconds=seconds)
    receipt = result["receipt"]
    cases = []
    tests = None
    if result["available"]:
        try:
            observed = json.loads(receipt["stdout"])
            cases = observed["cases"]
            tests = observed.get("repository_tests_passed")
            if not isinstance(cases,list) or not cases or any(
                not isinstance(c,dict) or type(c.get("passed")) is not bool for c in cases):
                raise ValueError("Invalid oracle result")
        except (ValueError, KeyError, TypeError):
            cases = [{"label": "candidate import/execution", "passed": False}]
    result.update(correct=not any(not c["passed"] for c in cases) and receipt.get("exit_code")==0 if result["available"] else None,
                  cases=cases, repository_tests_passed=tests, elapsed_seconds=time.monotonic()-started)
    write_record(directory / "result.json", result)
    return result


def controls(directory, *, trusted=True):
    started = time.monotonic()
    rows = []
    for task in corpus.REQUESTS:
        for variant in ("reference", "alternative", "defective", "coverage-gap"):
            folder = directory / task / variant
            product = corpus.seed(task, folder / "seed", variant)
            if not trusted:
                host.git(product,"init","--quiet","--template=")
                snapshots.freeze(product)
            grade_result = grade(product, task, folder / "hidden", trusted=trusted)
            public = invoke(product, probes.script(task), folder / "public", trusted=trusted)
            existing = invoke(product, "import unittest\ns=unittest.defaultTestLoader.discover("+repr(str(product / "tests"))+")\nr=unittest.TextTestRunner().run(s)\nassert r.wasSuccessful()\n", folder / "existing", trusted=trusted)
            matched = (grade_result["available"] and public["available"] and existing["available"] and
                grade_result["correct"] == (variant in ("reference","alternative")) and
                (public["receipt"]["exit_code"]==0) == (variant != "defective") and
                existing["receipt"]["exit_code"]==0)
            rows.append({"task":task,"variant":variant,"matched":matched,
                         "hidden":grade_result,"public":public,"existing":existing})
    result = {"all_matched":all(r["matched"] for r in rows), "controls":rows,
              "elapsed_seconds":time.monotonic()-started,"model_dispatches":0,
              "scope":"bundled authored controls" if trusted else "native protected controls"}
    write_record(directory / "controls.json", result)
    return result
