"""Offline structure checks only; never a source-faithfulness or spending gate."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARMS = set("ABCD")


def check(root=ROOT):
    load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    manifest, protocol, draft, ledger = (load(n) for n in
        ("task-manifest.json", "protocol.json", "obligations-draft.json",
         "results-template.json"))
    ids = [task["id"] for task in manifest["tasks"]]
    assert len(ids) == len(set(ids)) == 4
    assert manifest["status"] == "CANDIDATES_UNQUALIFIED"
    assert manifest["qualification"] == "NOT_QUALIFIED"
    assert not protocol["live_dispatch_allowed"]
    assert protocol["approval"] == "NOT_GRANTED"
    assert protocol["host_qualification"] == "NOT_PERFORMED"
    assert protocol["independent_review"] == "PENDING"
    assert protocol["candidate_cohort"]["assignment_count"] == 4 * len(ids)
    assert {a["arm"] for a in protocol["assignments"]} == ARMS
    assert len(protocol["assignments"]) == 4 * len(ids)
    assert [(a["task"], a["arm"]) for a in protocol["assignments"][:4]] == [
        (name, "A") for name in ids]
    assert [a["slot"] for a in protocol["assignments"]] == list(range(1, 17))
    assert len({(a["task"], a["arm"]) for a in protocol["assignments"]}) == 16
    assert len(ledger["assignments"]) == 16
    assert all(r["status"] == "NOT_EXECUTED" and
               r["independent_grade"] is None and r["total_seconds"] is None
               and r["actual_billed_cost"] is None for r in ledger["assignments"])
    assert [(r["task"], r["arm"], r["slot"]) for r in ledger["assignments"]] == [
        (a["task"], a["arm"], a["slot"]) for a in protocol["assignments"]]
    assert draft["status"] == "DRAFT_UNREVIEWED"
    assert {x["task"] for x in draft["entries"]} == set(ids)
    for task in manifest["tasks"]:
        source = (root / "requests" / (task["id"] + ".md")).read_text(encoding="utf-8")
        assert source.startswith("# " + task["title"] + "\n")
        assert len(source) > 100
        assert len(task["base_commit"]) == 40
        assert len(task["source_blob_sha"]) == 40
        entry = next(e for e in draft["entries"] if e["task"] == task["id"])
        assert entry["status"] == "DRAFT_NOT_QUALIFIED"
        assert entry["independent_oracle_script"] is None
        assert entry["independent_reviewer"] is None
        assert entry["expectations"] and entry["controls"]
        assert all(row["status"] == "DRAFT_UNTESTED" and
                   source.count(row["source_clause"]) == 1 for row in entry["expectations"])
        assert all(control["status"] == "NOT_EXECUTED" for control in entry["controls"])
    return {"status": "STRUCTURE_VALID_NOT_QUALIFIED", "tasks": len(ids),
            "assignments": len(protocol["assignments"]), "model_dispatches": 0}


if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True))
