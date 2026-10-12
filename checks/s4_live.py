#!/usr/bin/env python3
"""Real S4 seeded repair and evidence-only recovery on disposable S0 products."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import time
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as p
from s0_live import oracle_runner, positive_seconds


def qualify(output, seconds=900, stage_seconds=240):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record = {"kind": "s4_live_recovery", "status": "NOT VERIFIED", "cases": [],
              "model_dispatches": 0, "usage": None}
    spec = importlib.util.spec_from_file_location("s4_private_oracle", p.host.FIXTURES / "oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    native = p.live.run_stage
    try:
        for case in ("seeded-product-repair", "evidence-only-recovery"):
            directory = output / case
            directory.mkdir()
            source = directory / "source"
            shutil.copytree(p.host.FIXTURES / "workers" / "baseline", source)
            p.host.git(source, "init", "--quiet", "--template=")
            p.host.git(source, "add", "--all")
            p.host.git(source, "commit", "--quiet", "-m", "S4 disposable source")
            interventions = []
            proofs = 0
            implementations = 0
            def worker(codex, stage_dir, inputs, identity, role, preferences, timeout, **kwargs):
                nonlocal proofs, implementations
                if role == "prover":
                    proofs += 1
                    if case == "evidence-only-recovery" and proofs == 1:
                        original = kwargs["make_prompt"]
                        def weak_prompt(*args, **options):
                            return original(*args, **options) + "\nQualification fault injection for this first proof only: execute the boundary canary, but perform no behavioral probes. All behavioral criteria must remain NOT VERIFIED with empty commands; report the missing behavioral observations as insufficient evidence. Do not change product. A later independent proof will remedy this intentionally weak handoff.\n"
                        kwargs["make_prompt"] = weak_prompt
                        interventions.append("First proof intentionally lacks behavioral observations; native report remains NOT VERIFIED")
                result = native(codex, stage_dir, inputs, identity, role, preferences, timeout, **kwargs)
                if role == "implementer":
                    implementations += 1
                    if case == "seeded-product-repair" and implementations == 1 and result["status"] == "OBSERVED":
                        # Host-only fault injection, before candidate freeze and independent review.
                        (inputs / "product" / "username.py").write_bytes((p.host.FIXTURES / "workers" / "defective" / "username.py").read_bytes())
                        interventions.append("Seeded empty-only validator after initial implementation, before freeze/review")
                return result
            entry = {"case": case, "interventions": interventions, "run_record": str(directory / "run" / "report.json")}
            record["cases"].append(entry)
            p.write_record(output / "report.json", record)
            print(case, flush=True)
            if case == "evidence-only-recovery":
                child = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                    "--interrupt-delivery", str(source), str(directory / "run"),
                    "--seconds", str(seconds), "--stage-seconds", str(stage_seconds)], check=False)
                if child.returncode != 75:
                    raise ValueError("Controlled interruption did not reach the completed independent review")
                interventions.append("Controller exited after the native reviewer result was persisted; another process resumed the same episode")
                with patch.object(p.live, "run_stage", side_effect=worker):
                    result = p.resume(directory / "run" / "report.json")
            else:
                with patch.object(p.live, "run_stage", side_effect=worker):
                    result = episode(source, directory / "run", seconds, stage_seconds)
            confirmed = p.inspect_record(Path(entry["run_record"]))
            entry.update(status=confirmed["status"], dispatches=result["model_dispatches"],
                         correction_rounds=result["correction_rounds"], elapsed_seconds=result["elapsed_seconds"],
                         usage=[s.get("usage") for s in result["stages"]])
            record["model_dispatches"] += result["model_dispatches"]
            operator = directory / "operator"
            operator.mkdir()
            inputs = operator / "inputs"
            inputs.mkdir()
            shutil.copytree(result["candidate_path"], inputs / "product", symlinks=True)
            private = operator / "private"
            private.mkdir()
            receipts = []
            before = p.host.snapshot(inputs)
            entry["oracle"] = oracle.inspect_candidate(inputs / "product",
                runner=oracle_runner(p.host.find_codex(None), inputs, private, receipts))
            entry["oracle_receipts"] = receipts
            entry["unchanged"] = p.host.snapshot(inputs) == before
            roles = [s["role"] for s in result["stages"]]
            expected = (["implementer", "reviewer", "implementer", "reviewer", "prover"] if case == "seeded-product-repair" else
                        ["implementer", "reviewer", "prover", "prover"])
            entry["matched"] = (confirmed["status"] == "LOCAL ACCEPTED" and roles == expected and
                entry["oracle"]["matches_expected"] and entry["unchanged"] and
                (result["correction_rounds"] == 1 if case == "seeded-product-repair" else
                 result["correction_rounds"] == 0 and result["stages"][2]["binding"] == result["stages"][3]["binding"] and
                 result["current_checks"]["reviewer"] == 1))
            p.write_record(output / "report.json", record)
        if all(c["matched"] for c in record["cases"]):
            record["status"] = "OBSERVED"
    except (OSError, ValueError, KeyError, RuntimeError, KeyboardInterrupt) as exc:
        record["error"] = str(exc) or type(exc).__name__
    finally:
        record["elapsed_seconds"] = round(time.monotonic() - started, 6)
        p.write_record(output / "report.json", record)
    return record


def episode(source, output, seconds, stage_seconds):
    return p.deliver(source, (p.host.FIXTURES / "source.md").read_text(),
        (p.host.FIXTURES / "accepted-input.md").read_text(), output, seconds, stage_seconds, 120,
        execution_map=f"Use {Path(sys.executable).resolve()} -I -B <product>/username.py as the public CLI. Existing tests: <product>/test_username.py. Standard library only.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=p.host.ROOT / ".proofline" / "s4-live" / uuid.uuid4().hex)
    parser.add_argument("--seconds", type=positive_seconds, default=900, help="Per-episode cumulative budget")
    parser.add_argument("--stage-seconds", type=positive_seconds, default=240)
    parser.add_argument("--interrupt-delivery", type=Path, nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.interrupt_delivery:
        native = p.live.run_stage
        def interrupt(*values, **kwargs):
            result = native(*values, **kwargs)
            if result["role"] == "reviewer" and result["status"] == "OBSERVED" and result["report"]["verdict"] == "PASS":
                os._exit(75)
            return result
        with patch.object(p.live, "run_stage", side_effect=interrupt):
            episode(*args.interrupt_delivery, args.seconds, args.stage_seconds)
        return 2
    result = qualify(args.output.resolve(), args.seconds, args.stage_seconds)
    print(result["status"] + ": " + str(args.output / "report.json"))
    return 0 if result["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
