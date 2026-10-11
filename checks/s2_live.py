#!/usr/bin/env python3
"""Challenge actual approved deliveries; altered controls are never approvals."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as delivery


def challenge_matches(case, scope, stages):
    terms = {"omitted-source-promise": ("r22", "admission") if scope == "child" else ("r2", "resume", "next action", "recovery action"),
             "admission-regression": ("admission", "implement-contract"),
             "diagnosis-regression": ("invalid_diagnosis_response", "diagnosis"),
             "incomplete-combined-parent": ("adaptive", "re-sizing", "resizing", "re-slic", "descendant", "r13", "r14", "r16")}[case]
    if len(stages) != 2 or not all(s["status"] == "OBSERVED" and
            s["report"]["verdict"] in {"FAIL", "NOT VERIFIED"} and
            any(term in " ".join(s["report"]["findings"]).lower() for term in terms) for s in stages):
        return False
    if case.endswith("regression"):
        criterion = "R9" if case == "admission-regression" else "R1"
        return all(s["report"]["verdict"] == "FAIL" and any(
            r["id"] == criterion and r["status"] == "VIOLATED" for r in s["report"]["criteria"]) for s in stages)
    if case == "omitted-source-promise":
        return all(s["report"]["verdict"] == "NOT VERIFIED" and any(
            f.startswith("INPUT NOT READY:") for f in s["report"]["findings"]) for s in stages)
    return True


def prepare_case(original, inputs, case):
    shutil.copytree(original, inputs, symlinks=True)
    context_path = inputs / "contract-context.json"
    context = json.loads(context_path.read_text())
    contract = inputs / "accepted-input.md"
    if case == "omitted-source-promise":
        # R9 allocates the original parent's R22 admission promise to this child.
        text = contract.read_text()
        omitted = "R9" if context["scope"] == "child" else "R2"
        if (omitted == "R9" and "| R9 | Parent v1:R22;" not in text) or (omitted == "R2" and "invalid diagnosis" not in text.lower()):
            raise ValueError("Omission control requires one of the retained real qualification contracts")
        contract.write_text("\n".join(line for line in text.splitlines() if not line.startswith(f"| {omitted} |")) + "\n")
        context["criterion_ids"].remove(omitted)
    elif case == "admission-regression":
        path = inputs / "product/skills/productivity/plan-acceptance/SKILL.md"
        text = path.read_text()
        if "/deliver-issue" not in text:
            raise ValueError("Admission control needs the original public delivery route")
        path.write_text(text.replace("/deliver-issue", "/implement-contract"))
        delivery.freeze(inputs / "product")
    elif case == "incomplete-combined-parent":
        parent = context["context_files"][0]["content"]
        contract.write_text(parent)
        matrix = parent.split("## Acceptance matrix\n", 1)[1].split("\n## ", 1)[0]
        context["criterion_ids"] = delivery.criterion_ids(matrix)
        context["scope"] = "combined-parent"
    elif case == "diagnosis-regression":
        path = inputs / "product/skills/productivity/deliver-issue/scripts/p2p_delivery.py"
        text = path.read_text()
        if "invalid_diagnosis_response" not in text:
            raise ValueError("Diagnosis control needs the completed correction")
        path.write_text(text.replace("invalid_diagnosis_response", "failed_launch"))
        delivery.freeze(inputs / "product")
    else:
        raise ValueError("Unknown live control")
    if case in {"omitted-source-promise", "incomplete-combined-parent"}:
        # Hide the old full contract in its receipt: these controls must inspect original source coverage.
        context["approval"] = {"kind": "read-only-judgment-control", "reference": "Explicit caller-authorized fault judgment; no delivery/effect authority"}
        context["contract_sha256"] = delivery.host.sha256(contract.read_bytes())
        if case == "incomplete-combined-parent":
            context["revision"] = "v1"
    context["control"] = {"kind": "deliberate-unapproved-fault-injection", "case": case}
    delivery.write_record(context_path, context)
    return context["criterion_ids"]


def request_for(metadata):
    return {"path": Path(metadata["contract_path"]), "contract_sha256": metadata["contract_sha256"],
            "source_sha256": metadata["source_sha256"], "approval_reference": metadata["approval"]["reference"],
            "approval_path": Path(metadata["approval"]["path"]), "approval_sha256": metadata["approval"]["sha256"]}


def qualify(positive_path, output, seconds=3000, stage_seconds=360, parent_path=None, preservation_manifest=None):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record = {"kind": "s2_live_qualification", "status": "NOT VERIFIED", "positive_record": str(positive_path),
              "harness_sha256": delivery.host.sha256(Path(__file__).read_bytes()),
              "cases": [], "input_controls": [], "model_dispatches": 0, "limits": {"seconds": seconds, "dispatches": 9}}
    try:
        positive = delivery.inspect_record(positive_path)
        record["positive_status"] = positive["status"]
        record["model_dispatches"] = positive["model_dispatches"]
        record["positive_elapsed_seconds"] = positive["elapsed_seconds"]
        context = positive.get("accepted_contract", {})
        if context.get("approval", {}).get("kind") != "inspected-p2p-approval":
            raise ValueError("This gate needs a real caller-inspected approved contract and original source")
        request = request_for(context)
        parent = delivery.inspect_record(parent_path) if parent_path else positive
        parent_context = parent.get("accepted_contract", {})
        if parent_context.get("scope") != "child" or parent_context.get("parent_completion") is not False:
            raise ValueError("The parent control needs the preserved real approved child and contribution")
        parent_request = request_for(parent_context)
        current, _, _ = delivery.contract_input.adopted_contract(**parent_request)
        if current != parent_context:
            raise ValueError("Parent/contribution bindings changed after the retained child run")
        record["parent_record"] = str(parent_path or positive_path)
        record["child_status"] = parent["status"]
        record["child_parent_completion"] = parent_context["parent_completion"]
        for name, changes in (("unapproved", {"approval_reference": None}),
                              ("stale-contract", {"contract_sha256": "0" * 64}),
                              ("stale-source", {"source_sha256": "0" * 64}),
                              ("stale-approval", {"approval_sha256": "0" * 64})):
            result = delivery.deliver(Path(positive["source_repository"]["path"]), "", "", output / name,
                                      contract_request={**request, **changes})
            record["input_controls"].append({"case": name, "status": result["status"],
                "dispatches": result["model_dispatches"], "next_action": result["next_action"]})
        for name in ("incomplete-matrix", "missing-source", "unmet-prerequisite", "changed-parent", "changed-plan"):
            selected = parent_context if name in {"changed-parent", "changed-plan"} else context
            selected_request = request_for(selected)
            paths = {selected_request["path"], selected_request["approval_path"]} | {
                Path(item["path"]) for item in selected["source_files"] + selected["context_files"]}
            root = next(p for p in selected_request["path"].parents if all(item.is_relative_to(p) for item in paths))
            if selected_request["path"].parent.parent.parent.name == ".p2p":
                root = selected_request["path"].parents[3]
            copied = output / (name + "-inputs")
            for path in paths:
                target = copied / path.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
            contract = copied / selected_request["path"].relative_to(root)
            if name == "incomplete-matrix":
                contract.write_text(contract.read_text().replace("| planned |", "| |", 1))
            elif name == "unmet-prerequisite":
                contract.write_text(re.sub(r"^Prerequisites: .*$", "Prerequisites: Issue 7 is closed", contract.read_text(), count=1, flags=re.M))
            else:
                index = 0 if name != "changed-plan" else 1
                row = selected["source_files"][0] if name == "missing-source" else selected["context_files"][index]
                target = copied / Path(row["path"]).relative_to(root)
                if name == "missing-source":
                    target.unlink()
                else:
                    target.write_text(target.read_text().replace("## Approved delivery plan", "## Changed plan") if name == "changed-plan"
                                      else target.read_text() + "\nChanged parent promise\n")
            result = delivery.deliver(Path(positive["source_repository"]["path"]), "", "", output / name,
                contract_request={**selected_request, "path": contract,
                                  "approval_path": copied / selected_request["approval_path"].relative_to(root)})
            record["input_controls"].append({"case": name, "status": result["status"],
                "dispatches": result["model_dispatches"], "next_action": result["next_action"]})
        if not positive.get("identities"):
            raise ValueError("Positive delivery has no frozen candidate; preserve its blocker before running judgment controls")
        original = Path(positive["candidate_path"]).parent
        before = delivery.host.snapshot(original)
        preserved = []
        if context["scope"] == "standalone":
            manifest = preservation_manifest or Path(positive["source_repository"]["path"]).parent / "preserved-originals.json"
            preserved = json.loads(manifest.read_text())
            if not preserved or not all(delivery.host.sha256(Path(row["path"]).read_bytes()) == row["sha256"] for row in preserved):
                raise ValueError("Original attempt/agreement preservation is unavailable or stale")
            record["original_preservation"] = {"manifest": str(manifest), "sha256": delivery.host.sha256(manifest.read_bytes()), "files": len(preserved)}
        parent_original = Path(parent["candidate_path"]).parent
        parent_before = delivery.host.snapshot(parent_original)
        if (parent_before["sha256"] != parent.get("snapshot") or
                delivery.identities(parent_original, parent["identities"]["base_commit"]) != parent["identities"]):
            raise ValueError("Retained child candidate or its binding inputs changed")
        record["parent_record_sha256"] = delivery.host.sha256((parent_path or positive_path).read_bytes())
        codex, preferences = delivery.host.find_codex(None), delivery.live.preferences()
        regression = "admission-regression" if context["scope"] == "child" else "diagnosis-regression"
        for case in ("omitted-source-promise", regression, "incomplete-combined-parent"):
            entry = {"case": case, "stages": [], "matched": False}
            record["cases"].append(entry)
            for role in ("reviewer", "prover"):
                directory = output / (case + "-" + role)
                directory.mkdir()
                inputs = directory / "inputs"
                retained = parent if case == "incomplete-combined-parent" else positive
                case_original = Path(retained["candidate_path"]).parent
                ids = prepare_case(case_original, inputs, case)
                identity = delivery.identities(inputs, retained["identities"]["base_commit"])
                target = next((p for p in (inputs / "product").rglob("*")
                               if p.is_file() and ".git" not in p.relative_to(inputs / "product").parts), None)
                if target is None:
                    raise ValueError("Live controls need an existing product file for the native boundary canary")
                def make_prompt(role, inputs, identity, canary=None):
                    return delivery.prompt(role, inputs, identity, canary, ids=ids,
                        execution_map=f"Python: {sys.executable} -B. Multi-module controller entry points need their script directory on sys.path; use -B directly or a scratch driver importing protected modules explicitly. -I removes that import path. Developer Git PATH/GIT_EXEC_PATH and disabled global/system config are supplied. Tests may add /opt/homebrew/opt/python@3.14/libexec/bin and /opt/homebrew/bin to PATH. For fixtures requiring installed skills, make scratch/fixture-codex/skills a symlink to this exact product/skills/productivity and use that scratch CODEX_HOME only for test subprocesses. This is a deliberately altered judgment control, not an approved delivery. Inspect the public P2P instruction and scenario interfaces and controller seams. After a decisive material blocker, stop broad checks and return the structured rejection; unobserved criteria remain NOT VERIFIED. An import/setup failure alone is not a product defect. No external effects, host installation or source-tree writes. Old reports in context are provenance and cannot replace fresh observations.")
                remaining = seconds - positive["elapsed_seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise ValueError("Cumulative qualification budget exhausted; do not reset the retained episode")
                record["model_dispatches"] += 1
                record["active_stage"] = {"case": case, "role": role}
                delivery.write_record(output / "report.json", record)
                print(f"[{case}] {role}", flush=True)
                result = delivery.live.run_stage(codex, directory, inputs, identity, role, preferences,
                    min(stage_seconds, remaining), make_prompt=make_prompt, criterion_ids=ids, target=target)
                entry["stages"].append(result)
                record.pop("active_stage")
            # Rejection must name the intended missing/changed obligation, not only an authority label.
            entry["matched"] = challenge_matches(case, context["scope"], entry["stages"])
        threads = [s.get("thread_id") for s in positive["stages"]] + [
            s.get("thread_id") for c in record["cases"] for s in c["stages"]]
        if (positive["status"] == "LOCAL ACCEPTED" and context["parent_completion"] is False and
                all(c["matched"] for c in record["cases"]) and
                all(c["status"] == "INPUT NOT READY" and c["dispatches"] == 0 for c in record["input_controls"]) and
                len(threads) == len(set(threads)) == 9 and
                None not in threads and delivery.host.snapshot(original) == before and
                delivery.host.snapshot(parent_original) == parent_before and
                all(delivery.host.sha256(Path(row["path"]).read_bytes()) == row["sha256"] for row in preserved)):
            record["status"] = "OBSERVED"
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as exc:
        record["error"] = str(exc) or type(exc).__name__
    finally:
        record["elapsed_seconds"] = round(time.monotonic() - started + record.get("positive_elapsed_seconds", 0), 6)
        delivery.write_record(output / "report.json", record)
    return record


def audit(path, output):
    """Re-score unchanged native observations after a mechanical matcher correction."""
    output.mkdir(parents=True, exist_ok=False)
    result = {"kind": "s2_live_audit", "status": "NOT VERIFIED", "record": str(path),
              "record_sha256": delivery.host.sha256(path.read_bytes()),
              "harness_sha256": delivery.host.sha256(Path(__file__).read_bytes())}
    try:
        record = json.loads(path.read_text())
        if record.get("kind") != "s2_live_qualification" or record.get("active_stage"):
            raise ValueError("Audit needs a completed qualification record")
        positive = delivery.inspect_record(Path(record["positive_record"]))
        if positive["status"] != "LOCAL ACCEPTED":
            raise ValueError("Original positive delivery is no longer accepted")
        parent_path = Path(record["parent_record"])
        if delivery.host.sha256(parent_path.read_bytes()) != record["parent_record_sha256"]:
            raise ValueError("Retained child record changed")
        parent = delivery.inspect_record(parent_path)
        current, _, _ = delivery.contract_input.adopted_contract(**request_for(parent["accepted_contract"]))
        if current != parent["accepted_contract"] or current["scope"] != "child":
            raise ValueError("Original child agreement or contribution changed")
        parent_inputs = Path(parent["candidate_path"]).parent
        if (delivery.host.snapshot(parent_inputs)["sha256"] != parent["snapshot"] or
                delivery.identities(parent_inputs, parent["identities"]["base_commit"]) != parent["identities"] or
                parent["accepted_contract"]["parent_completion"] is not False):
            raise ValueError("Retained child candidate changed or claims parent completion")
        metadata = positive["accepted_contract"]
        if metadata["approval"]["kind"] != "inspected-p2p-approval":
            raise ValueError("Audit needs the actual inspected P2P approval")
        threads = [delivery.live.read_events(s["receipt"])["thread_id"] for s in positive["stages"]]
        expected_cases = {"omitted-source-promise", "admission-regression" if metadata["scope"] == "child" else "diagnosis-regression", "incomplete-combined-parent"}
        if len(record["cases"]) != 3 or {c["case"] for c in record["cases"]} != expected_cases:
            raise ValueError("Required control cases are missing")
        matches = []
        for case in record["cases"]:
            retained = parent if case["case"] == "incomplete-combined-parent" else positive
            if [s["role"] for s in case["stages"]] != ["reviewer", "prover"]:
                raise ValueError("Required independent control roles are missing")
            for stage in case["stages"]:
                inputs = Path(stage["identities"]["candidate_path"]).parent
                if (stage["status"] != "OBSERVED" or stage["boundary"]["status"] != "OBSERVED" or
                        any(stage["identities"][key] != retained["identities"][key] for key in ("source_sha256", "base_commit")) or
                        delivery.host.snapshot(inputs)["sha256"] != stage["snapshot"] or
                        delivery.identities(inputs, stage["identities"]["base_commit"]) != stage["identities"]):
                    raise ValueError("Control observation, boundary or candidate is unavailable or changed")
                native = delivery.live.read_events(stage["receipt"])
                delivery.live.resolve_command_refs(native["report"], native["commands"])
                context = json.loads((inputs / "contract-context.json").read_text())
                if context["control"] != {"kind": "deliberate-unapproved-fault-injection", "case": case["case"]}:
                    raise ValueError("Control source or purpose differs from the declared case")
                ids = context["criterion_ids"]
                delivery.live.validate_report(native["report"], stage["role"], stage["binding"], native["commands"], ids)
                if native["report"] != stage["report"] or stage["binding"] != delivery.live.binding_for(stage["identities"]):
                    raise ValueError("Saved control verdict differs from native evidence")
                threads.append(native["thread_id"])
            matches.append({"case": case["case"], "matched": challenge_matches(case["case"], metadata["scope"], case["stages"])})
        expected_inputs = {"unapproved", "stale-contract", "stale-source", "stale-approval", "incomplete-matrix", "missing-source", "unmet-prerequisite", "changed-parent", "changed-plan"}
        if len(record["input_controls"]) != 9 or {c["case"] for c in record["input_controls"]} != expected_inputs:
            raise ValueError("Required readiness controls are missing")
        for control in record["input_controls"]:
            saved = delivery.inspect_record(path.parent / control["case"] / "report.json")
            if saved["status"] != "INPUT NOT READY" or saved["model_dispatches"] != 0:
                raise ValueError("Readiness control did not reject before dispatch")
        if record.get("original_preservation"):
            manifest = Path(record["original_preservation"]["manifest"])
            if delivery.host.sha256(manifest.read_bytes()) != record["original_preservation"]["sha256"] or not all(
                    delivery.host.sha256(Path(row["path"]).read_bytes()) == row["sha256"] for row in json.loads(manifest.read_text())):
                raise ValueError("Original attempts or preservation manifest changed")
        result["cases"] = matches
        if all(c["matched"] for c in matches) and len(threads) == len(set(threads)) == 9 and metadata["parent_completion"] is False:
            result["status"] = "OBSERVED"
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        result["error"] = str(exc)
    delivery.write_record(output / "report.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positive_record", type=Path)
    parser.add_argument("--audit", action="store_true", help="Revalidate and score a completed qualification record; zero model calls")
    parser.add_argument("--parent-record", type=Path, help="Retained actual child record for parent/contribution controls")
    parser.add_argument("--preservation-manifest", type=Path, help="Original attempt/agreement before hashes for the diagnosis replay")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=delivery.positive_seconds, default=3000)
    parser.add_argument("--stage-seconds", type=delivery.positive_seconds, default=360)
    args = parser.parse_args()
    output = (args.output or delivery.host.ROOT / ".proofline/s2-live" / uuid.uuid4().hex).resolve()
    record = audit(args.positive_record.resolve(), output) if args.audit else qualify(args.positive_record.resolve(), output, args.seconds, args.stage_seconds,
                     args.parent_record.resolve() if args.parent_record else None,
                     args.preservation_manifest.resolve() if args.preservation_manifest else None)
    print(record["status"] + ": " + str(output / "report.json"))
    return 0 if record["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
