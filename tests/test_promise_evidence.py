"""Promise-to-evidence contract tests; source semantics are advisory, not proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from checks import promise_evidence as promises


SOURCE = "Reject blank usernames.\r\nSupport valid Unicode usernames.\r\nPreserve existing CLI behavior.\r\n"
CHECKS = [["/usr/bin/python", "-m", "unittest"], ["/usr/bin/python", "-B", "cli.py", "--version"]]


def cite(line, text):
    return {"source_id": "S1", "line_start": line, "line_end": line, "quote": text}


def example():
    return {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(SOURCE.encode("utf-8")).hexdigest(),
        "requirements": [
            {"id": "R1", "statement": "Reject blank usernames",
             "kind": "outcome", "source_refs": [cite(1, "Reject blank usernames.")],
             "checks": [{"index": 0, "argv": CHECKS[0]}]},
            {"id": "R2", "statement": "Unicode support",
             "source_refs": [cite(2, "Support valid Unicode usernames.")],
             "oracle": "José is accepted (proposal, not an executable oracle)",
             "checks": []},
            {"id": "R3", "statement": "Preserve API compatibility",
             "kind": "constraint", "source_refs": [cite(3, "Preserve existing CLI behavior.")],
             "checks": [{"index": 1, "argv": CHECKS[1]}]}
        ]
    }


def record(mapping, statuses, status="CHECKS PASSED"):
    return {"status": status, "promise_mapping": mapping, "checks": CHECKS,
            "source_sha256": mapping["source_sha256"], "snapshot": "snapshot-1",
            "candidate_tree": "candidate-tree-1", "candidate_commit": "commit-1",
            "observations": [
                {"status": state, "argv": CHECKS[i], "receipt_ref": "receipts/check-%03d.json" % i}
                for i, state in enumerate(statuses)]}


class SourceBoundMapping(unittest.TestCase):
    def test_green_suite_does_not_convert_unlinked_unicode_into_coverage(self):
        normalized = promises.validate(example(), SOURCE, CHECKS)
        view = promises.summarize(record(normalized, ["PASSED", "PASSED"]))
        self.assertEqual([row["status"] for row in view["requirements"]], [
            "LINKED CHECKS PASSED (limited evidence)", "NOT DEMONSTRATED",
            "LINKED CHECKS PASSED (limited evidence)"])
        self.assertEqual(view["requirements"][1]["linked_checks"], [])
        self.assertEqual(view["coverage_completeness"], "UNKNOWN")
        self.assertFalse(view["same_agent_review"]["reported_performed"])
        self.assertIn("unverified caller", view["requirements"][1]["oracle_authority"])
        lines = "\n".join(promises.format_lines(record(normalized, ["PASSED", "PASSED"])))
        self.assertIn("R2 NOT DEMONSTRATED", lines)
        self.assertIn("coverage UNKNOWN", lines)
        self.assertIn('inputs/source.md S1:2-2', lines)
        self.assertIn('Proposed oracle (unverified caller)', lines)
        self.assertIn('Jos', lines)
        self.assertIn('full original request', lines)
        self.assertIn('Select/author an executable assertion', lines)
        self.assertIn('link its exact selected argv to R2', lines)
        self.assertIn('rerun proofline check', lines)
        self.assertIn('passing remains limited evidence', lines)
        self.assertNotIn("100%", lines)

    def test_missing_plan_is_explicit_without_invented_expectations(self):
        mapping = example()
        mapping['requirements'][1].pop('oracle')
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        rec = record(normalized, ['PASSED', 'PASSED'])
        lines = '\n'.join(promises.format_lines(rec))
        self.assertIn('No source-grounded check plan supplied', lines)
        self.assertNotIn('Proposed', lines)
        self.assertNotIn('José', lines)
        self.assertNotIn('/usr/bin/python', lines)
        self.assertEqual(promises.summarize(rec)['coverage_completeness'], 'UNKNOWN')

    def test_failed_unavailable_and_stale_guidance_follow_receipts(self):
        mapping = example()
        mapping['requirements'] = [mapping['requirements'][0]]
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        cases = [
            ('CHECKS FAILED', ['FAILED'], 'Diagnose the actual linked failure', 'CHECK FAILED'),
            ('CHECKS UNAVAILABLE', ['UNAVAILABLE'], 'Restore the linked execution boundary',
             'CHECK UNAVAILABLE'),
            ('CHECKS UNAVAILABLE', [], 'Restore the linked execution boundary', 'CHECK UNAVAILABLE'),
            ('EXECUTION UNAVAILABLE', [], 'Restore the linked execution boundary', 'CHECK UNAVAILABLE'),
            ('STALE CHECKS', ['PASSED'], 'Restore intact frozen inputs', 'NOT DEMONSTRATED'),
        ]
        for status, observations, action, state in cases:
            with self.subTest(status=status, observations=observations):
                lines = '\n'.join(promises.format_lines(record(normalized, observations, status)))
                self.assertIn(action, lines)
                self.assertIn('R1 ' + state, lines)
                self.assertNotIn('Select/author', lines)
                self.assertNotIn('No selected executable check linked', lines)

    def test_stale_unlinked_rows_withhold_untrusted_plan_and_citations(self):
        normalized = promises.validate(example(), SOURCE, CHECKS)
        normalized['requirements'][1]['oracle'] = 'tampered suggestion'
        rec = record(normalized, ['PASSED', 'PASSED'], 'STALE CHECKS')
        lines = '\n'.join(promises.format_lines(rec))
        self.assertIn('Restore intact frozen inputs', lines)
        self.assertNotIn('tampered suggestion', lines)
        self.assertNotIn('inputs/source.md', lines)
        self.assertNotIn('Select/author', lines)

    def test_mapping_free_and_all_linked_pass_output_stays_concise(self):
        self.assertEqual(promises.format_lines({'status': 'CHECKS PASSED'}), [])
        mapping = example()
        mapping['requirements'].pop(1)
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        self.assertEqual(promises.format_lines(record(normalized, ['PASSED', 'PASSED'])), [
            'Promise evidence: 2/2 mapped rows have linked passing checks (limited); '
            'overall coverage UNKNOWN'])

    def test_output_limits_rows_and_untrusted_multiline_text(self):
        mapping = example()
        template = mapping['requirements'][1]
        mapping['requirements'] = [{**template, 'id': f'R{i}',
                                    'oracle': 'Advisory\n' + 'x' * 1500}
                                   for i in range(1, 65)]
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        rec = record(normalized, ['PASSED', 'PASSED'])
        lines = promises.format_lines(rec)
        self.assertEqual(sum('NOT DEMONSTRATED:' in line for line in lines), 3)
        self.assertIn('61 more; see report.json', lines[-1])
        self.assertLessEqual(max(map(len, lines)), 400)
        self.assertLessEqual(len(lines), 20)
        self.assertIn('...', '\n'.join(lines))
        self.assertEqual(len(promises.summarize(rec)['requirements'][0]['proposed_oracle']), 1509)
        limited = promises.format_lines(rec, limit=1)
        self.assertEqual(sum('NOT DEMONSTRATED:' in line for line in limited), 1)

    def test_one_failed_and_one_unavailable_check_are_distinct(self):
        normalized = promises.validate(example(), SOURCE, CHECKS)
        view = promises.summarize(record(normalized, ["PASSED", "FAILED"], "CHECKS FAILED"))
        self.assertEqual(view["requirements"][0]["status"], "LINKED CHECKS PASSED (limited evidence)")
        self.assertEqual(view["requirements"][1]["status"], "NOT DEMONSTRATED")
        self.assertEqual(view["requirements"][2]["status"], "CHECK FAILED")
        view = promises.summarize(record(normalized, ["PASSED", "UNAVAILABLE"], "CHECKS UNAVAILABLE"))
        self.assertEqual(view["requirements"][2]["status"], "CHECK UNAVAILABLE")
        view = promises.summarize(record(normalized, ["PASSED"], "CHECKS UNAVAILABLE"))
        self.assertEqual(view["requirements"][2]["status"], "CHECK UNAVAILABLE")
        view = promises.summarize(record(normalized, ["PASSED", "PASSED"], "STALE CHECKS"))
        self.assertTrue(all(row["status"] == "NOT DEMONSTRATED" for row in view["requirements"]))
        view = promises.summarize(record(normalized, [], "EXECUTION UNAVAILABLE"))
        self.assertEqual(view["requirements"][0]["status"], "CHECK UNAVAILABLE")

    def test_unverified_review_can_propose_omitted_clauses_without_certifying(self):
        mapping = example()
        # Deliberately omit the Unicode R2 obligation from the authored mapping.
        mapping["requirements"] = [mapping["requirements"][0], mapping["requirements"][2]]
        mapping["review"] = {"performed": True, "proposals": [
            {"statement": "Unicode outcome lacks an execution check",
             "source_refs": [cite(2, "Support valid Unicode usernames.")],
             "suggested_check": "Add Unicode acceptance examples with an independently expected output"}
        ]}
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        view = promises.summarize(record(normalized, ["PASSED", "PASSED"]))
        self.assertEqual(len(view["requirements"]), 2)
        self.assertEqual(len(view["same_agent_review"]["proposals"]), 1)
        self.assertFalse(view["same_agent_review"]["independent"])
        self.assertEqual(view["coverage_completeness"], "UNKNOWN")
        self.assertIn("unverified proposal(s)",
                      "\n".join(promises.format_lines(record(normalized, ["PASSED", "PASSED"]))))

    def test_bad_source_hash_quote_span_or_foreign_source_is_refused(self):
        for kind in ("hash", "quote", "start", "end", "source_id", "type"):
            mapping = example()
            ref = mapping["requirements"][1]["source_refs"][0]
            if kind == "hash":
                mapping["source_sha256"] = "0" * 64
            elif kind == "quote":
                ref["quote"] = "Unicode supported (not in the source)"
            elif kind == "start":
                ref["line_start"] = 0
            elif kind == "end":
                ref["line_end"] = 9
            elif kind == "source_id":
                ref["source_id"] = "S2"
            else:
                ref["line_start"] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                promises.validate(mapping, SOURCE, CHECKS)
        self.assertEqual(promises.validate(example(), SOURCE, CHECKS)["source_sha256"],
                         example()["source_sha256"])

    def test_line_spans_match_original_crlf_exactly(self):
        mapping = example()
        mapping["requirements"][0]["source_refs"] = [
            {"source_id": "S1", "line_start": 1, "line_end": 2,
             "quote": "Reject blank usernames.\r\nSupport valid Unicode usernames."}]
        self.assertEqual(promises.validate(mapping, SOURCE, CHECKS)["requirements"][0]["source_refs"],
                         mapping["requirements"][0]["source_refs"])
        mapping["requirements"][0]["source_refs"][0]["quote"] = (
            "Reject blank usernames.\nSupport valid Unicode usernames.")
        with self.assertRaisesRegex(ValueError, "quote differs"):
            promises.validate(mapping, SOURCE, CHECKS)

    def test_invalid_requirement_rows_wrong_argv_or_duplicate_ids_are_refused(self):
        for kind in ("duplicate", "invalid_id", "missing_quote", "missing_row", "bad_index",
                     "bool_index", "wrong_argv", "same_index", "unknown_field", "bad_kind"):
            mapping = example()
            row = mapping["requirements"][0]
            if kind == "duplicate":
                mapping["requirements"][1]["id"] = "R1"
            elif kind == "invalid_id":
                row["id"] = "R0"
            elif kind == "missing_quote":
                row["source_refs"][0].pop("quote")
            elif kind == "missing_row":
                row.pop("source_refs")
            elif kind == "bad_index":
                row["checks"][0]["index"] = 7
            elif kind == "bool_index":
                row["checks"][0]["index"] = True
            elif kind == "wrong_argv":
                row["checks"][0]["argv"] = ["/usr/bin/python", "-c", "not selected"]
            elif kind == "same_index":
                row["checks"].append(copy.deepcopy(row["checks"][0]))
            elif kind == "unknown_field":
                row["approved"] = True
            else:
                row["kind"] = "certified"
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                promises.validate(mapping, SOURCE, CHECKS)

    def test_conflicting_failure_ids_and_command_links_are_refused(self):
        details = [{"index": 0, "outcome_ids": ["R2"]}]
        with self.assertRaisesRegex(ValueError, "not linked"):
            promises.validate(example(), SOURCE, CHECKS, details)
        details = [{"index": 1, "outcome_ids": ["R99"]}]
        with self.assertRaisesRegex(ValueError, "not linked"):
            promises.validate(example(), SOURCE, CHECKS, details)
        good = [{"index": 0, "outcome_ids": ["R1"]}]
        self.assertEqual(promises.validate(example(), SOURCE, CHECKS, good)["requirements"][0]["id"], "R1")

    def test_candidate_tree_optional_pin_must_match_frozen_tree(self):
        mapping = example()
        mapping["candidate_tree"] = "1" * 40
        normalized = promises.validate(mapping, SOURCE, CHECKS)
        promises.bind_candidate(normalized, "1" * 40)
        with self.assertRaisesRegex(ValueError, "frozen candidate"):
            promises.bind_candidate(normalized, "2" * 40)
        mapping["candidate_tree"] = "../bad"
        with self.assertRaises(ValueError):
            promises.validate(mapping, SOURCE, CHECKS)

    def test_reviewer_proposals_are_source_grounded_and_never_cause_a_model_dispatch(self):
        mapping = example()
        mapping["review"] = {"performed": False, "proposals": [
            {"statement": "Maybe missing Unicode", "source_refs": [cite(2, "Support valid Unicode usernames.")],
             "suggested_check": "Write a targeted test"}
        ]}
        with self.assertRaisesRegex(ValueError, "review"):
            promises.validate(mapping, SOURCE, CHECKS)
        mapping["review"]["performed"] = True
        mapping["review"]["proposals"][0]["source_refs"][0]["quote"] = "Fabricated quote"
        with self.assertRaisesRegex(ValueError, "quote differs"):
            promises.validate(mapping, SOURCE, CHECKS)

    def test_read_mapping_rejects_duplicate_keys_and_giant_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mapping.json"
            path.write_text('{"requirements":[],"requirements":[]}')
            with self.assertRaisesRegex(ValueError, "duplicate"):
                promises.read_mapping(path)
            path.write_bytes(b" " * (promises.MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "256 KiB"):
                promises.read_mapping(path)
            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                promises.read_mapping(path)
            path.write_text(json.dumps(example(), ensure_ascii=False))
            self.assertEqual(promises.read_mapping(path)["schema_version"], 1)

    def test_frozen_mapping_readback_detects_tampering_or_removed_inputs(self):
        normalized = promises.validate(example(), SOURCE, CHECKS)
        with tempfile.TemporaryDirectory() as tmp:
            inputs = Path(tmp)
            (inputs / "source.md").write_bytes(SOURCE.encode("utf-8"))
            (inputs / "promises.json").write_text(json.dumps(normalized, ensure_ascii=False))
            rec = record(normalized, ["PASSED", "PASSED"])
            rec["promise_evidence"] = promises.summarize(rec)
            self.assertTrue(promises.readback_intact(rec, inputs))
            altered = copy.deepcopy(rec)
            altered["promise_evidence"]["requirements"][1]["status"] = "LINKED CHECKS PASSED (limited evidence)"
            self.assertFalse(promises.readback_intact(altered, inputs))
            altered = copy.deepcopy(rec)
            altered["candidate_tree"] = "2" * 40
            self.assertFalse(promises.readback_intact(altered, inputs))
            (inputs / "promises.json").write_text('{"fake":true}')
            self.assertFalse(promises.readback_intact(rec, inputs))
            (inputs / "promises.json").write_text(json.dumps(normalized))
            (inputs / "source.md").write_text("Changed original!")
            self.assertFalse(promises.readback_intact(rec, inputs))


if __name__ == "__main__":
    unittest.main()
