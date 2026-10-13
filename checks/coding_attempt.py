"""One autonomous Codex coding attempt; no model review, proof, or acceptance."""

import json
from pathlib import Path
import time

from checks import codex_live as live, host_probe as host
from checks.candidate_snapshot import capture_base, freeze
from checks.native_checks import write_record


def run(repo, source, guidance, output, codex, preferences, seconds, execution_map=""):
    """Return a coding handoff, not a verdict that the user promise is fulfilled."""
    started = time.monotonic()
    inputs = output / "implementation" / "inputs"
    inputs.mkdir(parents=True)
    (inputs / "source.md").write_text(source)
    (inputs / "guidance.md").write_text(guidance)
    _, base = capture_base(repo, inputs / "product")
    boundary = output / "preflight"
    boundary.mkdir()
    target = next((path for path in (inputs / "product").rglob("*")
        if path.is_file() and ".git" not in path.relative_to(inputs / "product").parts), None)
    if target is None:
        raise ValueError("A regular tracked product file is required")
    observed = host.probe_boundary(codex, boundary, inputs, 15, target)
    write_record(boundary / "report.json", observed)
    if observed["assessment"]["status"] != "OBSERVED":
        return {"accepted": False, "candidate": str(inputs / "product"),
                "stages": [], "model_dispatches": 0,
                "error": "Native coding boundary unavailable"}

    for name in ("canary.py", "canary.json"):
        (inputs / name).unlink()
    directory = output / "implementation"
    scratch, private = directory / "scratch", directory / "private"
    scratch.mkdir()
    private.mkdir()
    (inputs / "response.schema.json").write_text(json.dumps(live.object_schema({
        "completed": {"type": "boolean"}, "summary": live.STRING})))
    host.write_diff(inputs / "product", base, inputs / "change.diff")
    protected = {str(path.relative_to(inputs)): host.sha256(path.read_bytes())
                 for path in inputs.iterdir() if path.is_file()}
    git_before = host.snapshot(inputs / "product" / ".git")
    remaining = seconds - (time.monotonic() - started)
    if remaining <= 0:
        return {"accepted": False, "candidate": str(inputs / "product"),
                "stages": [], "model_dispatches": 0, "error": "Coding budget exhausted"}

    prompt = (
        "Implement the complete original request in " + str(inputs / "product") +
        " using your normal coding approach and useful checks. Only product code is "
        "writable; do not commit. Return completed=true when the whole original task "
        "is finished, otherwise false, with a short summary.\n"
        "Original request: " + str(inputs / "source.md") +
        ". Optional check guidance: " + str(inputs / "guidance.md") +
        ". Diff: " + str(inputs / "change.diff") + ". " + execution_map +
        "\nYou have at most " + f"{remaining:.1f}" +
        " seconds including self-checks and a final response.\n"
    )
    receipt = live.launch(live.command(
        codex, inputs, scratch, private, preferences, implementer=True),
        prompt, private, remaining)
    stage = {"role": "implementer", "status": "NOT VERIFIED",
             "receipt": receipt, "usage": None}
    try:
        unchanged = (git_before == host.snapshot(inputs / "product" / ".git")
            and all(host.sha256((inputs / name).read_bytes()) == expected
                    for name, expected in protected.items()))
        if not unchanged:
            raise ValueError("Protected source, guidance, Git or receipt inputs changed")
        native = live.read_events(receipt)
        stage.update(usage=native["usage"], thread_id=native["thread_id"],
                     commands=native["commands"])
        report = native["report"]
        if (set(report) != {"completed", "summary"} or
                type(report["completed"]) is not bool or
                not isinstance(report["summary"], str)):
            raise ValueError("Invalid native coding completion response")
        stage.update(status="OBSERVED", report=report)
    except (OSError, ValueError, KeyError, TypeError) as error:
        stage["error"] = str(error)
    write_record(directory / "stage.json", stage)
    accepted = stage["status"] == "OBSERVED" and stage["report"]["completed"] is True
    if accepted:
        freeze(inputs / "product")
    return {"accepted": accepted, "candidate": str(inputs / "product"),
            "stages": [stage], "model_dispatches": 1, "status": "FINISHED",
            "elapsed_seconds": time.monotonic() - started,
            "transport": "native Codex; self-reported completion only, not acceptance"}
