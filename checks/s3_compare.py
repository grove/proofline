#!/usr/bin/env python3
"""Predeclared local comparison; actual P2P, native model calls, private scoring."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as p
from checks import s2_live, s3_p2p_transport
from s0_live import oracle_runner

COHORTS = ("ordinary-agent", "agent-plus-review", "p2p", "proofline")
STAGE_SECONDS = 240
CASES = (("missing-validation", "baseline", False), ("correct-alternative", "alternative", False),
         ("green-tests-defect", "defective", False), ("false-scope-change", "correct", False),
         ("source-omission", "alternative", True))
SCRIPT = "skills/productivity/deliver-issue/scripts/p2p_delivery.py"


def contract(omitted=False):
    brief = (p.host.FIXTURES / "accepted-input.md").read_text()
    text = "# Acceptance contract: Username validation\n\nContract revision: v1\nSource: [Original request](source.md)\nParent: None\nPrerequisites: None\nIntended outcome: Complete the unchanged original username CLI promise.\n\n## Acceptance matrix\n\n"
    text += "| ID | Source | Requirement | Boundaries / counterexamples | Seam | Oracle | Planned evidence | Plan state |\n|---|---|---|---|---|---|---|---|\n"
    for line in brief.splitlines():
        if line.startswith("| U"):
            ident, requirement = [cell.strip() for cell in line.strip("|").split("|")]
            ident = "R" + ident[1:]
            if ident == "R2" and omitted:
                continue
            text += f"| {ident} | Original source | {requirement} | All original counterexamples remain binding. | Public CLI | Original source outcomes | Targeted tests and independent public observations | planned |\n"
    return text + "\n## Unresolved gaps\n\nNone.\n\n## Open questions\n\nNone.\n\n## Out of scope\n\nDependencies, external effects, and public interface changes.\n\n## Change notes\n\nSynthetic shared benchmark plan authorized for this local experiment; no historical approval is claimed.\n"


def seed(target, variant, trim=False):
    shutil.copytree(p.host.FIXTURES / "workers" / variant, target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if trim:
        script = target / "username.py"
        text = script.read_text()
        assert '"username": args.username' in text
        script.write_text(text.replace('"username": args.username', '"username": args.username.strip()'))
    (target / ".gitignore").write_text("/.p2p/\n__pycache__/\n*.pyc\n")
    p.host.git(target, "init", "--quiet", "--template=")
    p.freeze(target)


def outcome(accepted, correct, gap, timed_out=False, observed=False):
    if accepted:
        return "FALSE ACCEPTED" if gap or not correct else "ACCEPTED CORRECTLY"
    if timed_out:
        return "BUDGET EXHAUSTED"
    if correct and not gap and observed:
        return "FALSE BLOCKED"
    return "FAILED"


def source_gap_rejected(result):
    text = json.dumps([result.get("next_action"), result.get("controller_receipt", {}).get("stdout"),
        [stage.get("report") for stage in result.get("stages", [])]]).lower()
    return not result["accepted"] and any(word in text for word in ("source", "original", "contract", "agreement")) and any(
        word in text for word in ("omit", "missing", "incomplete")) and any(
        word in text for word in ("r2", "blank", "whitespace"))


def judgment_observed(stages):
    if not stages:
        return False
    last = stages[-1]
    report = last.get("report")
    planning_gap = (last.get("role") == "diagnosis" and
        isinstance(report, dict) and report.get("status") in {"BLOCKED", "ACTIONABLE"} and
        report.get("action") == "plan-acceptance")
    return last.get("status") == "OBSERVED" or (last.get("status") == "complete" and
        (last.get("role") in {"implementation", "review", "proof", "repair"} or planning_gap) and
        last.get("report_validation") == "accepted")


def ordinary(repo, source, brief, out, review, codex, preferences):
    started = time.monotonic()
    inputs = out / "implementation/inputs"
    inputs.mkdir(parents=True)
    (inputs / "source.md").write_text(source)
    (inputs / "accepted-input.md").write_text(brief)
    _, base = p.capture_base(repo, inputs / "product")
    boundary = out / "preflight"
    boundary.mkdir()
    observed = p.host.probe_boundary(codex, boundary, inputs, 15, inputs / "product/username.py")
    if observed["assessment"]["status"] != "OBSERVED":
        return {"accepted": False, "stages": [], "elapsed_seconds": time.monotonic() - started,
                "candidate": str(inputs / "product"), "error": "Native preflight unavailable"}
    for name in ("canary.py", "canary.json"):
        (inputs / name).unlink()
    ids = p.criterion_ids(brief)
    stages = []
    for role in (("implementer", "reviewer") if review else ("implementer",)):
        stage_dir = out / ("implementation" if role == "implementer" else role)
        stage_inputs = inputs
        if role != "implementer":
            stage_dir.mkdir()
            stage_inputs = stage_dir / "inputs"
            shutil.copytree(inputs, stage_inputs, symlinks=True)
        def prompt(role, inputs, identity, canary=None):
            if role == "reviewer":
                return p.prompt(role, inputs, identity, canary, ids=ids,
                    execution_map=f"Python {sys.executable} -B. Public entry point username.py; existing unittest checks are available.")
            return f"""Implement the unchanged original request in {inputs / 'product'}.
