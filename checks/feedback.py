"""Deterministic, receipt-grounded feedback for existing Proofline checks.

No model, semantic reviewer, inferred test oracle, or execution is involved.
Caller-supplied assertions are advisory; a purported observed value is shown
only when its exact text appears in the bounded host-captured process output.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

from checks import host_probe as host
from checks.native_checks import write_record

MAX_VALUE = 240
MAX_EXCERPT = 280
MAX_PRIMARY_LINES = 3
_R_ID = re.compile(r"R[1-9][0-9]{0,8}\Z")


def validate_failure_details(details, checks):
    """Validate a small optional per-check list before any worker/sandbox call.

    Format: [{"index": 0, "outcome_ids": ["R2"],
              "expected": "Unicode accepted", "observed": "Unicode rejected"}]
    Exact requirement IDs and expectations are caller claims, never authority.
    """
    if details is None:
        return []
    if type(details) is not list or len(details) > len(checks):
        raise ValueError("Failure details must be a JSON list with at most one row per check")
    seen = set()
    normalized = []
    for row in details:
        if type(row) is not dict or set(row) - {"index", "outcome_ids", "expected", "observed"}:
            raise ValueError("Failure details rows accept only index, outcome_ids, expected and observed")
        index = row.get("index")
        if type(index) is not int or not 0 <= index < len(checks) or index in seen:
            raise ValueError("Failure details require a unique valid zero-based check index")
        seen.add(index)
        ids = row.get("outcome_ids", [])
        if (type(ids) is not list or len(ids) > 24 or
                any(type(value) is not str or not _R_ID.fullmatch(value) for value in ids) or
                len(set(ids)) != len(ids)):
            raise ValueError("Failure detail outcome_ids must be distinct R1/R2/... strings")
        has_expected, has_observed = "expected" in row, "observed" in row
        if has_expected != has_observed:
            raise ValueError("Expected and observed details must be supplied together")
        if has_expected:
            for key in ("expected", "observed"):
                value = row[key]
                if (type(value) is not str or not value.strip() or
                        len(value) > MAX_VALUE or "\0" in value):
                    raise ValueError("Failure detail " + key + " must be a short nonempty string")
        if not has_expected and not ids:
            raise ValueError("Failure details need outcome_ids or an expected/observed pair")
        normalized.append({"index": index, "outcome_ids": list(ids),
                           **({"expected": row["expected"], "observed": row["observed"]}
                              if has_expected else {})})
    return sorted(normalized, key=lambda row: row["index"])


def receipt_for(entry):
    receipts = entry.get("receipts", [])
    return receipts[0] if type(receipts) is list and len(receipts) == 1 and type(receipts[0]) is dict else None


def save_receipt(entry, output, index):
    """Retain each existing bounded native receipt outside command-writable scratch."""
    receipt = receipt_for(entry)
    if receipt is None:
        return
    relative = "receipts/check-%03d.json" % index
    target = Path(output) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    write_record(target, receipt)
    entry["receipt_ref"] = relative
    entry["receipt_sha256"] = host.sha256(target.read_bytes())


def receipts_intact(record, output):
    """Validate only predictable host-owned relative receipt paths; no traversal."""
    strict = record.get("feedback_version") == 1
    for index, entry in enumerate(record.get("observations", [])):
        if type(entry) is not dict:
            return False
        receipt = receipt_for(entry)
        ref = entry.get("receipt_ref")
        if not strict and ref is None:
            continue  # Historical reports predate separate bounded receipt files.
        if receipt is None:
            if ref is not None or entry.get("receipts"):
                return False
            continue
        if ref != "receipts/check-%03d.json" % index:
            return False
        target = Path(output) / ref
        if target.is_symlink() or target.parent.is_symlink():
            return False
        try:
            raw = target.read_bytes()
            if (host.sha256(raw) != entry.get("receipt_sha256") or
                    json.loads(raw) != receipt):
                return False
        except (OSError, ValueError, TypeError):
            return False
    return True


def attach_details(entry, details, index):
    """Link advisory metadata only to *actual observed* native failure output."""
    row = next((row for row in details if row["index"] == index), None)
    if row is None:
        return
    entry["outcome_ids"] = row["outcome_ids"]
    if entry.get("status") != "FAILED" or "expected" not in row:
        return
    receipt = receipt_for(entry)
    if (receipt is None or receipt.get("stdout_truncated") or
            receipt.get("stderr_truncated") or
            row["observed"] not in (receipt.get("stdout", "") + "\n" +
                                    receipt.get("stderr", ""))):
        entry["annotation_warning"] = (
            "Caller-supplied observed text was not corroborated by the "
            "bounded native receipt; expected/observed annotation withheld.")
        return
    entry["assertion"] = {
        "expected": row["expected"], "observed": row["observed"],
        "expected_provenance": "caller-supplied, unverified oracle",
        "observed_provenance": "literal text in bounded native output",
    }


def _excerpt(raw, limit=MAX_EXCERPT):
    if not isinstance(raw, str) or not raw:
        return ""
    lines = " | ".join(part.strip() for part in raw.splitlines() if part.strip())
    if len(lines) <= limit:
        return lines
    return "... " + lines[-(limit - 4):]


def _reason(entry, native):
    status = entry.get("status")
    if status == "PASSED":
        return "Selected command exited 0; unselected promises are not demonstrated."
    if status == "FAILED":
        return "Command exited nonzero. Inspect its assertion/error output, fix and rerun."
    if native and native.get("timed_out"):
        return "Native command timed out; execution is unavailable, not a demonstrated product failure."
    if native and (native.get("stdout_truncated") or native.get("stderr_truncated")):
        return "Native output was truncated; the observation is insufficient, not a product failure."
    if native and native.get("error"):
        return "Native execution error; resolve the host/tool issue before evaluating behavior."
    if entry.get("error") == "Cumulative budget exhausted":
        return "Episode budget exhausted; this check was not executed."
    return "Check could not be observed reliably; inspect the native receipt/environment."


def summarize(record):
    """Stable structured summary from declared argv and the existing native receipts."""
    status = record.get("status", "EXECUTION UNAVAILABLE")
    checks = []
    for index, entry in enumerate(record.get("observations", [])):
        native = receipt_for(entry)
        relative = entry.get("receipt_ref") if native else None
        result = {
            "index": index,
            "argv": entry.get("argv", []),
            "status": entry.get("status", "UNAVAILABLE"),
            "exit_code": entry.get("returncode", native.get("exit_code") if native else None),
            "elapsed_seconds": entry.get("elapsed_seconds", 0),
            "receipt_ref": relative,
            "stdout_ref": (relative + "#stdout") if relative else None,
            "stderr_ref": (relative + "#stderr") if relative else None,
            "stdout_excerpt": _excerpt(native.get("stdout", "") if native else ""),
            "stderr_excerpt": _excerpt(native.get("stderr", "") if native else ""),
            "reason": _reason(entry, native),
            "outcome_ids": entry.get("outcome_ids", []),
        }
        if "assertion" in entry and entry.get("status") == "FAILED":
            result["caller_annotation"] = entry["assertion"]
        if "annotation_warning" in entry:
            result["annotation_warning"] = entry["annotation_warning"]
        checks.append(result)
    if status == "CHECKS PASSED":
        headline = "%d/%d selected checks passed" % (len(checks), len(record.get("checks", [])))
        action = "Report only the commands checked; original request coverage remains unknown."
    elif status == "CHECKS FAILED":
        headline = "%d selected check(s) failed" % sum(row["status"] == "FAILED" for row in checks)
        action = "Give the coding agent actual failing command and output; fix and rerun on a new candidate."
    elif status == "CHECKS UNAVAILABLE":
        headline = "Check execution or evidence unavailable"
        action = "Resolve timeout, missing tool, sandbox or missing/truncated evidence; do not infer a defect."
    elif status == "STALE CHECKS":
        headline = "Frozen candidate or receipts changed; checks are stale"
        action = "Do not reuse prior check claims. Verify provenance and run a fresh check."
    else:
        headline = "Execution unavailable or incomplete"
        action = "Resolve the host/candidate/integrity obstacle; no check success has been established."
    return {
        "status": status,
        "headline": headline,
        "source_sha256": record.get("source_sha256"),
        "candidate_commit": record.get("candidate_commit"),
        "candidate_tree": record.get("candidate_tree"),
        "snapshot_sha256": record.get("snapshot"),
        "checks": checks,
        "next_action": action,
        "scope": "Selected executable commands only; completeness of the original user promise is unknown.",
    }


def format_lines(record, limit=MAX_PRIMARY_LINES):
    """Short user/agent-facing text, never dump whole receipts into the CLI."""
    view = summarize(record)
    lines = ["Feedback: " + view["headline"]]
    if view["status"] == "EXECUTION UNAVAILABLE" and record.get("error"):
        lines.append("  Unavailable: " + _excerpt(record["error"], 220))
    relevant = [row for row in view["checks"] if row["status"] != "PASSED"]
    for row in relevant[:limit]:
        arguments = _excerpt(json.dumps(row["argv"], ensure_ascii=False), 160)
        ids = (" [" + ", ".join(row["outcome_ids"]) + "]") if row["outcome_ids"] else ""
        lines.append("  Check %d %s%s (exit %s): %s" %
                     (row["index"] + 1, row["status"], ids, row["exit_code"], arguments))
        snippet = row["stderr_excerpt"] or row["stdout_excerpt"]
        if snippet:
            lines.append("    Output: " + _excerpt(snippet, 180))
        if row.get("caller_annotation"):
            item = row["caller_annotation"]
            lines.append("    Caller expected: " + _excerpt(item["expected"], 120) +
                         "; native output contained: " + _excerpt(item["observed"], 120))
        if row.get("annotation_warning"):
            lines.append("    " + _excerpt(row["annotation_warning"], 180))
    if len(relevant) > limit:
        lines.append("  ... %d additional check(s); see report.json" % (len(relevant) - limit))
    if view["status"] != "CHECKS PASSED":
        lines.append("  Next: " + view["next_action"])
    return lines
