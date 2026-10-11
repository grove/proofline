"""Read the current standalone P2P Markdown contract; never infer approval."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_contract(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")

    def field(name):
        values = re.findall(r"^" + re.escape(name) + r": ([^\r\n]+)\r?$", text, re.MULTILINE)
        if len(values) != 1:
            raise ValueError(f"Contract needs one unambiguous {name} field")
        return values[0]

    if len(re.findall(r"^# Acceptance contract: .+\r?$", text, re.MULTILINE)) != 1:
        raise ValueError("Unsupported contract: expected the current P2P Markdown heading")
    revision = field("Contract revision")
    if not re.fullmatch(r"v[1-9][0-9]*", revision):
        raise ValueError("Unsupported contract revision")
    # shortcut: standalone local-source contracts only; qualify parent/prerequisite bindings before expanding.
    if field("Parent") != "None":
        raise ValueError("Parent/child input needs a qualified snapshot and contribution adapter; parent completion is not established")
    if field("Prerequisites") != "None":
        raise ValueError("Prerequisites need independently confirmed available outcomes; a reference or closed ticket is insufficient")
    if re.search(r"^(Parent snapshot|Contribution):", text, re.MULTILINE):
        raise ValueError("Standalone contract has contradictory parent/contribution metadata")
    field("Intended outcome")
    source_link = re.fullmatch(r"\[[^\]\r\n]+\]\(([^()\s]+\.md)\)", field("Source"))
    if not source_link or re.search(r"[:#?%\\]", source_link[1]) or Path(source_link[1]).is_absolute():
        raise ValueError("Source must be one relative local Markdown link to recoverable original bytes")
    source_path = (path.parent / source_link[1]).resolve()
    source = source_path.read_bytes()
    if not source.decode("utf-8").strip():
        raise ValueError("Original source is empty")
    sections = re.split(r"^## ([^\r\n]+)\r?\n", text, flags=re.MULTILINE)
    names = sections[1::2]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate contract sections are ambiguous")
    sections = dict(zip(names, sections[2::2]))
    for name in ("Acceptance matrix", "Unresolved gaps", "Open questions", "Out of scope", "Change notes"):
        if not sections.get(name, "").strip():
            raise ValueError(f"Missing contract section: {name}")
    for name in ("Unresolved gaps", "Open questions"):
        if sections[name].strip() not in {"None", "- None"}:
            raise ValueError(f"Resolve {name.lower()} before delivery; the adapter does not replan")
    rows = [line.strip() for line in sections["Acceptance matrix"].splitlines() if line.strip()]
    expected = ["ID", "Source", "Requirement", "Boundaries / counterexamples", "Seam", "Oracle", "Planned evidence", "Plan state"]
    parsed = []
    for row in rows:
        if not row.startswith("|") or not row.endswith("|"):
            raise ValueError("Unsupported acceptance matrix: use the current eight-column Markdown table")
        cells = [cell.strip() for cell in row[1:-1].split("|")]
        if len(cells) != 8 or not all(cells):
            raise ValueError("Incomplete or unsupported acceptance row")
        parsed.append(cells)
    if (len(parsed) < 3 or parsed[0] != expected or
            not all(re.fullmatch(r":?-{3,}:?", cell) for cell in parsed[1])):
        raise ValueError("Unsupported acceptance matrix header or empty criteria")
    ids = []
    for cells in parsed[2:]:
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+|[A-Z][0-9]+", cells[0]) or cells[0] in ids:
            raise ValueError("Material criterion IDs must be unique and preserved")
        if cells[-1] != "planned":
            raise ValueError("Contract has a gap or candidate verdict in its plan state")
        ids.append(cells[0])
    return {"format": "p2p-standalone-markdown", "revision": revision,
            "contract_path": str(path.resolve()), "contract_sha256": digest(raw),
            "source_path": str(source_path), "source_sha256": digest(source),
            "criterion_ids": ids, "scope": "standalone", "parent_completion": False}, source.decode("utf-8"), text


def adopted_contract(path, contract_sha256, source_sha256, approval_reference):
    metadata, source, contract = inspect_contract(path)
    if not contract_sha256 or not source_sha256 or not approval_reference or not approval_reference.strip():
        raise ValueError("Exact user adoption is missing: inspect this contract, then supply the user-authorized contract/source hashes and actual approval reference")
    if contract_sha256 != metadata["contract_sha256"] or source_sha256 != metadata["source_sha256"]:
        raise ValueError("Contract or original source changed since adoption; recover the approved bytes or obtain exact new adoption")
    # The initiating user/agent supplies actual authority; a hash or Markdown 'approved' label cannot grant it.
    metadata["approval"] = {"kind": "explicit-user-adoption", "reference": approval_reference}
    return metadata, source, contract
