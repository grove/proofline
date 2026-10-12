"""Experimental candidate-blind executable expectations; never an acceptance oracle."""
import json
from pathlib import Path
import shlex
import shutil
import sys

import codex_live as live
import host_probe as host

SCHEMA = live.object_schema({
    "role": {"type": "string", "enum": ["challenger"]},
    "binding": live.STRING,
    "verdict": {"type": "string", "enum": ["PLANNED", "NOT VERIFIED"]},
    "summary": live.STRING,
    "findings": {"type": "array", "items": live.STRING},
    "criteria": {"type": "array", "items": live.object_schema({
        "id": live.STRING, "source_quote": live.STRING,
        "domains": {"type": "array", "items": live.STRING}, "probe": live.STRING,
    })},
})


def encoded(report):
    return json.dumps(report, sort_keys=True).encode()


def validate_report(report, role, binding, commands, ids):
    if (not isinstance(report, dict) or set(report) != set(SCHEMA["properties"])
            or role != "challenger" or report["role"] != role or report["binding"] != binding
            or report["verdict"] not in {"PLANNED", "NOT VERIFIED"}
            or not isinstance(report["summary"], str) or not report["summary"].strip()
            or not isinstance(report["findings"], list)
            or any(not isinstance(x, str) or not x.strip() for x in report["findings"])
            or not isinstance(report["criteria"], list)):
        raise ValueError("Invalid blind challenge handoff")
    seen = set()
    for row in report["criteria"]:
        if (not isinstance(row, dict) or set(row) != {"id", "source_quote", "domains", "probe"}
                or row["id"] not in ids or row["id"] in seen
                or not isinstance(row["source_quote"], str) or not row["source_quote"].strip()
                or not isinstance(row["domains"], list) or not row["domains"]
                or any(not isinstance(x, str) or not x.strip() for x in row["domains"])
                or not isinstance(row["probe"], str) or not row["probe"].strip()):
            raise ValueError("Incomplete source-domain challenge")
        seen.add(row["id"])
        try:
            compile(row["probe"], row["id"] + ".py", "exec")
        except SyntaxError as exc:
            raise ValueError("Blind challenge is not executable Python: " + row["id"]) from exc
    if seen != set(ids) or report["verdict"] == "PLANNED" and report["findings"]:
        raise ValueError("Blind challenge handoff omits obligations or has unresolved gaps")


def prompt(role, inputs, identity, canary=None, *, ids, execution_map):
    return f"""You are an independent source-challenge author. The candidate, base implementation, implementation tests, peer judgments and private oracle are inaccessible. Do not attempt to access them. This is evidence design, not product verification or acceptance planning; do not change the promise.
Read the complete original source at {inputs / 'source.md'}, the indexed accepted input at {inputs / 'accepted-input.md'}, and any supplied binding context in inputs. The original source governs; omitted source obligations are INPUT NOT READY, not permission to narrow them.
Public interface and environment guidance (no expected answers):
{execution_map}
The product stub contains only this interface guidance, no implementation. Derive materially distinct valid domains, invalid inputs, preserved behavior and expected outcomes from the source. Do not assume restrictions from a familiar implementation, operator, parser or library. Where an operation is undefined, do not invent its result. State unresolved material standard/semantics coverage as NOT VERIFIED.
For each criterion {json.dumps(ids)}, quote its original source and return domain reasoning plus one self-contained standard-library Python probe as source text. It will receive the protected product directory as sys.argv[1], run with -I -B in disposable scratch, and have no network. Use public interfaces in the map. Assert independently determined expected and actual results; raise on mismatch, exit zero only after checks succeed. Bound subprocesses. Keep file/build/cache output in scratch. Do not use candidate tests as expectations. Code inspection can accompany executable observations for constraints. Missing observations cannot establish acceptance. Compile-check your probe source in scratch where useful, but no candidate is available to run it. PLANNED means only that executable expectations were designed, never that product behavior passed. Return NOT VERIFIED with precise gaps if meaningful probes cannot be designed.
Report role challenger, binding {live.binding_for(identity)}, verdict PLANNED or NOT VERIFIED. All criterion rows require id, source_quote, domains and probe. Do not return a product verdict.
{('First execute this exact standalone boundary canary: ' + canary) if canary else ''}
"""


def prepare(directory, original, execution_map):
    inputs = directory / "inputs"
    inputs.mkdir()
    for name in ("source.md", "accepted-input.md", "execution-map.md", "contract-context.json",
                 "execution-map.txt", "permissions.json"):
        if (original / name).exists():
            shutil.copy2(original / name, inputs / name)
    if (original / "intentline").exists():
        shutil.copytree(original / "intentline", inputs / "intentline")
    product = inputs / "product"
    product.mkdir()
    (product / "interface.txt").write_text(execution_map)
    host.git(product, "init", "--quiet", "--template=")
    host.git(product, "add", "--all")
    host.git(product, "commit", "--quiet", "-m", "Candidate-blind interface stub")
    return inputs


def attach(inputs, report):
    """Seal model-authored expectations outside product and bind them to later checks."""
    source = (inputs / "source.md").read_text()
    for row in report["criteria"]:
        if row["source_quote"] not in source:
            raise ValueError("Blind challenge cites text absent from the original source")
    (inputs / "challenges.json").write_bytes(encoded(report))
    directory = inputs / "challenges"
    directory.mkdir(exist_ok=True)
    for row in report["criteria"]:
        # IDs are validated against the caller's frozen criterion population.
        if not row["id"].isalnum() and not all(x.isalnum() for x in row["id"].split("-")):
            raise ValueError("Unsafe challenge criterion ID")
        (directory / (row["id"] + ".py")).write_text(row["probe"])


def commands(inputs):
    report = json.loads((inputs / "challenges.json").read_text())
    return {row["id"]: shlex.join([str(Path(sys.executable).resolve()), "-I", "-B",
            str(inputs / "challenges" / (row["id"] + ".py")), str(inputs / "product")])
            for row in report["criteria"]}


def validate_execution(report, observed, inputs):
    """A positive proof must execute each frozen probe and cannot waive its failure."""
    if not (inputs / "challenges.json").exists():
        return
    planned = json.loads((inputs / "challenges.json").read_text())
    for row in planned["criteria"]:
        path = inputs / "challenges" / (row["id"] + ".py")
        if path.read_text() != row["probe"]:
            raise ValueError("Sealed challenge bytes changed")
    if report["verdict"] != "PROVEN":
        return
    expected = commands(inputs)
    for row in report["criteria"]:
        matches = [key for key, item in observed.items() if expected[row["id"]] in
                   (item.get("command"), live.shell_payload(item.get("command", "")))]
        if not matches or matches[-1] not in row["commands"] or observed[matches[-1]]["exit_code"] != 0:
            raise ValueError("Positive proof lacks a successful cited frozen source challenge: " + row["id"])


def guidance(inputs):
    if not (inputs / "challenges.json").exists():
        return ""
    return f"""\nCandidate-blind source challenges were authored and sealed before implementation; inspect {inputs / 'challenges.json'} for source/domain reasoning. They are fallible evidence, not an oracle or amendment. Execute every frozen criterion probe as an exact standalone command before positive proof and cite it in that criterion, alongside your own candidate-specific challenges:
{json.dumps(commands(inputs), indent=2)}
Never edit or replace these probes to obtain a pass. Independently adjudicate a failure against the original source: a reproduced product mismatch is FAIL, an unsupported expectation or broken observation is NOT VERIFIED with the precise gap. Positive proof is forbidden while any frozen challenge fails or is unavailable. Successful finite probes alone do not establish full source coverage.\n"""
