"""Offline consumer controls using Intentline's real pinned native v1 source/contract.

The four-file JSON export manifest uses the producer's exact canonical layout.
No Intentline installation, model, network or native sandbox is invoked here.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from checks import intentline_advisory as adapter
from checks import promise_evidence as promises

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/intentline/v1"
SOURCE = (FIXTURE / "source-S1.txt").read_bytes().decode("utf-8")
CHECKS = [["/usr/bin/python3", "-B", "-m", "unittest"], ["/usr/bin/python3", "-B", "cli.py", "--version"]]


class IntentlineAdvisory(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="proofline-intentline-advisory-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.export = self.root / "export"
        shutil.copytree(FIXTURE, self.export)

    def changed(self, name, mutate, *, rehash=True):
        path = self.export / name
        obj = json.loads(path.read_bytes())
        mutate(obj)
        raw = adapter.canonical(obj)
        path.write_bytes(raw)
        if rehash and name != adapter.MARKER:
            marker_file = self.export / adapter.MARKER
            marker = json.loads(marker_file.read_bytes())
            marker["files"][name] = adapter.sha(raw)
            if name == "contract.json":
                marker["contract_sha256"] = adapter.sha(raw)
            if name == "source-manifest.json":
                marker["source_bundle_sha256"] = adapter.sha(raw)
                contract_file = self.export / "contract.json"
                contract = json.loads(contract_file.read_bytes())
                contract["source_bundle_sha256"] = adapter.sha(raw)
                contract_raw = adapter.canonical(contract)
                contract_file.write_bytes(contract_raw)
                marker["contract_sha256"] = adapter.sha(contract_raw)
                marker["files"]["contract.json"] = marker["contract_sha256"]
            marker_file.write_bytes(adapter.canonical(marker))
        return raw

    def test_real_source_contract_and_complete_export_marker_are_accepted(self):
        result = adapter.load_export(self.export, SOURCE, CHECKS)
        self.assertEqual(result["mapping"]["source_sha256"],
                         adapter.sha(SOURCE.encode("utf-8")))
        self.assertEqual([row["id"] for row in result["mapping"]["requirements"]], ["R1", "R2"])
        self.assertTrue(all(not row["checks"] for row in result["mapping"]["requirements"]))
        self.assertEqual(result["metadata"]["revision"], 1)
        self.assertEqual(result["metadata"]["contract_id"], "username-validation")
        self.assertEqual(result["metadata"]["export_authority"], "unapproved")
        self.assertEqual(result["metadata"]["external_caller_approval"], "not_supplied_or_authenticated")
        self.assertEqual(result["metadata"]["execution_authority"], "not_established")
        self.assertEqual(result["metadata"]["requirements"][0]["boundaries"], ["empty", "spaces", "tabs"])
        self.assertIn("validation error", result["metadata"]["requirements"][0]["oracle"])
        self.assertIn("public validation", result["metadata"]["requirements"][0]["seam"])
        self.assertIn("call interface", result["metadata"]["requirements"][0]["planned_evidence"])
        self.assertEqual(result["metadata"]["constraints"][0]["scope"], "Every child")
        self.assertEqual(result["metadata"]["out_of_scope"][0]["statement"],
                         "No other changes to valid usernames")
        rec = {"status": "CHECKS PASSED", "promise_mapping": result["mapping"],
               "intentline_advisory": result["metadata"], "checks": CHECKS,
               "observations": [{"status": "PASSED", "argv": cmd} for cmd in CHECKS]}
        view = promises.summarize(rec)
        self.assertEqual(view["coverage_completeness"], "UNKNOWN")
        self.assertEqual([x["status"] for x in view["requirements"]],
                         ["NOT DEMONSTRATED", "NOT DEMONSTRATED"])
        self.assertEqual(view["requirements"][0]["intentline_planning"]["basis"], "request")
        self.assertEqual(view["intentline"]["export_authority"], "unapproved")
        self.assertEqual(len(view["intentline"]["constraints"]), 1)
        self.assertEqual(len(view["intentline"]["out_of_scope"]), 1)
        self.assertIn("unverified", view["requirements"][0]["oracle_authority"])
        text = "\n".join(promises.format_lines(rec))
        self.assertIn("no external approval inferred", text)
        self.assertIn('inputs/source.md S1:1-1', text)
        self.assertIn('Proposed check focus (unverified Intentline plan): "call interface', text)
        self.assertIn('Proposed boundaries/seam (unverified Intentline): "empty; spaces; tabs"', text)
        self.assertIn('"public validation interface"', text)
        self.assertIn('Proposed oracle (unverified Intentline): "validation error', text)
        self.assertIn('link its exact selected argv to R1', text)
        self.assertIn('link its exact selected argv to R2', text)
        self.assertNotIn('/usr/bin/python3', text)
        self.assertEqual(rec['promise_mapping'], result['mapping'])

    def test_exact_explicit_links_are_the_only_way_to_get_limited_passing_evidence(self):
        links = {"R1": [{"index": 0, "argv": CHECKS[0]}],
                 "R2": [{"index": 1, "argv": CHECKS[1]}]}
        result = adapter.load_export(self.export, SOURCE, CHECKS, links=links)
        self.assertEqual(result["metadata"]["check_links"], links)
        rec = {"status": "CHECKS PASSED", "promise_mapping": result["mapping"],
               "intentline_advisory": result["metadata"], "checks": CHECKS,
               "observations": [{"status": "PASSED", "argv": cmd,
                                 "receipt_ref": "receipts/check-%03d.json" % idx}
                                for idx, cmd in enumerate(CHECKS)]}
        statuses = [row["status"] for row in promises.summarize(rec)["requirements"]]
        self.assertEqual(statuses, ["LINKED CHECKS PASSED (limited evidence)"] * 2)
        self.assertNotIn('Next:', '\n'.join(promises.format_lines(rec)))
        self.assertNotIn('Proposed check focus', '\n'.join(promises.format_lines(rec)))
        rec["observations"][1]["status"] = "FAILED"
        self.assertEqual(promises.summarize(rec)["requirements"][1]["status"], "CHECK FAILED")
        rec["observations"][1]["status"] = "UNAVAILABLE"
        self.assertEqual(promises.summarize(rec)["requirements"][1]["status"], "CHECK UNAVAILABLE")
        rec["status"] = "STALE CHECKS"
        self.assertEqual(promises.summarize(rec)["requirements"][0]["status"], "NOT DEMONSTRATED")

    def test_caller_links_must_match_known_R_ids_selected_indexes_and_exact_argv(self):
        invalid = [
            {"R99": []}, {"R1": "first"}, {"R1": [{"index": 4, "argv": CHECKS[0]}]},
            {"R1": [{"index": True, "argv": CHECKS[0]}]},
            {"R1": [{"index": 0, "argv": CHECKS[1]}]},
            {"R1": [{"index": 0, "argv": CHECKS[0]}, {"index": 0, "argv": CHECKS[0]}]},
            {"R1": [{"index": 0, "argv": CHECKS[0], "approved": True}]},
        ]
        for links in invalid:
            with self.subTest(links=links), self.assertRaises(ValueError):
                adapter.load_export(self.export, SOURCE, CHECKS, links=links)
        with self.assertRaisesRegex(ValueError, "not linked"):
            adapter.load_export(self.export, SOURCE, CHECKS,
                                links={"R1": [{"index": 0, "argv": CHECKS[0]}]},
                                failure_details=[{"index": 0, "outcome_ids": ["R2"]}])

    def test_operator_assertions_remain_unverified_and_other_approval_claims_refused(self):
        self.changed(adapter.MARKER, lambda m: m.update(authority="operator_asserted_unverified"))
        result = adapter.load_export(self.export, SOURCE, CHECKS)
        self.assertEqual(result["metadata"]["export_authority"], "operator_asserted_unverified")
        self.assertEqual(result["metadata"]["execution_authority"], "not_established")
        self.changed(adapter.MARKER, lambda m: m.update(authority="authenticated_external_approval"))
        with self.assertRaisesRegex(ValueError, "approval"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        self.changed(adapter.MARKER, lambda m: m.update(authority="unapproved", advisory=False))
        with self.assertRaises(ValueError):
            adapter.load_export(self.export, SOURCE, CHECKS)

    def test_missing_partial_extra_scripts_symlinks_and_native_exports_are_rejected(self):
        target = self.export / "contract.json"
        original = target.read_bytes()
        target.unlink()
        with self.assertRaisesRegex(ValueError, "missing|Missing|unreadable"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        target.write_bytes(original)
        self.changed(adapter.MARKER, lambda m: m.update(format="proofline-native"))
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        self.changed(adapter.MARKER, lambda m: m.update(format="json"))
        (self.export / "inspect_bundle.py").write_text("print('untrusted code')")
        with self.assertRaisesRegex(ValueError, "extra"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        (self.export / "inspect_bundle.py").unlink()
        target.unlink()
        target.symlink_to(FIXTURE / "contract.json")
        with self.assertRaisesRegex(ValueError, "symlinked|symbolic"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        target.unlink()
        target.write_bytes(original)
        root_link = self.root / "source-link"
        root_link.symlink_to(self.export, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "non-symlinked"):
            adapter.load_export(root_link, SOURCE, CHECKS)

    def test_contract_and_marker_corruption_or_duplicate_json_are_refused(self):
        (self.export / "contract.json").write_text('{"fake":true}')
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        (self.export / "contract.json").write_bytes((FIXTURE/"contract.json").read_bytes())
        (self.export / adapter.MARKER).write_bytes(
            b'{"advisory":true,"advisory":false}\n')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        (self.export / adapter.MARKER).write_bytes((FIXTURE/adapter.MARKER).read_bytes())
        self.changed("contract.json", lambda c: c["requirements"][0].update(
            source_refs=[{"source_id":"S1","line_start":1,"line_end":1,"quote":"Forged promised result"}]))
        with self.assertRaisesRegex(ValueError, "quote"):
            adapter.load_export(self.export, SOURCE, CHECKS)

    def test_revision_successor_context_and_origin_traversal_are_rejected(self):
        self.changed(adapter.MARKER, lambda m: m.update(revision=2))
        with self.assertRaisesRegex(ValueError, "revised|amended"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        self.changed(adapter.MARKER, lambda m: m.update(revision=1))
        self.changed("source-manifest.json", lambda m: m["sources"].append(
            {**m["sources"][0], "source_id": "S2", "role": "context"}))
        with self.assertRaisesRegex(ValueError, "multi-source"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        # Reset and make the original source's metadata point through traversal.
        shutil.rmtree(self.export)
        shutil.copytree(FIXTURE, self.export)
        def traversal(manifest):
            manifest["sources"][0]["original_location"] = manifest["root"] + "/../elsewhere"
            manifest["sources"][0]["relative_path"] = "../elsewhere"
        self.changed("source-manifest.json", traversal)
        with self.assertRaisesRegex(ValueError, "traversal"):
            adapter.load_export(self.export, SOURCE, CHECKS)

    def test_explicit_gap_reasons_survive_and_lost_reasons_fail_closed(self):
        def with_gap(contract):
            contract["requirements"][0]["plan_state"] = "gap"
            contract["evidence_gaps"] = [{"requirement_ids": ["R1"],
                                          "reason": "No acceptance harness available"}]
        self.changed("contract.json", with_gap)
        result = adapter.load_export(self.export, SOURCE, CHECKS)
        self.assertEqual(result["metadata"]["requirements"][0]["evidence_gap_reasons"],
                         ["No acceptance harness available"])
        rec = {"status": "CHECKS PASSED", "checks": CHECKS,
               "observations": [], "promise_mapping": result["mapping"],
               "intentline_advisory": result["metadata"]}
        view = promises.summarize(rec)
        self.assertEqual(view["requirements"][0]["intentline_planning"]["plan_state"], "gap")
        self.assertEqual(len(view["intentline"]["evidence_gaps"]), 1)
        self.assertIn('Plan gap (unverified Intentline): "No acceptance harness available"',
                      '\n'.join(promises.format_lines(rec)))
        self.changed("contract.json", lambda c: c.update(evidence_gaps=[]))
        with self.assertRaisesRegex(ValueError, "lost its evidence"):
            adapter.load_export(self.export, SOURCE, CHECKS)

    def test_hint_excerpts_bound_and_quote_imported_plan_without_changing_it(self):
        def long_plan(contract):
            row = contract['requirements'][0]
            row['planned_evidence'] = 'Advisory\n' + 'p' * 8000
            row['boundaries'] = ['\x1b[31m\nForged status\t' + 'b' * 8000] * 64
            row['seam'] = 's' * 8000
            contract['evidence_gaps'] = [{'requirement_ids': ['R1'], 'reason': 'g' * 8000}]
        self.changed('contract.json', long_plan)
        package = adapter.load_export(self.export, SOURCE, CHECKS)
        rec = {'status': 'CHECKS PASSED', 'checks': CHECKS, 'observations': [],
               'promise_mapping': package['mapping'], 'intentline_advisory': package['metadata']}
        before = copy.deepcopy(rec)
        lines = promises.format_lines(rec)
        self.assertLessEqual(max(map(len, lines)), 400)
        self.assertLessEqual(len(lines), 18)
        self.assertIn('...', '\n'.join(lines))
        self.assertIn('\\u001b[31m Forged status', '\n'.join(lines))
        self.assertNotIn('\x1b', '\n'.join(lines))
        self.assertEqual(rec, before)
        self.assertEqual(promises.summarize(rec)['requirements'][0]['intentline_planning']
                         ['planned_evidence'], 'Advisory\n' + 'p' * 8000)

    def test_unsettled_decisions_and_swapped_S2_quotes_are_rejected(self):
        self.changed("contract.json", lambda c: c.update(open_decisions=[{
            "id":"D1","statement":"Unsettled","kind":"outcome",
            "source_refs":c["requirements"][0]["source_refs"]}]))
        with self.assertRaisesRegex(ValueError, "unresolved"):
            adapter.load_export(self.export, SOURCE, CHECKS)
        shutil.rmtree(self.export)
        shutil.copytree(FIXTURE, self.export)
        self.changed("contract.json", lambda c: c["requirements"][1]["source_refs"][0].update(source_id="S2"))
        with self.assertRaisesRegex(ValueError, "S2"):
            adapter.load_export(self.export, SOURCE, CHECKS)

    def test_round_trip_frozen_export_does_not_follow_producer_changes(self):
        links = {"R1":[{"index":0,"argv":CHECKS[0]}]}
        package = adapter.load_export(self.export, SOURCE, CHECKS, links=links)
        out = self.root / "record"
        out.mkdir()
        (out/"inputs").mkdir()
        (out/"inputs/source.md").write_bytes(SOURCE.encode("utf-8"))
        adapter.freeze(out, package["files"])
        record = {"kind": "bounded_local_check", "status": "CHECKS PASSED",
                  "checks": CHECKS, "promise_mapping": package["mapping"],
                  "intentline_advisory": package["metadata"], "failure_details": []}
        self.assertTrue(adapter.readback_intact(record, out))
        shutil.rmtree(self.export)
        self.assertTrue(adapter.readback_intact(record, out),
                        "Frozen observation must not require original producer path")
        (out/"intentline-export/contract.json").write_text('{"modified":true}')
        self.assertFalse(adapter.readback_intact(record, out))
        (out/"intentline-export/contract.json").unlink()
        (out/"intentline-export/contract.json").symlink_to(FIXTURE/"contract.json")
        self.assertFalse(adapter.readback_intact(record, out))

    def test_package_validate_refuses_swapped_check_map_after_import(self):
        package = adapter.load_export(self.export, SOURCE, CHECKS)
        adapter.validate_package(package, SOURCE, CHECKS)
        corrupted = copy.deepcopy(package)
        corrupted["mapping"]["requirements"][0]["checks"] = [
            {"index": 0, "argv": CHECKS[0]}]
        with self.assertRaisesRegex(ValueError, "identity changed"):
            adapter.validate_package(corrupted, SOURCE, CHECKS)
        with self.assertRaisesRegex(ValueError, "exact full original"):
            adapter.validate_package(package, SOURCE + "A later promise\n", CHECKS)

    def test_links_parser_does_not_execute_or_follow_files(self):
        path = self.root/"links.json"
        valid = {"R1":[{"index":0,"argv":CHECKS[0]}]}
        path.write_text(json.dumps(valid))
        self.assertEqual(adapter.read_links(path), valid)
        path.write_text('{"R1":[],"R1":[]}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            adapter.read_links(path)
        path.unlink()
        path.symlink_to(FIXTURE/adapter.MARKER)
        with self.assertRaisesRegex(ValueError, "regular"):
            adapter.read_links(path)


if __name__ == "__main__":
    unittest.main()
