#!/usr/bin/env python3
"""Run the S0 live Codex experiment. Requires macOS and an authenticated CLI.

This is qualification glue for fixed disposable fixtures, not S1 delivery.
No imported report, fake executable, or user-provided positive verdict is accepted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

import codex_live as live
from codex_live import run_stage
import host_probe as host


def write_record(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def oracle_runner(codex, inputs, private, receipts):
    def run(argv, *, cwd, timeout, **unused):
        scratch = Path(cwd).resolve()
        command = host.sandbox_argv(codex, inputs, scratch, private)
        # Codex parses UTF-8 argv; reconstruct POSIX surrogateescaped arguments inside its sandbox.
        command = command[:command.index("--") + 1] + [str(Path(sys.executable).resolve()),
            "-I", "-B", "-c", "import json,os,sys; a=json.loads(sys.argv[1]); os.execv(a[0],a)",
            json.dumps(argv, ensure_ascii=True)]
        receipt = host.run_command(command, scratch, timeout,
                                   env={"PATH": "/usr/bin:/bin", "TMPDIR": str(scratch)})
        receipts.append(receipt)
        if receipt.get("error") or receipt["timed_out"] or any(
                receipt.get(key) for key in ("stdout_truncated", "stderr_truncated")):
            raise OSError("Sandboxed oracle observation unavailable")
        return subprocess.CompletedProcess(argv, receipt["exit_code"], receipt["stdout"], receipt["stderr"])
    return run



def qualify(output: Path, seconds: float, stage_seconds: float):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record = {"schema_version": 1, "kind": "s0_live", "started_at": datetime.now(timezone.utc).isoformat(),
              "host": {"system": platform.system(), "release": platform.release(),
                       "machine": platform.machine(), "python": platform.python_version()},
              "limits": {"seconds": seconds, "stage_seconds": stage_seconds, "dispatches": 7},
              "model_dispatches": 0, "stages": [], "s0": {"status": "NOT VERIFIED", "decision": "NO-GO"}}
    path = output / "report.json"

    def save():
        record["elapsed_seconds"] = round(time.monotonic() - started, 6)
        write_record(path, record)

    def stage(inputs, identities, role):
        remaining = seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise ValueError("Cumulative experiment budget exhausted; preserved all completed evidence")
        record["model_dispatches"] += 1
        record["active_stage"] = {"role": role, "inputs": str(inputs), "status": "dispatching"}
        save()
        print(f"[{record['model_dispatches']}/7] {role}: {inputs.parent.name}", flush=True)
        result = run_stage(codex, inputs.parent, inputs, identities, role, preferences,
                           min(stage_seconds, remaining))
        record["stages"].append(result)
        record.pop("active_stage")
        save()
        if result["status"] != "OBSERVED":
            raise ValueError(result["error"] or "Stage could not be observed")
        return result

    try:
        if platform.system() != "Darwin" or sys.version_info < (3, 11):
            raise ValueError("Live S0 currently supports macOS with Python 3.11+ only")
        codex = host.find_codex(None)
        if not codex:
            raise ValueError("Codex is not on PATH")
        record["codex_path"] = str(Path(codex).resolve())
        record["codex_sha256"] = host.sha256(Path(codex).read_bytes())
        preferences = live.preferences()
        record["model_preferences"] = preferences
        preflight = host.diagnose(output / "preflight", codex, min(15, seconds))
        record["preflight"] = {"path": str(output / "preflight" / "report.json"),
                               "authentication": preflight["authentication"], "host": preflight["host"],
                               "version": preflight.get("probes", {}).get("version")}
        if (preflight["authentication"] != "authenticated" or preflight.get("boundary", {}).get(
                "assessment", {}).get("status") != "OBSERVED"):
            raise ValueError("Native preflight failed; inspect preflight/report.json before model dispatch")
        controls = preflight["fixtures"]
        if any(controls[name]["oracle"]["matches_expected"] != expected or not controls[name]["inputs_unchanged"]
               for name, expected in (("correct", True), ("alternative", True), ("defective", False))):
            raise ValueError("Independent oracle controls failed")

        directory = output / uuid.uuid4().hex
        directory.mkdir()
        inputs = directory / "inputs"
        identities = host.freeze_fixture(inputs, "baseline")
        implementation = stage(inputs, identities, "implementer")
        spec = importlib.util.spec_from_file_location("s0_oracle", host.FIXTURES / "oracle.py")
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        before = host.snapshot(inputs)
        record["oracle_receipts"] = []
        record["implementation_oracle"] = oracle.inspect_candidate(inputs / "product",
            runner=oracle_runner(codex, inputs, directory / "private", record["oracle_receipts"]))
        if (implementation["report"]["verdict"] != "READY" or not record["implementation_oracle"]["matches_expected"]
                or before != host.snapshot(inputs)):
            raise ValueError("Live implementer did not produce a satisfactory unchanged fixture")

        record["controls"] = []
        for variant, expected in (("correct", True), ("alternative", True), ("defective", False)):
            judgments = []
            common = None
            # Neutral, separately readable paths prevent sharing transcripts, scratch, or labels.
            for role in ("reviewer", "prover"):
                directory = output / uuid.uuid4().hex
                directory.mkdir()
                inputs = directory / "inputs"
                identities = host.freeze_fixture(inputs, variant)
                equivalent = {key: value for key, value in identities.items() if key != "candidate_path"}
                if common is not None and common != equivalent:
                    raise ValueError("Review and proof candidates differ")
                common = equivalent
                judgments.append(stage(inputs, identities, role))
            accepted = judgments[0]["report"]["verdict"] == "PASS" and judgments[1]["report"]["verdict"] == "PROVEN"
            defect_observed = any(row["id"] == "U1" and row["status"] == "VIOLATED"
                                  for row in judgments[1]["report"]["criteria"])
            matched = accepted if expected else (not accepted and defect_observed)
            record["controls"].append({"variant": variant, "expected_accepted": expected, "matched": matched})
            save()
        threads = [item["thread_id"] for item in record["stages"]]
        if len(set(threads)) != 7 or not all(item["matched"] for item in record["controls"]):
            raise ValueError("Fresh-context or independent judgment controls failed")
        record["s0"] = {"status": "OBSERVED", "decision": "GO", "scope": "S0 fixed fixtures on recorded host only"}
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, KeyboardInterrupt) as exc:
        record["s0"]["reason"] = str(exc) or type(exc).__name__
    finally:
        save()
    return record


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > 3600:
        raise argparse.ArgumentTypeError("seconds must be finite, positive, and at most 3600")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New ignored evidence directory; never overwritten")
    parser.add_argument("--seconds", type=positive_seconds, default=1200, help="Cumulative wall-clock budget")
    parser.add_argument("--stage-seconds", type=positive_seconds, default=180, help="Maximum seconds per fresh invocation")
    args = parser.parse_args()
    output = (args.output or host.ROOT / ".proofline" / "live" / uuid.uuid4().hex).resolve()
    try:
        result = qualify(output, args.seconds, args.stage_seconds)
    except OSError as exc:
        print(f"Cannot create new run: {exc}", file=sys.stderr)
        return 1
    print(f"S0: {result['s0']['status']} ({result['s0']['decision']}). {result['s0'].get('reason', '')}")
    print(f"Record: {output / 'report.json'}")
    return 0 if result["s0"]["decision"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
