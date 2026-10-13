"""Finite independent observations; bare subprocesses only for bundled controls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from checks import host_probe as host
from evaluation.matched import corpus
from evaluation.v1.benchmark import PROBE

BATCH_PROBE = PROBE.replace("(app.process if sys.argv[2]=='library' else service.handle)", "service.batch")


def grade(product, task, directory, *, trusted=False, seconds=120):
    product, directory = Path(product), Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    private = directory / "private"
    private.mkdir()
    began = time.monotonic()
    before = host.snapshot(product)
    receipts, failures, unavailable = [], [], []

    def invoke(argv, payload):
        scratch = directory / f"probe-{len(receipts)}"
        scratch.mkdir()
        remaining = seconds - (time.monotonic() - began)
        if remaining <= 0:
            raise ValueError("Finite grading budget exhausted")
        if trusted:
            result = subprocess.run(argv, input=json.dumps(payload), cwd=product,
                                    capture_output=True, text=True, timeout=min(5, remaining),
                                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
            receipt = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        else:
            command = host.sandbox_argv("/opt/homebrew/bin/codex", product.parent, scratch, private)
            shim = "import os,sys,json; r,w=os.pipe(); os.write(w,sys.argv[2].encode()); os.close(w); os.dup2(r,0); os.close(r); os.chdir(sys.argv[3]); a=json.loads(sys.argv[1]); os.execv(a[0],a)"
            command = command[:command.index("--") + 1] + [str(Path(sys.executable).resolve()), "-I", "-B", "-c", shim, json.dumps(argv), json.dumps(payload), str(product)]
            receipt = host.run_command(command, scratch, min(5, remaining))
        receipts.append(receipt)
        if (receipt.get("error") or receipt.get("timed_out") or receipt.get("stdout_truncated")
                or receipt.get("stderr_truncated") or receipt["exit_code"] is None
                or "sandbox-exec: sandbox_apply:" in receipt["stderr"]):
            raise ValueError("Native observation unavailable")
        return receipt

    def observe(label, seam, payload, expected):
        python = str(Path(sys.executable).resolve())
        argv = ([python, "-I", "-B", "-c", BATCH_PROBE if seam == "batch" else PROBE, str(product), seam]
                if seam != "cli" else [python, "-B", str(product / "cli.py")])
        try:
            receipt = invoke(argv, payload)
            if seam == "cli":
                good = (receipt["exit_code"] == 2 and receipt["stdout"] == "" and receipt["stderr"].startswith("ERROR: ")) if expected == "ValueError" else (
                    receipt["exit_code"] == 0 and receipt["stderr"] == "" and json.loads(receipt["stdout"]) == expected)
            else:
                result = json.loads(receipt["stdout"])
                good = receipt["exit_code"] == 0 and result["unchanged"] is True and (
                    result.get("is_value_error") is True if expected == "ValueError" else result.get("ok") is True and result.get("value") == expected)
            if not good:
                failures.append({"obligation": label, "seam": seam, "receipt_index": len(receipts) - 1})
        except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError) as error:
            # Invalid candidate stdout is observed failure, infrastructure loss stays unknown.
            if isinstance(error, (json.JSONDecodeError, KeyError, TypeError)):
                failures.append({"obligation": label, "seam": seam, "receipt_index": len(receipts) - 1})
            else:
                unavailable.append({"obligation": label, "seam": seam, "error": str(error)})

    vectors = corpus.CASES[task] + [("payload container", [], "ValueError")]
    for label, payload, expected in vectors:
        for seam in ("library", "service", "cli"):
            observe(label, seam, payload, expected)
    positive = next((p, e) for _, p, e in vectors if e != "ValueError")
    negative = next(p for _, p, e in vectors if e == "ValueError")
    for payload, expected in [([], []), ([positive[0], positive[0]], [positive[1], positive[1]]),
                              ([positive[0], negative], "ValueError"), ({}, "ValueError")]:
        observe("untested batch and immutability", "batch", payload, expected)
    python = str(Path(sys.executable).resolve())
    for args, expected in [(["--version"], (0, "api-v1\n", "")), (["--unsupported"], None)]:
        try:
            r = invoke([python, "-B", str(product / "cli.py"), *args], {})
            if ((r["exit_code"], r["stdout"], r["stderr"]) != expected if expected else r["exit_code"] != 2):
                failures.append({"obligation": "CLI compatibility", "seam": "cli"})
        except (ValueError, OSError, subprocess.TimeoutExpired) as error:
            unavailable.append({"obligation": "CLI compatibility", "error": str(error)})
    if (product / "cli.py").read_bytes() != corpus.v1.CLI.encode():
        failures.append({"obligation": "unchanged cli.py", "seam": "file bytes"})
    tests = None
    try:
        tests = invoke([python, "-B", "-m", "unittest", "discover", "-s", str(product / "tests")], {})
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        unavailable.append({"obligation": "repository test observation", "error": str(error)})
    if before != host.snapshot(product):
        raise ValueError("Candidate changed during independent grading; stop")
    return {"available": not unavailable, "correct": None if unavailable else not failures,
            "failures": failures, "unavailable": unavailable, "receipts": receipts,
            "repository_tests_passed": None if tests is None else tests["exit_code"] == 0,
            "stale_test_expectation_retained": task == "dependency-order" and (
                product / "tests/test_example.py").read_text() == corpus.public_test(task),
            "elapsed_seconds": time.monotonic() - began}


def controls(*, trusted=True, directory=None):
    rows = []
    with tempfile.TemporaryDirectory(prefix="proofline-matched-controls-") as temporary:
        root = Path(directory or temporary)
        for task in corpus.REQUESTS:
            for variant in ("reference", "alternative", "defective"):
                folder = root / task / variant
                product = corpus.seed(task, folder / "inputs", variant)
                result = grade(product, task, folder / "evaluation", trusted=trusted)
                matched = result["available"] and result["correct"] == (variant != "defective") and result["repository_tests_passed"]
                rows.append({"task": task, "variant": variant, "matched": matched, "grade": result})
    return {"all_12_matched": all(r["matched"] for r in rows), "controls": rows,
            "model_dispatches": 0, "scope": "bundled trusted controls only" if trusted else "native protected controls"}