Original source: {inputs / 'source.md'}. Shared approved plan: {inputs / 'accepted-input.md'}.
The original source remains binding. Do not change the plan or claim completion of missing source promises. Report a material agreement gap instead of certifying an incomplete plan. Use your normal coding approach and useful checks. Python {sys.executable} -B; existing unittest checks are available. No dependencies or external effects. Only product is writable; do not commit.
Return the supplied schema: role implementer, binding {p.live.binding_for(identity)}, READY if the whole authorized task is complete, otherwise FAIL or NOT VERIFIED. List all criterion IDs {json.dumps(ids)} with observations; findings holds material blockers. Leave commands empty or cite actual host item IDs or EXACT full command strings from your tool events; paraphrased command citations invalidate the handoff. There is no separate checker in this coding stage.
"""
        result = p.live.run_stage(codex, stage_dir, stage_inputs, p.identities(stage_inputs, base), role,
            preferences, min(STAGE_SECONDS, 900 - (time.monotonic() - started)), make_prompt=prompt,
            criterion_ids=ids, target=stage_inputs / "product/username.py")
        stages.append(result)
        if result["status"] != "OBSERVED" or result["report"]["verdict"] != ("READY" if role == "implementer" else "PASS"):
            break
        if role == "implementer":
            p.freeze(inputs / "product")
    return {"accepted": len(stages) == (2 if review else 1) and all(s["status"] == "OBSERVED" and
        s["report"]["verdict"] in {"READY", "PASS"} for s in stages), "stages": stages,
        "elapsed_seconds": time.monotonic() - started, "candidate": str(inputs / "product")}


def p2p_run(repo, brief, source, out, controller, private, codex, *, stage_seconds=STAGE_SECONDS):
    started = time.monotonic()
    out.mkdir(parents=True)
    work = ".p2p/work/username/contract.md"
    directory = repo / Path(work).parent
    directory.mkdir(parents=True)
    (directory / "source-issue.md").write_text(source)
    (directory / "contract.md").write_text(brief.replace(
        "[Original request](source.md)", "[Original request](source-issue.md)"))
    base = p.host.git(repo, "rev-parse", "HEAD")
    p.host.git(repo, "branch", "delivery-target", base)
    blocked = [private, p.host.FIXTURES, Path(__file__).resolve(),
               p.host.ROOT / "tests/test_s3_compare.py", p.host.ROOT / "docs/S3-COMPARISON.md"]
    pending = [p.host.ROOT / ".proofline"]
    while pending:
        for entry in pending.pop().iterdir():
            if entry == out.parent:
                continue
            if out.parent.is_relative_to(entry):
                pending.append(entry)
            else:
                blocked.append(entry)
    scratch = out / "privacy-scratch"
    scratch.mkdir()
    profile = s3_p2p_transport.profile(scratch, blocked)
    canary = p.host.run_command([codex, "--no-daemon", "-c", "permissions.s3_p2p=" + p.host.toml(profile),
        "sandbox", "-P", "s3_p2p", "--include-managed-config", "-C", str(scratch), "--", sys.executable, "-I", "-B", "-c",
        "from pathlib import Path\nimport subprocess,sys\nfor i,value in enumerate(sys.argv[1:]):\n link=Path('key-link-'+str(i)); link.symlink_to(value)\n for target in (Path(value),link):\n  try: target.read_bytes()\n  except PermissionError: pass\n  else: raise AssertionError('private key readable')\n child=subprocess.run([sys.executable,'-I','-c','import pathlib,sys;pathlib.Path(sys.argv[1]).read_bytes()',value],capture_output=True)\n assert child.returncode!=0 and b'PermissionError' in child.stderr\nprint('private keys denied: absolute, symlink, subprocess')",
        str(private / "oracle-canary"), str(p.host.FIXTURES / "oracle.py")], out)
    if not p.host.succeeded(canary):
        return {"accepted": False, "candidate": str(repo), "elapsed_seconds": time.monotonic() - started,
                "model_dispatches": 0, "privacy": canary, "error": "Private oracle boundary unavailable", "stages": []}
    transport = out / "transport"
    transport.mkdir()
    launches = transport / "launches"
    launches.mkdir()
    executable = transport / "codex"
    executable.write_text(f"#!{sys.executable}\nimport sys\nsys.path.insert(0,{str(p.host.ROOT)!r})\n"
        "from checks.s3_p2p_transport import launch\n"
        f"launch({codex!r},sys.argv[1:],{[str(path.resolve()) for path in blocked]!r},{str(launches)!r})\n")
    executable.chmod(0o755)
    sys.path.insert(0, str(controller.parent))
    import p2p_delivery as d
    policy = d.autonomy.local('Deliver the shared preplanned contract without revising it.')['policy']
    policy['decisions'].remove('planning')
    policy['constraints'].append('Report material source gaps for upstream agreement; do not revise the shared plan or binding inputs.')
    policy['approval_source'] = 'User-authorized fixed-plan local S3 comparison.'
    mandate = out / 'mandate.json'
    p.write_record(mandate, policy)
    entry = out / "p2p_entry.py"
    entry.write_text(f"import sys\nfrom pathlib import Path\nsys.path.insert(0,{str(controller.parent)!r})\nimport p2p_delivery as d\n"
        f"stage_root=Path({str(controller.parents[2])!r})\n"
        "def package(name):\n path=(stage_root/name/'SKILL.md').resolve(strict=True)\n return {'path':str(path),'sha256':d.fs.digest(path.read_bytes())}\n"
        "d.installed_skill=package\nraise SystemExit(d.main())\n")
    receipt = p.host.run_command([sys.executable, "-B", str(entry),
        "--repo", str(repo), "run", work, "--comparison-base", base, "--destination", "delivery-target",
        "--authorize-local", "--mandate", str(mandate), "--max-dispatches", "12", "--max-seconds", "900",
        "--max-stage-seconds", str(stage_seconds), "--max-repairs", "1"], out, 915,
        env=os.environ | {"PATH": str(transport) + os.pathsep + os.environ.get("PATH", os.defpath)})
    local = d.local_directory(repo, work)
    runtime = d.execution_runtime(repo, work)
    state_path = local / "delivery.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    stages = []
    for attempt in state.get("attempts", []):
        folder = runtime / "attempts" / attempt["id"]
        if not (folder / "launch.json").exists():
            continue
        stages.append({"role": attempt["stage"], "usage": attempt.get("usage"),
            "receipt": json.loads((folder / "exit.json").read_text()) if (folder / "exit.json").exists() else {},
            "attempt_id": attempt["id"], "status": attempt["status"], "path": str(folder)})
        stages[-1]["report_validation"] = attempt.get("report_validation")
        if (folder / "report.json").exists():
            raw = (folder / "report.json").read_text()
            try:
                stages[-1]["report"] = json.loads(raw)
            except json.JSONDecodeError:
                stages[-1]["report"] = raw
    candidate = runtime / "workspace"
    return {"accepted": p.host.succeeded(receipt) and state.get("status") == "REVIEWED_AND_PROVEN",
            "candidate": str(candidate if candidate.exists() else repo), "stages": stages,
            "elapsed_seconds": time.monotonic() - started, "model_dispatches": len(stages),
            "controller_receipt": receipt, "privacy": canary, "state_path": str(state_path),
            "controller_status": state.get("status"), "skills": state.get("skills"),
            "runtime": str(runtime),
            "autonomy": state.get("autonomy"), "limits": state.get("limits"),
            "transport": "One native named permission profile: unchanged scratch writes/network denial, private-key read denials",
            "transport_sha256": p.host.sha256(Path(s3_p2p_transport.__file__).read_bytes()),
            "shim_sha256": p.host.sha256(executable.read_bytes()),
            "effective_launches": [{"path": str(path), "sha256": p.host.sha256(path.read_bytes())}
                                   for path in sorted(launches.glob("*.json"))],
            "instruction_lookup": "Unchanged current checkout packages; no host installation",
            "entry_sha256": p.host.sha256(entry.read_bytes())}


def run(s2_record, p2p_repo, output):
    output.mkdir(parents=True, exist_ok=False)
    operator = output / "operator"
    operator.mkdir()
    shutil.copyfile(__file__, operator / "runner.py")
    shutil.copyfile(s3_p2p_transport.__file__, operator / "p2p_transport.py")
    shutil.copyfile(p.live.__file__, operator / "codex_live.py")
    shutil.copyfile(p.__file__, operator / "proofline.py")
    (operator / "p2p.patch").write_bytes(p.git_bytes(p2p_repo, "diff", "--binary", "HEAD"))
    (operator / "proofline.patch").write_bytes(p.git_bytes(p.host.ROOT, "diff", "--binary", "HEAD"))
    (operator / "oracle-canary").write_text("operator-only")
    started = time.monotonic()
    audit_record = json.loads(s2_record.read_text())
    gate = s2_live.audit(Path(audit_record["record"]), operator / "s2-readback")
    if audit_record["status"] != "OBSERVED" or gate["status"] != "OBSERVED":
        raise ValueError("S2 live qualification must pass before any comparison")
    codex, preferences = p.host.find_codex(None), p.live.preferences()
    controller = p2p_repo / SCRIPT
    sys.path.insert(0, str(controller.parent))
    import p2p_delivery as current_p2p
    spec = importlib.util.spec_from_file_location("s3_private_oracle", p.host.FIXTURES / "oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    record = {"kind": "s3_four_way_comparison", "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING", "input_mode": "shared-preplanned", "raw_request_cohort": "not executed",
        "upstream_planning_cost": None, "human_attention_seconds": None, "monetary_cost": None,
        "model_preferences": preferences, "p2p_commit": p.git_bytes(p2p_repo, "rev-parse", "HEAD").decode().strip(),
        "p2p_patch_sha256": p.host.sha256((operator / "p2p.patch").read_bytes()),
        "proofline_commit": p.git_bytes(p.host.ROOT, "rev-parse", "HEAD").decode().strip(),
        "proofline_patch_sha256": p.host.sha256((operator / "proofline.patch").read_bytes()),
        "proofline_runner_sha256": p.host.sha256((operator / "proofline.py").read_bytes()),
        "codex_live_sha256": p.host.sha256((operator / "codex_live.py").read_bytes()),
        "limits": {"seconds": 900, "stage_seconds": STAGE_SECONDS, "p2p_dispatches": 12, "p2p_repairs": 1},
        "host": {"codex": p.host.run_command([codex, "--version"], operator)["stdout"].strip(),
                 "codex_sha256": p.host.sha256(Path(codex).read_bytes()), "python": sys.version},
        "p2p_instruction_packages": {stage: {"path": str(p2p_repo / "skills/productivity" / name / "SKILL.md"),
            "sha256": p.host.sha256((p2p_repo / "skills/productivity" / name / "SKILL.md").read_bytes())}
            for stage, name in current_p2p.STAGES.items()},
        "p2p_controller_sha256": p.host.sha256(controller.read_bytes()),
        "p2p_transport_sha256": p.host.sha256(Path(s3_p2p_transport.__file__).read_bytes()),
        "p2p_transport_policy": "One named native profile, scratch writes only, Git read-only, network off, private scoring paths denied",
        "oracle_sha256": p.host.sha256((p.host.FIXTURES / "oracle.py").read_bytes()),
        "runner_sha256": p.host.sha256(Path(__file__).read_bytes()),
        "oracle_criterion_mapping": {f"U{i}": f"R{i}" for i in range(1, 5)},
        "assignments": [], "sanity_controls": []}
    runs = output / "runs"
    runs.mkdir()
    for name, variant, gap in CASES:
        for cohort in COHORTS:
            record["assignments"].append({"case": name, "cohort": cohort, "variant": variant,
                "source_gap": gap, "path": str(runs / uuid.uuid4().hex), "outcome": "NOT EXECUTED"})
    p.write_record(operator / "manifest.json", record)
    source = (p.host.FIXTURES / "source.md").read_text()
    for variant, expected, trim in (("correct", True, False), ("alternative", True, False),
                                    ("defective", False, False), ("correct", False, True)):
        directory = operator / uuid.uuid4().hex
        directory.mkdir()
        inputs = directory / "inputs"
        inputs.mkdir()
        seed(inputs / "product", variant, trim)
        receipts = []
        observed = oracle.inspect_candidate(inputs / "product",
            runner=oracle_runner(codex, inputs, directory / "private", receipts))
        record["sanity_controls"].append({"variant": variant, "trim": trim,
            "expected": expected, "oracle": observed, "receipts": receipts})
        if observed["matches_expected"] != expected or any(x["status"] == "NOT_EXECUTED" for x in observed["observations"]):
            raise ValueError("Fixed oracle controls failed; no comparison models dispatched")
    record["setup_seconds"] = time.monotonic() - started
    for assignment in record["assignments"]:
        directory = Path(assignment["path"])
        directory.mkdir()
        repo = directory / "source"
        seed(repo, assignment["variant"], assignment["case"] == "false-scope-change")
        brief = contract(assignment["source_gap"])
        print(assignment["case"], assignment["cohort"], flush=True)
        p.write_record(operator / "report.json", record)
        began = time.monotonic()
        try:
            if assignment["cohort"] == "p2p":
                result = p2p_run(repo, brief, source, directory / "run", controller, operator, codex)
            elif assignment["cohort"] == "proofline":
                r = p.deliver(repo, source, brief, directory / "run", 900, STAGE_SECONDS, 120, dispatches=3,
                    execution_map=f"Python {sys.executable} -B. Public entry point username.py; existing unittest checks are available. This is a shared preplanned local benchmark task, not a historical P2P approval.")
                result = {**r, "accepted": r["status"] == "LOCAL ACCEPTED", "candidate": r.get("candidate_path", str(repo))}
            else:
                result = ordinary(repo, source, brief, directory / "run", assignment["cohort"] == "agent-plus-review", codex, preferences)
            assignment["delivery"] = result
            candidate = Path(result["candidate"])
            oracle_inputs = operator / uuid.uuid4().hex
            oracle_inputs.mkdir()
            shutil.copytree(candidate, oracle_inputs / "product", symlinks=True,
                            ignore=shutil.ignore_patterns(".git", ".p2p", "__pycache__", "*.pyc"))
            before = p.host.snapshot(oracle_inputs)
            receipts = []
            score = oracle.inspect_candidate(oracle_inputs / "product", runner=oracle_runner(codex, oracle_inputs, operator / "private", receipts))
            if p.host.snapshot(oracle_inputs) != before:
                raise ValueError("Independent scoring modified the candidate")
            assignment["oracle"] = score
            assignment["oracle_receipts"] = receipts
            stages = result.get("stages", [])
            timeout = result.get("status") == "BUDGET EXHAUSTED" or any(s.get("receipt", {}).get("timed_out") or s.get("receipt", {}).get("outcome") == "interrupted" for s in stages) or result.get("controller_receipt", {}).get("timed_out", False)
            observed = judgment_observed(stages)
            assignment["outcome"] = outcome(result["accepted"], score["matches_expected"], assignment["source_gap"], timeout, observed)
            assignment["matched_source_gap_rejection"] = assignment["source_gap"] and observed and source_gap_rejected(result)
        except (OSError, ValueError, RuntimeError) as exc:
            assignment["outcome"] = "FAILED"
            assignment["error"] = str(exc)
        assignment["elapsed_seconds"] = time.monotonic() - began
        p.write_record(operator / "report.json", record)
    record["elapsed_seconds"] = time.monotonic() - started
    record["status"] = "OBSERVED" if not any(a["cohort"] == "proofline" and a["outcome"] == "FALSE ACCEPTED" for a in record["assignments"]) else "TRUST GATE FAILED"
    p.write_record(operator / "report.json", record)
    return record


def p2p_followup(previous, p2p_repo, output):
    """Repeat only invalid P2P transports; preserve every original assignment."""
    original = json.loads(previous.read_text())
    if original["status"] not in {"OBSERVED", "TRUST GATE FAILED"}:
        raise ValueError("Original comparison must finish before transport follow-up")
    invalid = [a for a in original["assignments"] if a["cohort"] == "p2p"]
    if len(invalid) != 5 or any(a.get("delivery", {}).get("model_dispatches") != 0 or
        "generated artifacts cannot be binding inputs" not in a["delivery"]["controller_receipt"]["stdout"]
        for a in invalid):
        raise ValueError("Follow-up only covers the five recorded pre-admission source-location failures")
    if p.git_bytes(p2p_repo, "rev-parse", "HEAD").decode().strip() != original["p2p_commit"]:
        raise ValueError("P2P checkout changed since comparison predeclaration")
    if p.host.sha256((p.host.FIXTURES / "oracle.py").read_bytes()) != original["oracle_sha256"]:
        raise ValueError("Private oracle changed since comparison predeclaration")
    if p.live.preferences() != original["model_preferences"]:
        raise ValueError("Configured model preferences changed since predeclaration")
    output.mkdir(parents=True, exist_ok=False)
    operator = output / "operator"
    operator.mkdir()
    shutil.copyfile(__file__, operator / "runner.py")
    shutil.copyfile(s3_p2p_transport.__file__, operator / "p2p_transport.py")
    (operator / "oracle-canary").write_text("operator-only")
    spec = importlib.util.spec_from_file_location("s3_followup_oracle", p.host.FIXTURES / "oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    codex = p.host.find_codex(None)
    source = (p.host.FIXTURES / "source.md").read_text()
    captured = Path(original["assignments"][0]["path"]) / "run/implementation/inputs/source.md"
    if source != captured.read_text():
        raise ValueError("Original source changed since the comparison")
    record = {"kind": "s3_supported_p2p_transport_followup", "status": "RUNNING",
        "previous": str(previous), "previous_sha256": p.host.sha256(previous.read_bytes()),
        "reason": "Original imported source filename rejected before admission; source bytes unchanged",
        "runner_sha256": p.host.sha256(Path(__file__).read_bytes()),
        "assignments": [{"case": name, "cohort": "p2p", "variant": variant,
            "source_gap": gap, "path": str(output / "runs" / uuid.uuid4().hex),
            "outcome": "NOT EXECUTED"} for name, variant, gap in CASES]}
    p.write_record(operator / "manifest.json", record)
    started = time.monotonic()
    for assignment in record["assignments"]:
        directory = Path(assignment["path"])
        directory.mkdir(parents=True)
        repo = directory / "source"
        seed(repo, assignment["variant"], assignment["case"] == "false-scope-change")
        prior = next(a for a in invalid if a["case"] == assignment["case"])
        original_repo = Path(prior["path"]) / "source"
        if p.host.git(repo, "rev-parse", "HEAD^{tree}") != p.host.git(original_repo, "rev-parse", "HEAD^{tree}"):
            raise ValueError("Product seed changed since original assignment")
        if contract(assignment["source_gap"]) != (original_repo / ".p2p/work/username/contract.md").read_text():
            raise ValueError("Shared plan changed beyond supported relative source link")
        began = time.monotonic()
        print(assignment["case"], "supported-p2p", flush=True)
        p.write_record(operator / "report.json", record)
        try:
            result = p2p_run(repo, contract(assignment["source_gap"]), source,
                directory / "run", p2p_repo / SCRIPT, operator, codex,
                stage_seconds=original.get("limits", {}).get("stage_seconds", 180))
            assignment["delivery"] = result
            inputs = operator / uuid.uuid4().hex
            inputs.mkdir()
            shutil.copytree(Path(result["candidate"]), inputs / "product", symlinks=True,
                ignore=shutil.ignore_patterns(".git", ".p2p", "__pycache__", "*.pyc"))
            before = p.host.snapshot(inputs)
            receipts = []
            score = oracle.inspect_candidate(inputs / "product",
                runner=oracle_runner(codex, inputs, operator / "private", receipts))
            if before != p.host.snapshot(inputs):
                raise ValueError("Independent scoring modified the candidate")
            assignment.update(oracle=score, oracle_receipts=receipts)
            stages = result["stages"]
            timeout = result["controller_receipt"]["timed_out"] or any(
                s["receipt"].get("outcome") in {"interrupted", "timeout"} for s in stages)
            observed = judgment_observed(stages)
            assignment["outcome"] = outcome(result["accepted"], score["matches_expected"],
                assignment["source_gap"], timeout, observed)
            assignment["matched_source_gap_rejection"] = assignment["source_gap"] and observed and source_gap_rejected(result)
        except (OSError, ValueError, RuntimeError) as exc:
            assignment.update(outcome="FAILED", error=str(exc))
        assignment["elapsed_seconds"] = time.monotonic() - began
        p.write_record(operator / "report.json", record)
    record.update(status="OBSERVED", elapsed_seconds=time.monotonic() - started)
    p.write_record(operator / "report.json", record)
    return record


def summarize(records):
    """Known subtotals stay separate from unknown costs and quality eligibility."""
    result = {"cohorts": {}, "campaign_seconds": None, "known_campaign_seconds": 0,
        "unknown_campaign_durations": 0, "monetary_cost": None,
        "human_attention_seconds": None, "upstream_planning_cost": None}
    for record in records:
        seconds = record.get("elapsed_seconds")
        if seconds is None:
            result["unknown_campaign_durations"] += 1
        else:
            result["known_campaign_seconds"] += seconds
        for assignment in record["assignments"]:
            cohort = assignment["cohort"]
            row = result["cohorts"].setdefault(cohort, {"outcomes": {}, "dispatches": 0,
                "unknown_dispatch_counts": 0,
                "known_delivery_seconds": 0, "unknown_delivery_durations": 0,
                "qualified_satisfactory_deliveries": 0, "independently_satisfactory_deliveries": 0,
                "usage_known_stages": 0,
                "usage_unknown_stages": 0, "known_tokens": {}, "roles": {}})
            label = assignment["outcome"]
            row["outcomes"][label] = row["outcomes"].get(label, 0) + 1
            if label == "ACCEPTED CORRECTLY":
                row["independently_satisfactory_deliveries"] += 1
            if assignment.get("quality_eligible", record.get("quality_eligible", True)) and label == "ACCEPTED CORRECTLY":
                row["qualified_satisfactory_deliveries"] += 1
            delivery = assignment.get("delivery", {})
            stages = delivery.get("stages", [])
            if "delivery" not in assignment and label != "NOT EXECUTED":
                row["unknown_dispatch_counts"] += 1
            dispatches = delivery.get("model_dispatches", len(stages))
            if dispatches < len(stages):
                raise ValueError("Dispatch count cannot omit retained stages")
            row["dispatches"] += dispatches
            row["usage_unknown_stages"] += dispatches - len(stages)
            if label != "NOT EXECUTED":
                duration = delivery.get("elapsed_seconds")
                if duration is None:
                    row["unknown_delivery_durations"] += 1
                else:
                    row["known_delivery_seconds"] += duration
            for stage in stages:
                role = stage["role"]
                timing = row["roles"].setdefault(role, {"dispatches": 0,
                    "known_seconds": 0, "unknown_durations": 0})
                timing["dispatches"] += 1
                duration = stage.get("receipt", {}).get("elapsed_seconds")
                if duration is None:
                    timing["unknown_durations"] += 1
                else:
                    timing["known_seconds"] += duration
                usage = stage.get("usage")
                if not isinstance(usage, dict):
                    row["usage_unknown_stages"] += 1
                else:
                    row["usage_known_stages"] += 1
                    for key, value in usage.items():
                        if type(value) is int and value >= 0:
                            row["known_tokens"][key] = row["known_tokens"].get(key, 0) + value
    if not result["unknown_campaign_durations"]:
        result["campaign_seconds"] = result["known_campaign_seconds"]
    for row in result["cohorts"].values():
        row["total_dispatches"] = row["dispatches"] if not row["unknown_dispatch_counts"] else None
        all_count = row["independently_satisfactory_deliveries"]
        row["known_seconds_per_satisfactory_delivery"] = row["known_delivery_seconds"] / all_count if all_count else None
        row["seconds_per_satisfactory_delivery"] = (
            row["known_seconds_per_satisfactory_delivery"] if not row["unknown_delivery_durations"] else None)
        count = row["qualified_satisfactory_deliveries"]
        row["known_seconds_per_qualified_satisfactory_delivery"] = row["known_delivery_seconds"] / count if count else None
        row["seconds_per_qualified_satisfactory_delivery"] = (
            row["known_seconds_per_qualified_satisfactory_delivery"] if not row["unknown_delivery_durations"] else None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s2-record", type=Path)
    parser.add_argument("--p2p-followup", type=Path)
    parser.add_argument("--summary", nargs="+", type=Path)
    parser.add_argument("--p2p-repo", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if sum(bool(x) for x in (args.s2_record, args.p2p_followup, args.summary)) != 1:
        parser.error("Specify one S2 record, completed comparison for P2P follow-up, or summary inputs")
    if args.summary:
        args.output.mkdir(parents=True, exist_ok=False)
        record = summarize([json.loads(path.read_text()) for path in args.summary])
        record["inputs"] = [{"path": str(path.resolve()), "sha256": p.host.sha256(path.read_bytes())} for path in args.summary]
        p.write_record(args.output / "report.json", record)
        return 0
    if args.p2p_repo is None:
        parser.error("Native comparison requires --p2p-repo")
    record = (p2p_followup(args.p2p_followup.resolve(), args.p2p_repo.resolve(), args.output.resolve())
        if args.p2p_followup else run(args.s2_record.resolve(), args.p2p_repo.resolve(), args.output.resolve()))
    print(record["status"], args.output / "operator/report.json")
    return 0 if record["status"] == "OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
