"""One-shot matched issue #16 study. No retries, resumption or oracle repair.

Offline: python -B -m evaluation.matched.study controls|report
Native host: python -B -m evaluation.matched.study qualify|execute
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import sys
import time

import proofline as p
from checks import intentline_advisory, local_run
from evaluation.matched import corpus, grader, report

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STORE = ROOT / ".proofline/issue16-matched-v2-20261013"
PRODUCER = Path("/Users/grove/projects/intentline")
CODEX = "/opt/homebrew/bin/codex"
SCHEMA = p.live.object_schema({"completed": {"type": "boolean"}, "summary": p.live.STRING})


def now():
    return datetime.now(timezone.utc).isoformat()


def read_protocol():
    return json.loads((HERE / "protocol.json").read_text())


def ledger():
    spec = read_protocol()
    return [{"sequence": i * 4 + j + 1, "task": task, "arm": arm, "status": "NOT_EXECUTED",
             "model_dispatches": 0, "usage": None, "workflow_seconds": None}
            for i, task in enumerate(spec["tasks"]) for j, arm in enumerate(spec["order"][i])]


def producer_files():
    paths = [path for name in ("intentline", "schema", "docs", "skills/intentline-plan")
             for path in (PRODUCER / name).rglob("*")
             if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".json", ".md")]
    return {str(path.relative_to(PRODUCER)): path for path in paths}


def identities():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if p.host.sha256((ROOT / name).read_bytes()) != expected:
            raise ValueError("Frozen study input drift: " + name)
    paths = {str(path.relative_to(ROOT)): path for folder in (ROOT / "checks", HERE, ROOT / "evaluation/v1")
             for path in folder.rglob("*") if path.is_file() and path.suffix in (".py", ".json", ".md")}
    paths.update({"proofline.py": ROOT / "proofline.py", "evaluation/__init__.py": ROOT / "evaluation/__init__.py",
                  "codex": Path(CODEX), "python": Path(sys.executable).resolve()})
    paths.update({"intentline/" + name: path for name, path in producer_files().items()})
    return {name: p.host.sha256(path.read_bytes()) for name, path in paths.items()}


def selected_checks(task):
    python = str(Path(sys.executable).resolve())
    payload, expected = corpus.CASES[task][0][1:]
    return [[python, "-B", "-c", f"from app import process; assert process({payload!r}) == {expected!r}"],
            [python, "-B", "-m", "unittest", "discover", "-s", "tests"]]


def boundary(inputs, directory, *, worker=False):
    directory.mkdir(parents=True, exist_ok=False)
    with p.host.boundary_fixture(directory, inputs, target=inputs / "product/app.py",
            denied_reads={"matched_oracle": str(HERE / "corpus.py"), "grader": str(HERE / "grader.py"),
                          "study_results": str(STORE / "results.json"), "enclosing_repository": str(ROOT / "README.md"),
                          "sibling": str(STORE / "qualification/inputs/product/app.py")}) as (spec, before, private_before, _):
        if worker:
            command = p.live.command(CODEX, inputs, directory / "scratch", directory / "private", read_protocol()["model"], implementer=True)
            profile = next(value for value in command if value.startswith("permissions.proofline="))
            argv = [CODEX, "--no-daemon", "-c", profile, "sandbox", "--permission-profile", "proofline",
                    "--include-managed-config", "--cd", str(directory / "scratch"), "--",
                    str(Path(sys.executable).resolve()), "-I", "-B", str(inputs / "canary.py"), str(inputs / "canary.json")]
        else:
            argv = p.host.sandbox_argv(CODEX, inputs, directory / "scratch", directory / "private")
        receipt = p.host.run_command(argv, directory / "scratch", 15)
    if worker:
        observation = json.loads(receipt["stdout"]) if p.host.succeeded(receipt) else {}
        writes = dict.fromkeys(spec["writes"], "denied")
        writes["candidate"] = "allowed"
        after = p.host.snapshot(inputs)
        unchanged = all(entry == after["entries"][i] for i, entry in enumerate(before["entries"]) if entry["path"] != "product/app.py")
        valid = (observation.get("nonce") == spec["nonce"] and observation.get("writes") == writes
                 and observation.get("reads") == dict.fromkeys(spec["reads"], "denied")
                 and observation.get("mode_change") == "allowed" and observation.get("scratch") is True
                 and spec["port"] is not None and observation.get("network") == "denied" and unchanged
                 and private_before == p.host.snapshot(directory / "private"))
        assessment = {"status": "OBSERVED" if valid else "NOT VERIFIED", "observations": observation}
    else:
        assessment = p.host.assess_canary(receipt, spec, before == p.host.snapshot(inputs) and private_before == p.host.snapshot(directory / "private"))
    result = {"assessment": assessment, "receipt": receipt}
    p.write_record(directory / "boundary.json", result)
    if assessment["status"] != "OBSERVED":
        raise ValueError("Unqualified native boundary; no dispatch")
    for name in ("canary.py", "canary.json"):
        (inputs / name).unlink()
    return result


def initialize(task, directory):
    product = corpus.seed(task, directory)
    p.host.git(product, "init", "--quiet", "--template=")
    p.host.git(product, "add", "--all")
    p.host.git(product, "commit", "--quiet", "-m", "Matched v2 original seed")
    return product


def verify():
    manifest = json.loads((STORE / "manifest.json").read_text())
    if manifest["identities"] != identities():
        raise ValueError("Frozen code/tool/runtime drift; stop")
    return manifest


def qualify():
    STORE.mkdir(mode=0o700, parents=True, exist_ok=False)
    started = time.monotonic()
    rows = ledger()
    result = {"study": read_protocol()["study_id"], "status": "PREPARING", "assignments": rows, "declared_at": now()}
    p.write_record(STORE / "results.json", result)
    try:
        spec = read_protocol()
        if (platform.system(), platform.machine(), platform.mac_ver()[0], platform.python_version()) != (
                spec["host"]["system"], spec["host"]["machine"], spec["host"]["macos"], spec["host"]["python"]):
            raise ValueError("Declared host/version unavailable")
        version = p.host.run_command([CODEX, "--version"], STORE)
        if not p.host.succeeded(version) or version["stdout"].strip() != spec["host"]["codex"]:
            raise ValueError("Declared native CLI unavailable")
        if p.host.auth_status(p.host.run_command([CODEX, "login", "status"], STORE)) != "authenticated":
            raise ValueError("Existing model authentication unavailable")
        cache = json.loads((Path.home() / ".codex/models_cache.json").read_text())
        models = [m for m in cache["models"] if m["slug"] == spec["model"]["model"]]
        if not models or spec["model"]["model_reasoning_effort"] not in [r["effort"] for r in models[0]["supported_reasoning_levels"]]:
            raise ValueError("Declared model/reasoning unavailable")
        manifest = {"declared_at": now(), "source_revision": p.host.git(ROOT, "rev-parse", "HEAD"), "identities": identities(),
                    "protocol": spec, "model_cache_at": cache.get("fetched_at"), "model_capacity": "unknown until first dispatch",
                    "producer_revision": p.host.git(PRODUCER, "rev-parse", "HEAD"), "version_receipt": version, "assignments": []}
        if p.host.git(PRODUCER, "status", "--porcelain"):
            raise ValueError("Intentline producer checkout is dirty")
        for row in rows:
            inputs = STORE / "assignments" / f'{row["sequence"]:02d}-{row["task"]}-{row["arm"]}' / "inputs"
            product = initialize(row["task"], inputs)
            row.update(inputs=str(inputs), source_sha256=p.host.sha256((inputs / "source.md").read_bytes()),
                       base_tree=p.host.git(product, "rev-parse", "HEAD^{tree}"))
            manifest["assignments"].append({"sequence": row["sequence"], "source_sha256": row["source_sha256"],
                                            "base_tree": row["base_tree"], "seed_snapshot": p.host.snapshot(product),
                                            "checks": selected_checks(row["task"])})
        p.write_record(STORE / "manifest.json", manifest)
        probe = STORE / "qualification"
        inputs = probe / "inputs"
        initialize(spec["tasks"][0], inputs)
        boundary(inputs, probe / "worker", worker=True)
        boundary(inputs, probe / "grader")
        controls = grader.controls(trusted=False, directory=probe / "controls")
        p.write_record(STORE / "controls.json", controls)
        if not controls["all_12_matched"]:
            raise ValueError("Invalid native controls; no dispatch")
        manifest["qualification_seconds"] = time.monotonic() - started
        p.write_record(STORE / "manifest.json", manifest)
        result["status"] = "QUALIFIED_NOT_DISPATCHED"
    except Exception as error:
        result.update(status="STOPPED", blocker=str(error))
        raise
    finally:
        result["preparation_seconds"] = time.monotonic() - started
        p.write_record(STORE / "results.json", result)


def prompt(row, inputs, scratch, remaining):
    text = (f"Implement the complete original request {inputs / 'source.md'} in {inputs / 'product'}. "
            "Use your ordinary autonomous coding approach, useful tests and debugging. Only product and scratch are writable; do not commit. "
            "Network, external tools, sibling assignments and evaluator inputs are unavailable. Original source and Git metadata are protected. "
            f"Python is {Path(sys.executable).resolve()}. Cwd/TMPDIR is {scratch}. "
            f"Common public check guidance: {inputs / 'checks.json'}. These checks are not exhaustive. "
            f"You have at most {remaining:.1f} seconds TOTAL, including any planning, export, coding, self-checks and final response. "
            "Return completed=true when the entire original task is implemented, otherwise false, with a short summary.\n")
    if row["arm"] in ("intentline", "combined"):
        cli = f"{Path(sys.executable).resolve()} -B {inputs / 'intentline_cli.py'}"
        text += (f"Before implementation, perform ONE advisory planning pass yourself using {inputs / 'tool/skills/intentline-plan/SKILL.md'}. "
                 "The skill applies to the planning phase; finish that phase then implement this same original task in this same turn. "
                 "No audit, adoption, separate planner, reviewer, or user approval. CLI examples use this frozen offline CLI instead of -m intentline: "
                 f"{cli}. Use prepare --source {inputs / 'source.md'} --root {inputs} --out {scratch / 'plan'} --json. "
                 "Read frozen schema/identity and authority documents. Author source-grounded draft.json, propose, check and render per the skill. "
                 f"After structurally valid planning you are explicitly authorized to export --work {scratch / 'plan'} --format json --out {scratch / 'export'} --json. "
                 "The draft is advisory; an evidence gap never prevents implementation. Preserve all original obligations. "
                 "Do not claim generated R labels, plans or passing tests certify completeness. Planning/export consume the same total budget.\n")
    if row["arm"] in ("proofline", "combined"):
        text += "After your coding handoff the host will use actual Proofline check-only against those selected commands and display feedback. No correction turn is available.\n"
    return text


def execute():
    manifest = verify()
    result = json.loads((STORE / "results.json").read_text())
    if result["status"] != "QUALIFIED_NOT_DISPATCHED":
        raise ValueError("No retry or resume; campaign already used or unavailable")
    result.update(status="RUNNING", started_at=now())
    p.write_record(STORE / "results.json", result)
    try:
        for row, frozen in zip(result["assignments"], manifest["assignments"], strict=True):
            verify()
            started = time.monotonic()
            inputs = Path(row["inputs"])
            product, folder = inputs / "product", inputs.parent
            if p.host.snapshot(product) != frozen["seed_snapshot"] or p.host.sha256((inputs / "source.md").read_bytes()) != frozen["source_sha256"]:
                raise ValueError("Starting candidate/source drift")
            boundary(inputs, folder / "boundary", worker=True)
            # The coding canary changed its target; restore only its declared disposable change before dispatch.
            (product / "app.py").write_text(corpus.v1.APP_STUB)
            (product / "app.py").chmod(0o644)
            (inputs / "checks.json").write_text(json.dumps(frozen["checks"]))
            (inputs / "response.schema.json").write_text(json.dumps(SCHEMA))
            if row["arm"] in ("intentline", "combined"):
                for name, source in producer_files().items():
                    target = inputs / "tool" / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                (inputs / "intentline_cli.py").write_text("import sys,runpy\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).parent/'tool'))\nrunpy.run_module('intentline',run_name='__main__')\n")
            protected = {str(path.relative_to(inputs)): p.host.sha256(path.read_bytes()) for path in inputs.rglob("*")
                         if path.is_file() and product not in path.parents}
            git_before = p.host.snapshot(product / ".git")
            scratch, private = folder / "scratch", folder / "private"
            scratch.mkdir(); private.mkdir()
            remaining = 600 - (time.monotonic() - started)
            if remaining <= 0:
                raise ValueError("Agent allocation exhausted")
            argv = p.live.command(CODEX, inputs, scratch, private, manifest["protocol"]["model"], implementer=True)
            row.update(status="DISPATCHED", model_dispatches=1, started_at=now())
            p.write_record(STORE / "results.json", result)
            print("DISPATCH", row["sequence"], row["task"], row["arm"], flush=True)
            receipt = p.live.launch(argv, prompt(row, inputs, scratch, remaining), private, remaining)
            row.update(receipt=receipt, agent_completed=False, handoff=False, native_available=False)
            try:
                native = p.live.read_events(receipt)
                response = native["report"]
                if set(response) != {"completed", "summary"} or type(response["completed"]) is not bool or not isinstance(response["summary"], str):
                    raise ValueError("Invalid completion response")
                row.update(native_available=True, agent_completed=response["completed"], handoff=response["completed"],
                           usage=native["usage"], thread_id=native["thread_id"], tool_executions=len(native["commands"]), response=response)
                events = [json.loads(line) for line in Path(receipt["events_path"]).read_bytes().splitlines()]
                row["tool_executions"] = sum(e["type"] == "item.completed" and e["item"]["type"] in ("command_execution", "file_change") for e in events)
            except (OSError, ValueError, TypeError, KeyError) as error:
                row["native_error"] = str(error)
            p.live.reconcile_worker(private)
            if (git_before != p.host.snapshot(product / ".git") or any(p.host.sha256((inputs / n).read_bytes()) != h for n,h in protected.items())):
                raise ValueError("Protected source/runtime/Git changed")
            row["candidate_commit"], row["candidate_tree"] = p.freeze(product)
            intervention_available = True
            if row["arm"] in ("intentline", "combined"):
                try:
                    row["plan_identity"] = intentline_advisory.load_export(scratch / "export", (inputs / "source.md").read_text(), frozen["checks"])["metadata"]
                except (OSError, ValueError) as error:
                    row["plan_error"] = str(error)
                    intervention_available = False
            if row["arm"] in ("proofline", "combined") and intervention_available:
                package = intentline_advisory.load_export(scratch / "export", (inputs / "source.md").read_text(), frozen["checks"]) if row["arm"] == "combined" else None
                record = local_run.check(product, (inputs / "source.md").read_text(), frozen["checks"], folder / "check",
                                 seconds=max(0.001, 900 - (time.monotonic() - started)), check_seconds=30, intentline_package=package)
                status = local_run.inspect(folder / "check/report.json")
                row.update(check_status=status["status"], feedback=record["feedback"], check_elapsed_seconds=record["elapsed_seconds"],
                           check_model_dispatches=record["model_dispatches"], promise_evidence=record.get("promise_evidence"))
                row["handoff"] = row["agent_completed"] and status["status"] == "CHECKS PASSED"
                intervention_available = status["status"] in ("CHECKS PASSED", "CHECKS FAILED")
                print("FEEDBACK", row["sequence"], json.dumps(record["feedback"], ensure_ascii=False), flush=True)
            row["workflow_seconds"] = time.monotonic() - started
            grade = grader.grade(product, row["task"], folder / "evaluation", seconds=120)
            row.update(grade=grade, finished_at=now(), operator_candidate_edits=0, extra_worker_messages=0)
            row["status"] = report.outcome(row["handoff"], grade["correct"], row["native_available"] and intervention_available)
            p.write_record(folder / "result.json", row)
            p.write_record(STORE / "results.json", result)
            print("RESULT", row["sequence"], row["status"], round(row["workflow_seconds"], 2), flush=True)
            verify()
            if row["workflow_seconds"] > 900 or not row["native_available"] or not intervention_available or not grade["available"]:
                raise ValueError("Model/intervention/grader unavailable or budget drift; retain missing runs, stop")
        result["status"] = "COMPLETE"
    except Exception as error:
        result.update(status="STOPPED", blocker=str(error))
        for assigned in result["assignments"]:
            if assigned["status"] == "DISPATCHED":
                assigned.update(status="UNAVAILABLE", unavailable_reason=str(error),
                                workflow_seconds=time.monotonic() - started)
        raise
    finally:
        result.update(finished_at=now(), metrics=report.summarize(result["assignments"]))
        p.write_record(STORE / "results.json", result)


def main():
    action = sys.argv[1]
    if action == "controls":
        result = grader.controls()
        print(json.dumps({"all_12_matched": result["all_12_matched"], "model_dispatches": 0,
                          "controls": [{"task": r["task"], "variant": r["variant"], "matched": r["matched"]} for r in result["controls"]]}, indent=2))
        return 0 if result["all_12_matched"] else 2
    if action == "report":
        print(json.dumps(report.summarize(ledger()), indent=2))
        return 0
    {"qualify": qualify, "execute": execute}[action]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
