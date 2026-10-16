"""Trusted no-model controls for the real producer, adapter and native checks."""
import json
from pathlib import Path
import sys

from checks import host_probe as host, intentline_advisory as adapter, local_run
from evaluation.matched import corpus


def check_adapter_roundtrip(root, install_tool, selected_checks, boundary, *, codex="/opt/homebrew/bin/codex"):
    product = corpus.seed("atomic-transfers", root / "inputs", "reference")
    host.git(product, "init", "--quiet", "--template=")
    host.git(product, "add", "--all")
    host.git(product, "commit", "--quiet", "-m", "Trusted adapter qualification")
    inputs = product.parent
    install_tool(inputs)
    boundary(inputs, root / "coding-profile", worker=True)
    (product / "app.py").write_text(corpus.candidate("atomic-transfers"))
    (product / "app.py").chmod(0o644)
    scratch, private = root / "scratch", root / "private"
    scratch.mkdir(); private.mkdir()
    receipts = []
    cli = [str(Path(sys.executable).resolve()), "-B", str(inputs / "intentline_cli.py")]

    def invoke(args):
        command = host.sandbox_argv(codex, inputs, scratch, private)
        command = command[:command.index("--") + 1] + cli + args
        receipt = host.run_command(command, scratch, 15)
        receipts.append(receipt)
        if not host.succeeded(receipt) or receipt.get("stdout_truncated") or receipt.get("stderr_truncated"):
            raise ValueError("Native Intentline control unavailable: " + receipt.get("stderr", ""))
        response = json.loads(receipt["stdout"])
        if response.get("ok") is not True:
            raise ValueError("Intentline control did not succeed")
        return response["data"]

    plan, export = scratch / "plan", scratch / "export"
    prepared = invoke(["prepare", "--source", str(inputs / "source.md"), "--root", str(inputs), "--out", str(plan), "--json"])
    lines = corpus.REQUESTS["atomic-transfers"].splitlines(keepends=True)
    requirements = []
    # This source-grounded control draft never reaches a task worker.
    for index, (start, end, statement, seam, oracle) in enumerate([
            (1, 6, "Apply valid transfers in order and reject invalid/overdrawn accounts", "app.process", "Ordered balances; intermediate/self overdrafts rejected"),
            (8, 10, "Expose ordered batch processing and reject any invalid member", "service.batch", "One result per input, invalid member rejects batch"),
            (11, 13, "Preserve inputs, exact CLI compatibility, extra keys and source-correct tests", "CLI and input snapshots", "No mutation; unchanged CLI bytes; extra keys accepted")], 1):
        requirements.append({"id": f"R{index}", "statement": statement, "basis": "request",
                             "source_refs": [{"source_id": "S1", "line_start": start, "line_end": end,
                                              "quote": "".join(lines[start-1:end]).rstrip("\n")}],
                             "boundaries": [oracle], "seam": seam, "oracle": oracle,
                             "planned_evidence": "Chosen project commands and finite independent probes", "plan_state": "planned"})
    draft = {"contract": "intentline.acceptance", "schema_version": 1, "contract_id": "issue16-control", "revision": 1,
             "source_bundle_sha256": prepared["source_bundle_sha256"], "intended_outcome": "Entire atomic transfer request",
             "requirements": requirements, "constraints": [], "out_of_scope": [], "open_decisions": [],
             "evidence_gaps": [], "change_notes": [{"revision": 1, "kind": "initial"}]}
    (scratch / "draft.json").write_text(json.dumps(draft))
    invoke(["propose", "--work", str(plan), "--draft", str(scratch / "draft.json"), "--json"])
    invoke(["check", "--work", str(plan), "--json"])
    invoke(["render", "--work", str(plan), "--json"])
    invoke(["export", "--work", str(plan), "--format", "json", "--out", str(export), "--json"])
    checks = selected_checks("atomic-transfers")
    package = adapter.load_export(export, corpus.REQUESTS["atomic-transfers"], checks,
                                  links={"R1": [{"index": 0, "argv": checks[0]}]})
    before = host.snapshot(product)
    result = local_run.check(product, corpus.REQUESTS["atomic-transfers"], checks, root / "check",
                             seconds=60, check_seconds=15, intentline_package=package)
    readback = local_run.inspect(root / "check/report.json")
    if (result["status"] != "CHECKS PASSED" or readback["status"] != "CHECKS PASSED" or result["model_dispatches"] != 0
            or host.snapshot(product) != before or result["promise_evidence"]["coverage_completeness"] != "UNKNOWN"
            or result["promise_evidence"]["requirements"][1]["status"] != "NOT DEMONSTRATED"):
        raise ValueError("Producer/adapter/check binding control mismatch")
    (root / "qualification.json").write_text(json.dumps({"model_dispatches": 0, "status": "OBSERVED",
        "native_cli_receipts": receipts, "package_metadata": package["metadata"], "check_status": readback["status"],
        "check_candidate_tree": result["candidate_tree"], "promise_evidence": result["promise_evidence"]}, indent=2))
