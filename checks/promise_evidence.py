"""Optional source-to-check associations; no AI inference or semantic certification.

An original request is the sole authoritative source. Mapping rows and the
same-agent source review are caller-authored *proposals*, not complete acceptance
criteria, expected test oracles, approvals or independently observed correctness.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "S1"  # One original request. Future peer-context adapters are separate.
R_ID = re.compile(r"R[1-9][0-9]{0,8}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_TREE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
MAX_JSON_BYTES = 262_144


def _object_no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Promise mapping contains duplicate JSON key: " + key)
        value[key] = item
    return value


def read_mapping(path):
    """Read optional explicit JSON once; never import Intentline or execute content."""
    path = Path(path)
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("Promise mapping exceeds 256 KiB")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_object_no_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ValueError("Non-finite JSON number: " + value)))
    except UnicodeDecodeError as error:
        raise ValueError("Promise mapping must be UTF-8 JSON") from error


def _keys(obj, required, optional=(), context="mapping"):
    if type(obj) is not dict or not set(required) <= set(obj) or set(obj) - set(required) - set(optional):
        raise ValueError(context + " has missing or unsupported fields")


def _text(value, name, limit=1600):
    if (type(value) is not str or not value.strip() or len(value) > limit or
            any(ord(c) < 32 and c not in "\n\r\t" for c in value) or
            "\x7f" in value):
        raise ValueError(name + " must be a nonempty bounded text string")
    return value


def _source_quotes(refs, lines, subject):
    if type(refs) is not list or not 1 <= len(refs) <= 8:
        raise ValueError(subject + " needs 1–8 exact original-source citations")
    validated = []
    for ref in refs:
        _keys(ref, ("source_id", "line_start", "line_end", "quote"), context=subject + " citation")
        if ref["source_id"] != SOURCE_ID:
            raise ValueError("Direct mapping supports S1 original-request citations only")
        start, end = ref["line_start"], ref["line_end"]
        if (type(start) is not int or type(end) is not int or
                not 1 <= start <= end <= len(lines) or end - start > 31):
            raise ValueError(subject + " source citation has invalid line bounds")
        exact = "".join(lines[start - 1:end])
        # Only the final line terminator can be omitted, retaining all interior
        # CRLF and blank lines verbatim.
        if exact.endswith("\r\n"):
            exact = exact[:-2]
        elif exact.endswith(("\n", "\r")):
            exact = exact[:-1]
        if ref["quote"] != exact:
            raise ValueError(subject + " quote differs from exact original request at S1 lines")
        validated.append(dict(ref))
    return validated


def validate(mapping, source, checks, failure_details=()):
    """Validate untrusted mapping before model/host effects or output creation."""
    _keys(mapping, ("schema_version", "source_sha256", "requirements"),
          ("candidate_tree", "review"), context="promise mapping")
    if type(source) is not str or mapping["schema_version"] != 1 or type(mapping["schema_version"]) is not int:
        raise ValueError("Unsupported promise mapping schema")
    original_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if type(mapping["source_sha256"]) is not str or not SHA256.fullmatch(mapping["source_sha256"]):
        raise ValueError("source_sha256 must be the exact SHA-256 of the original UTF-8 request")
    if mapping["source_sha256"] != original_sha:
        raise ValueError("Promise mapping source_sha256 does not match the full original request")
    if "candidate_tree" in mapping and (
            type(mapping["candidate_tree"]) is not str or
            not GIT_TREE.fullmatch(mapping["candidate_tree"])):
        raise ValueError("candidate_tree must be an exact Git tree ID when supplied")

    lines = source.splitlines(keepends=True)
    rows = mapping["requirements"]
    if type(rows) is not list or not 1 <= len(rows) <= 64:
        raise ValueError("Promise mapping needs 1–64 caller-supplied requirements")
    ids = set()
    normalized = []
    linked = {}
    for row in rows:
        _keys(row, ("id", "statement", "source_refs", "checks"),
              ("kind", "oracle"), context="requirement")
        rid = row["id"]
        if type(rid) is not str or not R_ID.fullmatch(rid) or rid in ids:
            raise ValueError("Duplicate or invalid stable requirement R ID")
        ids.add(rid)
        statement = _text(row["statement"], rid + " statement")
        cites = _source_quotes(row["source_refs"], lines, rid)
        kind = row.get("kind", "outcome")
        if type(kind) is not str or kind not in ("outcome", "constraint", "exception"):
            raise ValueError(rid + " kind must be outcome, constraint, or exception")
        oracle = row.get("oracle")
        if oracle is not None:
            oracle = _text(oracle, rid + " proposed oracle")
        refs = row["checks"]
        if type(refs) is not list or len(refs) > len(checks):
            raise ValueError(rid + " linked checks must be a list within the selected commands")
        selected, seen = [], set()
        for ref in refs:
            _keys(ref, ("index", "argv"), context=rid + " check reference")
            index = ref["index"]
            if (type(index) is not int or not 0 <= index < len(checks) or
                    index in seen or type(ref["argv"]) is not list or
                    ref["argv"] != checks[index]):
                raise ValueError(rid + " linked command index/argv differs from the selected checks")
            seen.add(index)
            selected.append({"index": index, "argv": list(checks[index])})
            linked.setdefault(rid, set()).add(index)
        normalized.append({"id": rid, "statement": statement, "kind": kind,
                           "source_refs": cites, "checks": selected,
                           **({"oracle": oracle} if oracle is not None else {})})

    review = mapping.get("review", {"performed": False, "proposals": []})
    _keys(review, ("performed", "proposals"), context="optional same-agent review")
    if type(review["performed"]) is not bool or type(review["proposals"]) is not list:
        raise ValueError("Same-agent review needs performed boolean and proposals list")
    if not review["performed"] and review["proposals"]:
        raise ValueError("Proposed omissions require an explicitly reported same-agent review")
    if len(review["proposals"]) > 24:
        raise ValueError("Review has too many unverified source-gap proposals")
    proposals = []
    for item in review["proposals"]:
        _keys(item, ("statement", "source_refs", "suggested_check"),
              context="source-gap proposal")
        proposals.append({"statement": _text(item["statement"], "gap proposal"),
                          "source_refs": _source_quotes(item["source_refs"], lines, "gap proposal"),
                          "suggested_check": _text(item["suggested_check"], "suggested check")})

    for entry in failure_details:
        for rid in entry["outcome_ids"]:
            if rid not in ids or entry["index"] not in linked.get(rid, set()):
                raise ValueError("Failure annotation R ID is absent or not linked to its selected check")

    return {"schema_version": 1, "source_sha256": original_sha,
            "requirements": normalized,
            "review": {"performed": review["performed"], "proposals": proposals},
            **({"candidate_tree": mapping["candidate_tree"]}
               if "candidate_tree" in mapping else {})}


def bind_candidate(mapping, candidate_tree):
    """Exact-tree precondition is opt-in, never an implicit user-snapshot mutation."""
    if "candidate_tree" in mapping and mapping["candidate_tree"] != candidate_tree:
        raise ValueError("Promise mapping candidate_tree does not match the frozen candidate")


def _linked_state(record, indexes):
    if not indexes:
        return ("NOT DEMONSTRATED", "No selected executable check linked")
    if record.get("status") == "STALE CHECKS":
        return ("NOT DEMONSTRATED", "Frozen evidence is stale")
    if record.get("status") == "EXECUTION UNAVAILABLE":
        return ("CHECK UNAVAILABLE", "Candidate or execution boundary unavailable")
    entries = record.get("observations", [])
    outcomes = []
    for index in indexes:
        if index >= len(entries):
            return ("CHECK UNAVAILABLE", "Linked check was not executed or observed")
        entry = entries[index]
        if type(entry) is not dict or entry.get("argv") != record["checks"][index]:
            return ("CHECK UNAVAILABLE", "Linked command observation does not match")
        outcomes.append(entry.get("status"))
    if "UNAVAILABLE" in outcomes or any(s not in ("PASSED", "FAILED") for s in outcomes):
        return ("CHECK UNAVAILABLE", "A linked native check was unavailable or incomplete")
    if "FAILED" in outcomes:
        return ("CHECK FAILED", "A linked executable check failed (actual receipt)")
    return ("LINKED CHECKS PASSED (limited evidence)",
            "Selected commands passed; linked behaviors are not proven in full")


def summarize(record):
    """Summarize advisory rows without allowing a malformed report to claim green."""
    mapping = record.get("promise_mapping")
    if mapping is None:
        return None
    try:
        return _summarize_mapping(record, mapping)
    except (KeyError, TypeError, ValueError, IndexError):
        return {"source_sha256": None, "original_source_ref": "inputs/source.md",
                "candidate_commit": record.get("candidate_commit"),
                "candidate_tree": record.get("candidate_tree"),
                "snapshot_sha256": record.get("snapshot"),
                "coverage_completeness": "UNKNOWN", "requirements": [],
                "mapping_invalid": True,
                "same_agent_review": {"reported_performed": False, "independent": False,
                                       "proposals": [],
                                       "authority": "invalid untrusted mapping"},
                "scope": "Mapping invalid; no accepted requirement coverage evidence."}


def _summarize_mapping(record, mapping):
    rows = []
    for row in mapping["requirements"]:
        indexes = [ref["index"] for ref in row["checks"]]
        state, explanation = _linked_state(record, indexes)
        observations = record.get("observations", [])
        links = [{"index": ref["index"], "argv": ref["argv"],
                  "observation_status": (observations[ref["index"]].get("status", "UNAVAILABLE")
                                         if ref["index"] < len(observations) and
                                         type(observations[ref["index"]]) is dict else "NOT EXECUTED"),
                  "receipt_ref": (observations[ref["index"]].get("receipt_ref")
                                  if ref["index"] < len(observations) and
                                  type(observations[ref["index"]]) is dict else None)}
                 for ref in row["checks"]]
        rows.append({"id": row["id"], "statement": row["statement"], "kind": row["kind"],
                     "source_refs": row["source_refs"], "linked_checks": links,
                     "status": state, "reason": explanation,
                     **({"proposed_oracle": row["oracle"],
                         "oracle_authority": "unverified caller suggestion"}
                        if "oracle" in row else {})})
    result = {"source_sha256": mapping["source_sha256"],
            "original_source_ref": "inputs/source.md",
            "candidate_commit": record.get("candidate_commit"),
            "candidate_tree": record.get("candidate_tree"),
            "snapshot_sha256": record.get("snapshot"),
            "coverage_completeness": "UNKNOWN",
            "requirements": rows,
            "same_agent_review": {
                "reported_performed": mapping["review"]["performed"],
                "independent": False,
                "proposals": mapping["review"]["proposals"],
                "authority": "unverified advisory review; may omit original promises"},
            "scope": "Only explicitly mapped requirements/commands; all original source remains authoritative."}
    producer = record.get("intentline_advisory")
    if producer is not None:
        details = {row["id"]: row for row in producer["requirements"]}
        for row in result["requirements"]:
            detail = details[row["id"]]
            # Intentline authored expectations stay advisory; they never change
            # linked-pass/failed/unavailable/not-demonstrated receipt states.
            row["intentline_planning"] = {
                "basis": detail["basis"], "boundaries": detail["boundaries"],
                "seam": detail["seam"], "planned_evidence": detail["planned_evidence"],
                "plan_state": detail["plan_state"],
                "evidence_gap_reasons": detail["evidence_gap_reasons"],
                "authority": "unverified original-source-grounded proposal",
            }
        result["intentline"] = {
            "contract_id": producer["contract_id"],
            "revision": producer["revision"],
            "contract_sha256": producer["contract_sha256"],
            "source_bundle_sha256": producer["source_bundle_sha256"],
            "export_manifest_sha256": producer["export_manifest_sha256"],
            "source_sha256": producer["source_sha256"],
            "export_authority": producer["export_authority"],
            "external_caller_approval": producer["external_caller_approval"],
            "execution_authority": producer["execution_authority"],
            "intended_outcome": producer["intended_outcome"],
            "constraints": producer["constraints"],
            "out_of_scope": producer["out_of_scope"],
            "evidence_gaps": producer["evidence_gaps"],
            "scope": "Untrusted advisory planning data, not executable tests, proof or consent.",
        }
    return result


def format_lines(record, limit=3):
    evidence = summarize(record)
    if evidence is None:
        return []
    if evidence.get("mapping_invalid"):
        return ["Promise evidence: invalid or tampered mapping; coverage UNKNOWN"]
    rows = evidence["requirements"]
    not_demonstrated = [x for x in rows if x["status"] != "LINKED CHECKS PASSED (limited evidence)"]
    passed = len(rows) - len(not_demonstrated)
    lines = [f"Promise evidence: {passed}/{len(rows)} mapped rows have linked passing checks"
             " (limited); overall coverage UNKNOWN"]
    if "intentline" in evidence:
        info = evidence["intentline"]
        lines.append("  Intentline advisory (" + info["export_authority"] +
                     "): " + str(len(info["evidence_gaps"])) + " plan gap(s); " +
                     str(len(info["constraints"])) + " constraint(s); " +
                     str(len(info["out_of_scope"])) +
                     " exclusion(s) retained; no external approval inferred")
    for row in not_demonstrated[:limit]:
        lines.append(f"  {row['id']} {row['status']}: {row['reason']}")
    if len(not_demonstrated) > limit:
        lines.append(f"  ... {len(not_demonstrated) - limit} more; see report.json")
    review = evidence["same_agent_review"]
    if review["reported_performed"]:
        lines.append(f"  Same-agent gap review: {len(review['proposals'])} unverified proposal(s)"
                     "; not independent or exhaustive")
    return lines


def readback_intact(record, inputs):
    """Revalidate optional input without reading a caller-selected path."""
    mapping = record.get("promise_mapping")
    if mapping is None:
        return record.get("promise_evidence") is None
    try:
        inputs = Path(inputs)
        if (not isinstance(mapping, dict) or inputs.is_symlink() or
                (inputs / "source.md").is_symlink() or
                (inputs / "promises.json").is_symlink()):
            return False
        source = (inputs / "source.md").read_bytes().decode("utf-8")
        frozen = (inputs / "promises.json").read_bytes()
        if len(frozen) > MAX_JSON_BYTES:
            return False
        stored = json.loads(frozen.decode("utf-8"), object_pairs_hook=_object_no_duplicates)
        if stored != mapping:
            return False
        normalized = validate(mapping, source, record["checks"],
                              record.get("failure_details", []))
        if normalized != mapping:
            return False
        bind_candidate(mapping, record["candidate_tree"])
        return record.get("promise_evidence") == summarize(record)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        return False
