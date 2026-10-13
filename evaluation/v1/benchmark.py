#!/usr/bin/env python3
"""Offline, frozen evaluation preflight; NOT a coding agent or live benchmark.

Only bundled trusted control code is executed here. Never run an untrusted
coding-agent candidate through this bare subprocess harness. Live grading
requires a separately qualified protected host and private grader inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evaluation.v1 import oracle, tasks, variants

HERE = Path(__file__).resolve().parent
PROBE = """import copy,json,sys
sys.path.insert(0,sys.argv[1])
import app,service
payload=json.load(sys.stdin)
before=copy.deepcopy(payload)
try:
    result=(app.process if sys.argv[2]=='library' else service.handle)(payload)
    observation={'ok':True,'value':result,'unchanged':payload==before}
except Exception as error:
    observation={'ok':False,'error':type(error).__name__,'unchanged':payload==before}
print(json.dumps(observation,ensure_ascii=False,sort_keys=True))
"""


def git_blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def frozen_inputs():
    """Verify exact, versioned inputs before any candidate/grader activity."""
    manifest = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in manifest["git_blob_sha1"].items():
        path = HERE / name
        if not path.is_file() or git_blob_id(path.read_bytes()) != expected:
            raise ValueError("Frozen baseline input modified or missing: " + name)
    protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    ledger = json.loads((HERE / "ledger.json").read_text(encoding="utf-8"))
    ids = list(tasks.TASKS)
    if (protocol["tasks"] != ids or list(oracle.VECTORS) != ids or
        list(variants.FUNCTIONS) != ids or
        [item["task"] for item in ledger["assignments"]] != ids):
        raise ValueError("Frozen task population/order/ledger mismatch")
    if len(set(ids)) != 6 or protocol["model_dispatches_planned"] != 6:
        raise ValueError("Expected exactly six ordinary-agent assignments")
    if any(item["status"] != "NOT_EXECUTED" or
           item["seconds"] is not None or item["reported_tokens"] is not None
           for item in ledger["assignments"]):
        raise ValueError("Frozen preparation ledger contains invented observations")
    return protocol, ledger, manifest


def _invoke(args, payload, cwd, timeout=5):
    """Trusted built-in fixtures only; NO untrusted worker-candidate execution."""
    env = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONNOUSERSITE": "1", "PYTHONPATH": ""}
    try:
        return subprocess.run(args, input=json.dumps(payload, ensure_ascii=False),
                              text=True, capture_output=True, cwd=cwd,
                              env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Trusted control execution unavailable: " + str(error)) from error


def _tree_fingerprint(product):
    result = {}
    for file in product.rglob("*"):
        if file.is_symlink():
            raise ValueError("Unexpected linked file in trusted fixture")
        if file.is_file():
            result[file.relative_to(product).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def grade_trusted_control(product, task):
    """Finite public CLI/library/service checks for *generated trusted controls*.

    Do not call on an untrusted coding-agent output without a protected sandbox.
    """
    if task not in oracle.VECTORS:
        raise ValueError("Unknown task")
    product = Path(product).resolve()
    original = _tree_fingerprint(product)
    failures, passes = [], 0
    for index, (payload, expected) in enumerate(oracle.VECTORS[task]):
        for entry in ("library", "service"):
            process = _invoke([sys.executable, "-I", "-B", "-c", PROBE,
                               str(product), entry], payload, product)
            try:
                observed = json.loads(process.stdout)
            except json.JSONDecodeError:
                observed = None
            good = process.returncode == 0 and isinstance(observed, dict) and observed.get("unchanged") is True
            if expected == "ValueError":
                good = good and observed.get("ok") is False and observed.get("error") == "ValueError"
            else:
                good = good and observed.get("ok") is True and observed.get("value") == expected
            if good:
                passes += 1
            else:
                failures.append({"case": index, "seam": entry, "status": "MISMATCH"})
        cli = _invoke([sys.executable, "-B", str(product / "cli.py")],
                      payload, product)
        if expected == "ValueError":
            good = cli.returncode == 2 and cli.stdout == "" and cli.stderr.startswith("ERROR: ")
        else:
            try:
                output = json.loads(cli.stdout)
            except json.JSONDecodeError:
                output = None
            good = cli.returncode == 0 and cli.stderr == "" and output == expected
        if good:
            passes += 1
        else:
            failures.append({"case": index, "seam": "cli", "status": "MISMATCH"})

    version = _invoke([sys.executable, "-B", str(product / "cli.py"), "--version"],
                      {}, product)
    if (version.returncode, version.stdout, version.stderr) != (0, "api-v1\n", ""):
        failures.append({"case": "compatibility", "seam": "cli-version", "status": "MISMATCH"})
    else:
        passes += 1
    unknown = _invoke([sys.executable, "-B", str(product / "cli.py"), "--unsupported"],
                      {}, product)
    if unknown.returncode != 2:
        failures.append({"case": "compatibility", "seam": "cli-arguments", "status": "MISMATCH"})
    else:
        passes += 1
    for name, expected_content in (("cli.py", tasks.CLI),
                                    ("service.py", tasks.SERVICE),
                                    ("tests/test_compat.py", tasks.COMPAT)):
        if (product / name).read_text(encoding="utf-8") != expected_content:
            failures.append({"case": "compatibility", "seam": name, "status": "CHANGED"})
    if original != _tree_fingerprint(product):
        failures.append({"case": "candidate", "seam": "frozen-inputs", "status": "CHANGED"})
    return {"passed": not failures, "observed_passes": passes,
            "total_checks": 3 * len(oracle.VECTORS[task]) + 2,
            "failures": failures}


def run_controls():
    """Exercise all 18 fixed positive/alternative/negative controls once."""
    frozen_inputs()
    outcomes = []
    for task in tasks.TASKS:
        row = {"task": task}
        for variant in ("reference", "alternative", "defective"):
            with tempfile.TemporaryDirectory(prefix="proofline-eval-control-") as temporary:
                output = Path(temporary) / "assignment"
                product = tasks.seed(task, output)
                (product / "app.py").write_text(
                    variants.candidate_code(task, variant), encoding="utf-8")
                observation = grade_trusted_control(product, task)
            row[variant] = {
                "all_finite_checks_passed": observation["passed"],
                "passes": observation["observed_passes"],
                "failures": len(observation["failures"]),
            }
        row["matched"] = (row["reference"]["all_finite_checks_passed"] and
                          row["alternative"]["all_finite_checks_passed"] and
                          not row["defective"]["all_finite_checks_passed"] and
                          row["defective"]["passes"] > 0 and
                          row["defective"]["failures"] > 0)
        outcomes.append(row)
    return {"controls": outcomes, "all_18_matched": all(r["matched"] for r in outcomes),
            "positive_controls": 12, "deliberately_defective_controls": 6,
            "live_model_assignments_executed": 0}


def summarize_unexecuted():
    """Unknown resource measurements are NULL, never silently counted as zero."""
    protocol, ledger, manifest = frozen_inputs()
    return {
        "study": protocol["study_id"],
        "status": "PREPARED_ONLY_NO_LIVE_MODEL_ACCESS",
        "frozen_inputs": manifest["git_blob_sha1"],
        "assigned": len(ledger["assignments"]),
        "executed": 0,
        "unexecuted": len(ledger["assignments"]),
        "independently_correct_deliveries": None,
        "correct_delivery_rate": None,
        "false_acceptances": None,
        "unnecessary_blocks": None,
        "elapsed_seconds_per_correct_delivery": None,
        "reported_tokens_per_correct_delivery": None,
        "operator_effort_seconds": None,
        "dollars_per_correct_delivery": None,
        "reason": ledger["reason"],
        "denominator_policy": "All six assignments stay assigned; no baseline rate until live scoring.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("controls", help="Run only the 18 built-in trusted fixtures")
    seed_parser = sub.add_parser("seed", help="Export only the public task starter; no grader keys")
    seed_parser.add_argument("task", choices=list(tasks.TASKS))
    seed_parser.add_argument("output", type=Path)
    sub.add_parser("report", help="Describe incomplete live baseline without fabricated metrics")
    args = parser.parse_args(argv)
    if args.action == "controls":
        value = run_controls()
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0 if value["all_18_matched"] else 2
    if args.action == "seed":
        frozen_inputs()
        print(tasks.seed(args.task, args.output))
        return 0
    print(json.dumps(summarize_unexecuted(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
