"""Strict read-only Intentline JSON export adapter for optional Proofline checks.

Only initial acceptance schema 1 and its one original S1 request are supported.
No peer runtime, script, approval, model, test, or external source is executed.
Producer claims and authored oracles remain unverified advice.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from checks import promise_evidence as promises

MARKER = "export-manifest.json"
FILES = ("contract.json", "source-manifest.json", "source-S1.txt")
LIMIT = 2 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("Duplicate Intentline JSON key: " + key)
        out[key] = value
    return out


def parse(raw, name, exact=True):
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=lambda token: (_ for _ in ()).throw(
                               ValueError("Invalid nonfinite Intentline JSON: " + token)))
    except UnicodeError as exc:
        raise ValueError("Invalid UTF-8 in " + name) from exc
    except RecursionError as exc:
        raise ValueError("Excessive nesting in " + name) from exc
    if exact and canonical(value) != raw:
        raise ValueError(name + " is not canonical Intentline JSON")
    return value


def shape(value, required, name, optional=()):
    if (type(value) is not dict or set(required) - set(value) or
            set(value) - set(required) - set(optional)):
        raise ValueError(name + " has missing or unsupported fields")


def expect(value, what, max_length=8192):
    if type(value) is not str or not value.strip() or len(value) > max_length:
        raise ValueError("Invalid " + what)
    return value


def digest(value, what):
    if type(value) is not str or promises.SHA256.fullmatch(value) is None:
        raise ValueError("Invalid SHA-256: " + what)
    return value


def _read_file(dirfd, name, limit=LIMIT):
    if name not in (MARKER, *FILES):
        raise ValueError("Unexpected export file name")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dirfd)
    except OSError as exc:
        raise ValueError("Missing, symlinked or unreadable export file: " + name) from exc
    try:
        mode = os.fstat(fd)
        if not stat.S_ISREG(mode.st_mode) or mode.st_size > limit:
            raise ValueError("Export file is not a bounded regular file: " + name)
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError("Export file too large: " + name)
        return raw
    finally:
        os.close(fd)


def read_files(directory):
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValueError("Intentline import needs POSIX no-follow inspection")
    try:
        dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError("Intentline export root must be a non-symlinked directory") from exc
    try:
        first = _read_file(dfd, MARKER, 262144)
        marker = parse(first, MARKER)
        validate_marker(marker)
        if set(os.listdir(dfd)) != {MARKER, *FILES}:
            raise ValueError("Intentline export has missing/extra files or unsupported scripts")
        files = {name: _read_file(dfd, name) for name in FILES}
        if _read_file(dfd, MARKER, 262144) != first:
            raise ValueError("Intentline export completion marker changed during inspection")
        return {MARKER: first, **files}
    finally:
        os.close(dfd)


def validate_marker(marker):
    shape(marker, ("record", "schema_version", "format", "contract_id",
                   "revision", "contract_sha256", "source_bundle_sha256",
                   "advisory", "authority", "files"), "export-manifest")
    if marker["record"] != "intentline.export" or type(marker["schema_version"]) is not int or marker["schema_version"] != 1:
        raise ValueError("Unsupported Intentline completion-manifest schema")
    if marker["format"] != "json":
        raise ValueError("Unsupported Intentline native/direct/markdown export; use --format json")
    if type(marker["revision"]) is not int or marker["revision"] != 1:
        raise ValueError("Unsupported amended/revised Intentline export; only initial revision 1 is qualified")
    if marker["advisory"] is not True or marker["authority"] not in (
            "unapproved", "operator_asserted_unverified"):
        raise ValueError("Intentline export cannot assert authenticated approval or execution authority")
    expect(marker["contract_id"], "contract_id", 80)
    digest(marker["contract_sha256"], "contract_sha256")
    digest(marker["source_bundle_sha256"], "source_bundle_sha256")
    if type(marker["files"]) is not dict or set(marker["files"]) != set(FILES):
        raise ValueError("Incomplete, multi-source or successor Intentline JSON export")


def check_hashes(files):
    if type(files) is not dict or set(files) != {MARKER, *FILES} or any(
            type(value) is not bytes or len(value) > LIMIT for value in files.values()):
        raise ValueError("Invalid frozen Intentline export file set")
    marker = parse(files[MARKER], MARKER)
    validate_marker(marker)
    for name in FILES:
        if digest(marker["files"][name], name) != sha(files[name]):
            raise ValueError("Intentline export file hash mismatch: " + name)
    return marker


def refs(original, source, name):
    """Validate original producer quotations, then normalize final newline only."""
    lines = source.splitlines(keepends=True)
    if type(original) is not list or not 1 <= len(original) <= 8:
        raise ValueError(name + " lacks source-grounded citations")
    translated = []
    for row in original:
        shape(row, ("source_id", "line_start", "line_end", "quote"), name + " source ref")
        a, b = row["line_start"], row["line_end"]
        if (row["source_id"] != "S1" or type(a) is not int or type(b) is not int or
                not 1 <= a <= b <= len(lines) or b-a > 31):
            raise ValueError(name + " has unsupported S2/invalid original-source lines")
        full = "".join(lines[a-1:b])
        short = full[:-2] if full.endswith("\r\n") else (full[:-1] if full.endswith(("\r", "\n")) else full)
        if row["quote"] not in (full, short):
            raise ValueError(name + " has forged/incorrect original-source quote")
        translated.append({**row, "quote": short})
    return promises._source_quotes(translated, lines, name)


def source(files, request, marker):
    manifest = parse(files["source-manifest.json"], "source-manifest.json")
    shape(manifest, ("manifest", "schema_version", "root", "sources"), "source manifest")
    if manifest["manifest"] != "intentline.sources" or type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported Intentline successor lineage/source manifest")
    if type(manifest["sources"]) is not list or len(manifest["sources"]) != 1:
        raise ValueError("Unsupported multi-source Intentline export; cannot silently drop S2 contexts")
    row = manifest["sources"][0]
    shape(row, ("source_id", "role", "relative_path", "original_location", "identity",
                "declared_authority", "sha256", "bytes"), "source S1")
    if row["source_id"] != "S1" or row["role"] != "request" or row["declared_authority"] != "user_request":
        raise ValueError("Unsupported Intentline original-request authority")
    expect(manifest["root"], "producer root")
    if not Path(manifest["root"]).is_absolute():
        raise ValueError("Intentline producer root is not absolute")
    if row["original_location"] is None:
        if row["relative_path"] is not None or row["identity"] is not None:
            raise ValueError("Invalid stdin source identity")
    else:
        expect(row["original_location"], "producer source path")
        expect(row["relative_path"], "producer relative path")
        try:
            relative = Path(row["original_location"]).relative_to(Path(manifest["root"])).as_posix()
        except ValueError as exc:
            raise ValueError("Intentline source origin is outside producer root") from exc
        if (relative != row["relative_path"] or
                ".." in Path(relative).parts or Path(row["relative_path"]).is_absolute()):
            raise ValueError("Intentline source path identity mismatch or traversal")
        shape(row["identity"], ("device", "inode"), "source inode")
        if any(type(row["identity"][v]) is not int or row["identity"][v] < 0 for v in ("device", "inode")):
            raise ValueError("Invalid producer inode identity")
    raw = files["source-S1.txt"]
    if (type(row["bytes"]) is not int or len(raw) != row["bytes"] or
            digest(row["sha256"], "S1") != sha(raw) or
            sha(files["source-manifest.json"]) != marker["source_bundle_sha256"]):
        raise ValueError("Intentline S1/source manifest identity mismatch")
    if raw != request.encode("utf-8"):
        raise ValueError("Intentline S1 is not the exact full original Proofline request")


def contract(files, request, marker):
    c = parse(files["contract.json"], "contract.json")
    shape(c, ("contract", "schema_version", "contract_id", "revision", "source_bundle_sha256",
              "intended_outcome", "requirements", "constraints", "out_of_scope",
              "open_decisions", "evidence_gaps", "change_notes"), "acceptance contract",
          ("advisory_notes",))
    if (c["contract"] != "intentline.acceptance" or type(c["schema_version"]) is not int or c["schema_version"] != 1 or
            type(c["revision"]) is not int or c["revision"] != 1 or
            c["contract_id"] != marker["contract_id"] or c["revision"] != marker["revision"] or
            c["source_bundle_sha256"] != marker["source_bundle_sha256"] or
            sha(files["contract.json"]) != marker["contract_sha256"]):
        raise ValueError("Intentline contract/version/source identity mismatch")
    if c["change_notes"] != [{"revision": 1, "kind": "initial"}]:
        raise ValueError("Unsupported Intentline revision lineage")
    if type(c["open_decisions"]) is not list or c["open_decisions"]:
        raise ValueError("Intentline contract has unresolved decisions")
    expect(c["intended_outcome"], "intended outcome")
    if type(c["requirements"]) is not list or not 1 <= len(c["requirements"]) <= 64:
        raise ValueError("Missing/oversized Intentline requirements")
    for name in ("constraints", "out_of_scope", "evidence_gaps"):
        if type(c[name]) is not list or len(c[name]) > 64:
            raise ValueError("Invalid Intentline " + name)
    if "advisory_notes" in c and (type(c["advisory_notes"]) is not list or
            any(type(v) is not str for v in c["advisory_notes"])):
        raise ValueError("Invalid Intentline advisory notes")
    ids = set()
    requirements = []
    gap_by_id = {}
    for gap in c["evidence_gaps"]:
        shape(gap, ("requirement_ids", "reason"), "evidence gap")
        expect(gap["reason"], "evidence gap reason")
        if type(gap["requirement_ids"]) is not list or not gap["requirement_ids"]:
            raise ValueError("Intentline evidence gap missing R IDs")
        for rid in gap["requirement_ids"]:
            if type(rid) is not str or promises.R_ID.fullmatch(rid) is None:
                raise ValueError("Invalid Intentline evidence gap R ID")
            gap_by_id.setdefault(rid, []).append(gap["reason"])
    for item in c["requirements"]:
        shape(item, ("id", "statement", "basis", "source_refs", "boundaries",
                     "seam", "oracle", "planned_evidence", "plan_state"), "requirement")
        rid = item["id"]
        if type(rid) is not str or promises.R_ID.fullmatch(rid) is None or rid in ids:
            raise ValueError("Duplicate/invalid Intentline requirement R ID")
        ids.add(rid)
        if item["basis"] not in ("request", "necessary_invariant"):
            raise ValueError("Unsupported Intentline S2 project-context requirement")
        if type(item["plan_state"]) is not str or item["plan_state"] not in ("planned", "gap"):
            raise ValueError("Invalid Intentline plan state")
        for attr in ("statement", "seam", "oracle", "planned_evidence"):
            expect(item[attr], rid + " " + attr)
        if (type(item["boundaries"]) is not list or len(item["boundaries"]) > 64 or
                any(type(x) is not str or not x.strip() for x in item["boundaries"])):
            raise ValueError("Invalid Intentline requirement boundaries")
        requirements.append({**item, "source_refs": refs(item["source_refs"], request, rid)})
    if not set(gap_by_id) <= ids:
        raise ValueError("Intentline evidence gap refers to unknown R ID")
    if any(item["plan_state"] == "gap" and item["id"] not in gap_by_id for item in requirements):
        raise ValueError("Intentline gap-state R lost its evidence-gap reason")
    rest = {}
    for name in ("constraints", "out_of_scope"):
        rest[name] = []
        for item in c[name]:
            fields = ("statement", "basis", "source_refs", "scope") if name == "constraints" else (
                "statement", "source_refs")
            shape(item, fields, name)
            expect(item["statement"], name + " statement")
            if name == "constraints":
                if item["basis"] not in ("request", "necessary_invariant"):
                    raise ValueError("Unsupported S2 project context constraint")
                expect(item["scope"], "constraint scope")
            rest[name].append({**item, "source_refs": refs(item["source_refs"], request, name)})
    return c, requirements, rest, gap_by_id


def links_for(value, rows, checks):
    if value is None:
        value = {}
    ids = {item["id"] for item in rows}
    if type(value) is not dict or set(value) - ids:
        raise ValueError("Intentline links must be a JSON object keyed by known R IDs")
    result = {}
    for rid, refs_ in value.items():
        if type(refs_) is not list or len(refs_) > len(checks):
            raise ValueError("Intentline explicit R check links must be lists")
        seen = set()
        result[rid] = []
        for row in refs_:
            shape(row, ("index", "argv"), rid + " command link")
            n = row["index"]
            if (type(n) is not int or not 0 <= n < len(checks) or n in seen or
                    type(row["argv"]) is not list or row["argv"] != checks[n]):
                raise ValueError("Intentline R check index/argv differs from the selected command")
            seen.add(n)
            result[rid].append({"index": n, "argv": list(checks[n])})
    return result


def compile_package(files, request, checks, check_links=None, failure_details=()):
    marker = check_hashes(files)
    source(files, request, marker)
    c, rows, rest, gaps = contract(files, request, marker)
    linked = links_for(check_links, rows, checks)
    mapping = promises.validate({
        "schema_version": 1, "source_sha256": sha(request.encode("utf-8")),
        "requirements": [{"id": row["id"], "statement": row["statement"],
                          "source_refs": row["source_refs"], "kind": "outcome",
                          "oracle": row["oracle"], "checks": linked.get(row["id"], [])}
                         for row in rows],
        "review": {"performed": False, "proposals": []},
    }, request, checks, failure_details)
    metadata = {
        "record": "intentline.advisory-input", "schema_version": 1,
        "export_format": "json", "contract_id": c["contract_id"],
        "revision": c["revision"], "contract_sha256": marker["contract_sha256"],
        "source_bundle_sha256": marker["source_bundle_sha256"],
        "export_manifest_sha256": sha(files[MARKER]), "source_sha256": sha(files["source-S1.txt"]),
        "export_authority": marker["authority"], "advisory": True,
        "external_caller_approval": "not_supplied_or_authenticated",
        "execution_authority": "not_established",
        "intended_outcome": c["intended_outcome"],
        "requirements": [{**row, "evidence_gap_reasons": gaps.get(row["id"], [])} for row in rows],
        "constraints": rest["constraints"], "out_of_scope": rest["out_of_scope"],
        "evidence_gaps": c["evidence_gaps"], "check_links": linked,
        "coverage_completeness": "UNKNOWN",
    }
    return {"files": files, "mapping": mapping, "metadata": metadata}


def load_export(directory, request, checks, links=None, failure_details=()):
    return compile_package(read_files(directory), request, checks, links, failure_details)


def read_links(path):
    if path is None:
        return None
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Intentline check-link JSON must be regular")
    with path.open("rb") as stream:
        raw = stream.read(262145)
    if len(raw) > 262144:
        raise ValueError("Intentline check-link JSON exceeds 256 KiB")
    return parse(raw, "Intentline check links", exact=False)


def validate_package(package, request, checks, details=()):
    if type(package) is not dict or set(package) != {"files", "mapping", "metadata"}:
        raise ValueError("Invalid Intentline imported package")
    expected = compile_package(package["files"], request, checks,
                               package["metadata"]["check_links"], details)
    if package != expected:
        raise ValueError("Intentline export package identity changed")
    return expected


def freeze(output, files):
    folder = Path(output) / "intentline-export"
    folder.mkdir(mode=0o700, exist_ok=False)
    for name in (MARKER, *FILES):
        fd = os.open(folder / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(files[name])


def readback_intact(record, output):
    try:
        root = Path(output)
        inputs = root / "inputs"
        if inputs.is_symlink() or (inputs / "source.md").is_symlink():
            return False
        original = (inputs / "source.md").read_bytes().decode("utf-8")
        package = load_export(root / "intentline-export", original,
                              record["checks"], record["intentline_advisory"]["check_links"],
                              record.get("failure_details", []))
        return (package["mapping"] == record.get("promise_mapping") and
                package["metadata"] == record["intentline_advisory"])
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        return False
