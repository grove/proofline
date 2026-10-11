"""Read supported source-linked P2P Markdown contracts; never infer approval."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local_links(value, directory):
    links = re.findall(r"\[[^\]\r\n]+\]\(([^()\s]+)\)", value)
    if not links:
        raise ValueError("Binding input needs relative local links to recoverable original bytes")
    for link in links:
        if re.search(r"[:#?%\\]", link) or Path(link).is_absolute():
            raise ValueError("Binding input must use relative local links")
    return [(directory / link).resolve() for link in links]


def source_closure(path, seen=None):
    """Recover transitive original sources, retaining every exact UTF-8 byte stream."""
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        raise ValueError("Cyclic source chain")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if not text.strip():
        raise ValueError("Original source is empty")
    result = [(path, raw)]
    if text.startswith("# Acceptance contract:"):
        fields = re.findall(r"^Source: ([^\r\n]+)\r?$", text, re.MULTILINE)
        if len(fields) != 1:
            raise ValueError("Source contract needs one recoverable original Source field")
        for source in local_links(fields[0], path.parent):
            result.extend(source_closure(source, seen | {path}))
    return result


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
    parent = field("Parent")
    prerequisites = field("Prerequisites")
    preservation_only = prerequisites == "Preserve the exact reviewed predecessor candidate and the issue #72 approval/transition records. Do not run the live-evaluation script or install this candidate before matching fresh review and proof."
    # shortcut: no runtime prerequisite imports; qualify a native receipt adapter when a real dependent task needs it.
    if not preservation_only and prerequisites not in {"None", "None beyond the approved parent agreement for S1 planning or implementation."}:
        raise ValueError("Prerequisites need independently confirmed available outcomes; a reference or closed ticket is insufficient")
    if parent == "None" and prerequisites != "None" and not preservation_only:
        raise ValueError("Parent-dependent readiness needs its binding parent agreement")
    context = []
    if parent != "None":
        parents = local_links(parent, path.parent)
        if len(parents) != 1:
            raise ValueError("Child needs one parent snapshot")
        parent_path = parents[0]
        parent_raw = parent_path.read_bytes()
        parent_text = parent_raw.decode("utf-8")
        if not parent_text.startswith("# Acceptance contract:"):
            raise ValueError("Parent snapshot must preserve a P2P acceptance agreement")
        hashes = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", field("Parent snapshot"))
        if not hashes or digest(parent_raw) != hashes[0]:
            raise ValueError("Parent snapshot changed; reconcile the child's contribution before delivery")
        contribution = field("Contribution")
        plans = local_links(contribution, path.parent)
        if len(plans) != 1:
            raise ValueError("Child needs one retrievable contribution plan")
        plan_raw = plans[0].read_bytes()
        plan_sections = re.findall(rb"^## Approved delivery plan\r?\n.*?(?=^## |\Z)", plan_raw, re.M | re.S)
        hashes = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", contribution)
        if len(hashes) != 1 or len(plan_sections) != 1 or digest(plan_sections[0]) != hashes[0]:
            raise ValueError("Contribution plan changed or is incomplete; recover the exact approved snapshot and reconcile current amendments")
        if prerequisites != "None" and "None beyond the approved parent agreement" not in plan_raw.decode():
            raise ValueError("Contribution plan does not establish absence of prerequisites")
        context = [(parent_path, parent_raw), (plans[0], plan_raw)]
    elif re.search(r"^(Parent snapshot|Contribution):", text, re.MULTILINE):
        raise ValueError("Standalone contract has contradictory parent/contribution metadata")
    field("Intended outcome")
    sources = []
    for source_path in local_links(field("Source"), path.parent):
        sources.extend(source_closure(source_path))
    sources = list(dict(sources).items())
    if preservation_only:
        if parent != "None" or path.parent.parent.name != "work" or path.parent.parent.parent.name != ".p2p":
            raise ValueError("Preservation-only readiness needs its original standalone P2P work-item layout")
        source_text = b"\n".join(raw for _, raw in sources).decode("utf-8")
        match = re.search(r"prior P2P contract is `([^`]+)` v1, SHA-256 `([0-9a-f]{64})`; its saved review and proof reports are identified by SHA-256 `([0-9a-f]{64})` and `([0-9a-f]{64})`", source_text)
        candidate = re.search(r"reviewed recovery candidate: `snapshot:sha256:([0-9a-f]{64})`", source_text)
        if not match or not candidate or "## Exact reviewed predecessor patch\n" not in source_text:
            raise ValueError("Recover the exact predecessor patch and source-bound review/proof identities before delivery")
        relative = Path(match[1])
        if relative.is_absolute() or ".." in relative.parts or not re.fullmatch(r"\.p2p/work/[a-z0-9-]+/contract\.md", match[1]):
            raise ValueError("Unsupported predecessor binding path")
        predecessor = path.parents[3] / relative
        for document, expected in zip((predecessor, predecessor.with_name("review.md"), predecessor.with_name("proof.md")), match.groups()[1:]):
            content = document.read_bytes()
            if digest(content) != expected or (document.name != "contract.md" and candidate[1].encode() not in content):
                raise ValueError("Predecessor agreement or matching review/proof changed; preserve the source-bound candidate")
            context.append((document, content))
    if parent != "None" and parent_path not in dict(sources):
        raise ValueError("Child Source must retain the parent and its original source chain")
    # A single source keeps the original S1 byte identity; bundles index exact constituent bytes.
    source = sources[0][1] if len(sources) == 1 else b"".join(
        f"\nOriginal source: {p}\nSHA-256: {digest(raw)}\nByte length: {len(raw)}\n\n".encode() + raw
        for p, raw in sources)
    sections = re.split(r"^## ([^\r\n]+)\r?\n", text, flags=re.MULTILINE)
    names = sections[1::2]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate contract sections are ambiguous")
    sections = dict(zip(names, sections[2::2]))
    for name in ("Acceptance matrix", "Unresolved gaps", "Open questions", "Out of scope", "Change notes"):
        if not sections.get(name, "").strip():
            raise ValueError(f"Missing contract section: {name}")
    for name in ("Unresolved gaps", "Open questions"):
        if (sections[name].strip() != "- None in the approved S1 product outcome or contribution." and
                not re.fullmatch(r"(?:- )?None(?:\.[^\r\n]*)?", sections[name].strip())):
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
    if parent != "None":
        parent_revisions = re.findall(r"^Contract revision: (v[1-9][0-9]*)\r?$", parent_text, re.MULTILINE)
        matrix = re.findall(r"^## Acceptance matrix\r?\n(.*?)(?=^## |\Z)", parent_text, re.M | re.S)
        if len(parent_revisions) != 1 or len(matrix) != 1:
            raise ValueError("Parent revision or acceptance mapping is incomplete")
        parent_ids = set(re.findall(r"^\|\s*([A-Z][A-Z0-9]*-[0-9]+|[A-Z][0-9]+)\s*\|", matrix[0], re.M))
        for cells in parsed[2:]:
            prefix = f"Parent {parent_revisions[0]}:"
            allocation = cells[1].partition(prefix)[2].split(";", 1)[0]
            references = re.findall(r"\b(?:[A-Z][A-Z0-9]*-[0-9]+|[A-Z][0-9]+)\b", allocation)
            if not references or not set(references) <= parent_ids:
                raise ValueError("Every child criterion needs source-qualified mapping to existing parent obligations")
    scope = "child" if parent != "None" else "combined-parent" if "Children" in sections else "standalone"
    return {"format": "p2p-markdown", "revision": revision,
            "contract_path": str(path.resolve()), "contract_sha256": digest(raw),
            "source_path": str(sources[0][0]), "source_sha256": digest(source),
            "source_files": [{"path": str(p), "sha256": digest(raw)} for p, raw in sources],
            "context_files": [{"path": str(p), "sha256": digest(raw), "content": raw.decode("utf-8")} for p, raw in context],
            "criterion_ids": ids, "scope": scope, "parent_completion": False}, source.decode("utf-8"), text


def adopted_contract(path, contract_sha256, source_sha256, approval_reference,
                     approval_path=None, approval_sha256=None):
    metadata, source, contract = inspect_contract(path)
    if not contract_sha256 or not source_sha256 or not approval_reference or not approval_reference.strip():
        raise ValueError("Exact user adoption is missing: inspect this contract, then supply the user-authorized contract/source hashes and actual approval reference")
    if contract_sha256 != metadata["contract_sha256"] or source_sha256 != metadata["source_sha256"]:
        raise ValueError("Contract or original source changed since adoption; recover the approved bytes or obtain exact new adoption")
    # The initiating user/agent supplies actual authority; a hash or Markdown 'approved' label cannot grant it.
    metadata["approval"] = {"kind": "explicit-user-adoption", "reference": approval_reference}
    if approval_path is not None:
        raw = approval_path.read_bytes()
        if digest(raw) != approval_sha256 or metadata["contract_sha256"] not in raw.decode("utf-8"):
            raise ValueError("Inspected approval reference changed or does not bind this exact contract")
        metadata["approval"] = {"kind": "inspected-p2p-approval", "reference": approval_reference,
                                "path": str(approval_path.resolve()), "sha256": digest(raw), "content": raw.decode("utf-8")}
    elif approval_sha256:
        raise ValueError("Approval digest needs its inspected reference file")
    return metadata, source, contract
