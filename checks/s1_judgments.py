#!/usr/bin/env python3
"""Live S1 source-omission and regression challenges; never a performance benchmark."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as delivery

host, live = delivery.host, delivery.live


def main():
    output = host.ROOT / ".proofline" / "s1-judgments" / uuid.uuid4().hex
    output.mkdir(parents=True)
    record = {"kind": "s1_live_judgments", "status": "NOT VERIFIED", "cases": [],
              "model_dispatches": 0, "limits": {"seconds": 900, "dispatches": 4}}
    started = time.monotonic()
    codex, preferences = host.find_codex(None), live.preferences()
    try:
        for case, expected in (("omitted-source-promise", "NOT VERIFIED"), ("interface-regression", "FAIL")):
            entry = {"case": case, "expected": expected, "stages": [], "matched": False}
            record["cases"].append(entry)
            for role in ("reviewer", "prover"):
                directory = output / uuid.uuid4().hex
                directory.mkdir()
                inputs = directory / "inputs"
                identity = host.freeze_fixture(inputs, "correct")
                if case == "omitted-source-promise":
                    brief = inputs / "accepted-input.md"
                    brief.write_text("\n".join(line for line in brief.read_text().splitlines()
                                              if not line.startswith("| U1 |")) + "\n")
                else:
                    source = inputs / "product" / "username.py"
                    source.write_text(source.read_text().replace("    args = parser.parse_args()\n",
                        '    args = parser.parse_args()\n    if args.username.startswith("-"):\n        parser.error("invalid username")\n'))
                    delivery.freeze(inputs / "product")
                identity = delivery.identities(inputs, identity["base_commit"])
                ids = delivery.criterion_ids((inputs / "accepted-input.md").read_text())
                def make_prompt(role, inputs, identity, canary=None):
                    return delivery.prompt(role, inputs, identity, canary, ids=ids,
                        execution_map=f"Python CLI: {sys.executable} -I -B <product>/username.py; existing tests: <product>/test_username.py. No dependencies.")
                remaining = 900 - (time.monotonic() - started)
                if remaining <= 0:
                    raise ValueError("Cumulative challenge budget exhausted")
                record["model_dispatches"] += 1
                record["active_stage"] = {"case": case, "role": role}
                delivery.write_record(output / "report.json", record)
                print(f"[{case}] {role}", flush=True)
                result = live.run_stage(codex, directory, inputs, identity, role, preferences,
                    min(240, remaining), make_prompt=make_prompt, criterion_ids=ids)
                entry["stages"].append(result)
                record.pop("active_stage")
            entry["matched"] = all(s["status"] == "OBSERVED" and s["report"]["verdict"] == expected
                                   for s in entry["stages"])
        threads = [s.get("thread_id") for c in record["cases"] for s in c["stages"]]
        if all(c["matched"] for c in record["cases"]) and len(set(threads)) == 4 and None not in threads:
            record["status"] = "OBSERVED"
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as exc:
        record["error"] = str(exc) or type(exc).__name__
    finally:
        record["elapsed_seconds"] = round(time.monotonic() - started, 6)
        delivery.write_record(output / "report.json", record)
    print(record["status"] + ": " + str(output / "report.json"))
    return 0 if record["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
