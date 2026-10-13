"""Deterministic feedback tests. No model, shell or native sandbox qualification."""
import json
from pathlib import Path
import tempfile
import unittest

from checks import feedback


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.checks = [["/bin/python3", "-B", "-m", "unittest"],
                       ["/bin/python3", "-B", "some other test"]]

    def test_valid_optional_annotations_bind_to_selected_indexes(self):
        supplied = [{"index": 1, "outcome_ids": ["R2", "R7"],
                     "expected": "accept Unicode", "observed": "rejects Unicode"},
                    {"index": 0, "outcome_ids": ["R1"]}]
        self.assertEqual([x["index"] for x in feedback.validate_failure_details(supplied, self.checks)], [0, 1])
        self.assertEqual(feedback.validate_failure_details(None, self.checks), [])
        self.assertEqual(feedback.validate_failure_details([], self.checks), [])

    def test_malformed_metadata_refused_before_runtime(self):
        examples = [
            {}, "bad", [True],
            [{"index": True, "outcome_ids": ["R1"]}],
            [{"index": 2, "outcome_ids": ["R1"]}],
            [{"index": -1, "outcome_ids": ["R1"]}],
            [{"index": 0, "outcome_ids": ["R1"]},
             {"index": 0, "outcome_ids": ["R2"]}],
            [{"index": 0, "outcome_ids": "R1"}],
            [{"index": 0, "outcome_ids": ["R0"]}],
            [{"index": 0, "outcome_ids": ["R1", "R1"]}],
            [{"index": 0, "outcome_ids": ["R1"], "expected": "yes"}],
            [{"index": 0, "observed": "no"}],
            [{"index": 0, "outcome_ids": [], "expected": 123, "observed": "no"}],
            [{"index": 0, "expected": "x", "observed": " "}],
            [{"index": 0, "expected": "x" * 241, "observed": "no"}],
            [{"index": 0, "outcome_ids": ["R1"], "check_argv": ["/bin/false"]}],
            [{"index": 0}],
        ]
        for value in examples:
            with self.subTest(value=value), self.assertRaises(ValueError):
                feedback.validate_failure_details(value, self.checks)

    def fail_entry(self, stdout="", stderr="", code=3, truncated=False):
        receipt = {"kind": "process_probe", "argv": ["sandbox", "argv"],
                   "exit_code": code, "timed_out": False,
                   "stdout": stdout, "stderr": stderr,
                   "stderr_truncated": truncated}
        return {"argv": self.checks[0], "status": "FAILED", "returncode": code,
                "elapsed_seconds": 0.251, "receipts": [receipt]}

    def record(self, entries, status="CHECKS FAILED"):
        return {"kind": "bounded_local_check", "feedback_version": 1, "status": status,
                "checks": self.checks[:len(entries)], "observations": entries,
                "source_sha256": "original-request", "candidate_commit": "exact-tree"}

    def test_actual_failure_includes_stderr_and_receipt_reference_without_guessing(self):
        entry = self.fail_entry(stderr="Traceback:\nAssertionError: wrong answer\n")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            feedback.save_receipt(entry, output, 0)
            self.assertTrue(feedback.receipts_intact(self.record([entry]), output))
            view = feedback.summarize(self.record([entry]))
            row = view["checks"][0]
            self.assertEqual(row["status"], "FAILED")
            self.assertEqual(row["argv"], self.checks[0])
            self.assertEqual(row["exit_code"], 3)
            self.assertEqual(row["elapsed_seconds"], 0.251)
            self.assertEqual(row["receipt_ref"], "receipts/check-000.json")
            self.assertEqual(row["stdout_ref"], "receipts/check-000.json#stdout")
            self.assertEqual(row["stderr_ref"], "receipts/check-000.json#stderr")
            self.assertIn("AssertionError", row["stderr_excerpt"])
            self.assertNotIn("caller_annotation", row)
            self.assertEqual(view["source_sha256"], "original-request")
            self.assertEqual(view["candidate_commit"], "exact-tree")
            text = "\n".join(feedback.format_lines(self.record([entry])))
            self.assertIn("Check 1 FAILED", text)
            self.assertIn("AssertionError", text)
            self.assertIn("fix and rerun", text.lower())

    def test_caller_expected_and_observed_need_native_corroboration(self):
        details = feedback.validate_failure_details(
            [{"index": 0, "outcome_ids": ["R2"],
              "expected": "Unicode accepted", "observed": "Unicode rejected"}], self.checks)
        verified = self.fail_entry(stderr="AssertionError: Unicode rejected\n")
        feedback.attach_details(verified, details, 0)
        row = feedback.summarize(self.record([verified]))["checks"][0]
        self.assertEqual(row["outcome_ids"], ["R2"])
        self.assertEqual(row["caller_annotation"]["expected"], "Unicode accepted")
        self.assertEqual(row["caller_annotation"]["observed"], "Unicode rejected")
        self.assertIn("unverified oracle", row["caller_annotation"]["expected_provenance"])

        not_observed = self.fail_entry(stderr="Actual traceback says something else")
        feedback.attach_details(not_observed, details, 0)
        row = feedback.summarize(self.record([not_observed]))["checks"][0]
        self.assertNotIn("caller_annotation", row)
        self.assertIn("not corroborated", row["annotation_warning"])
        text = "\n".join(feedback.format_lines(self.record([not_observed])))
        self.assertNotIn("Unicode accepted", text)
        self.assertIn("something else", text)

    def test_truncated_output_cannot_ground_expected_actual_pair(self):
        entry = self.fail_entry(stderr="Unicode rejected", truncated=True)
        details = feedback.validate_failure_details(
            [{"index": 0, "expected": "Unicode accepted", "observed": "Unicode rejected"}],
            self.checks)
        feedback.attach_details(entry, details, 0)
        self.assertNotIn("assertion", entry)
        self.assertIn("not corroborated", entry["annotation_warning"])
        self.assertEqual(feedback.summarize(self.record([entry]))["checks"][0]["status"], "FAILED")
        # In live execution native_checks marks this unavailable. A malformed
        # synthetic FAILED receipt cannot become evidence of semantic success.

    def test_passes_do_not_get_assertion_claims_or_an_extra_stage(self):
        entry = self.fail_entry(stderr="", code=0)
        entry["status"] = "PASSED"
        entry["returncode"] = 0
        details = feedback.validate_failure_details(
            [{"index": 0, "outcome_ids": ["R1"],
              "expected": "pass", "observed": "pass"}], self.checks)
        feedback.attach_details(entry, details, 0)
        view = feedback.summarize(self.record([entry], "CHECKS PASSED"))
        self.assertNotIn("caller_annotation", view["checks"][0])
        self.assertIn("1/1 selected checks passed", view["headline"])
        self.assertEqual(len(feedback.format_lines(self.record([entry], "CHECKS PASSED"))), 1)
        self.assertIn("original user promise", view["scope"])

    def test_unavailable_timeout_truncation_and_missing_evidence_are_not_defects(self):
        cases = [
            ({"status": "UNAVAILABLE", "receipts": [{"exit_code": None, "timed_out": True}]},
             "timed out"),
            ({"status": "UNAVAILABLE", "receipts": [{"exit_code": None, "stdout_truncated": True}]},
             "truncated"),
            ({"status": "UNAVAILABLE", "receipts": [{"error": "no sandbox executable"}]},
             "execution error"),
            ({"status": "UNAVAILABLE", "receipts": [], "error": "Cumulative budget exhausted"},
             "budget exhausted"),
            ({"status": "UNAVAILABLE", "receipts": []}, "not be observed"),
        ]
        for entry, message in cases:
            entry.update(argv=self.checks[0], elapsed_seconds=0.0)
            with self.subTest(message=message):
                row = feedback.summarize(self.record([entry], "CHECKS UNAVAILABLE"))["checks"][0]
                self.assertIn(message, row["reason"])
                self.assertNotIn("caller_annotation", row)
                self.assertNotIn("product failure", " ".join(feedback.format_lines(
                    self.record([entry], "CHECKS UNAVAILABLE"))).lower())

    def test_unavailable_and_stale_headers_are_not_test_failures(self):
        cases = [
            ("EXECUTION UNAVAILABLE", "Execution unavailable", "Native sandbox not qualified"),
            ("STALE CHECKS", "stale", None),
            ("CHECKS UNAVAILABLE", "unavailable", None),
        ]
        for status, needle, error in cases:
            record = self.record([], status)
            if error:
                record["error"] = error
            with self.subTest(status=status):
                text = "\n".join(feedback.format_lines(record))
                self.assertIn(needle.lower(), text.lower())
                self.assertNotIn("Selected check(s) failed", text)

    def test_missing_or_tampered_external_receipts_are_stale(self):
        entry = self.fail_entry(stderr="bad")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            feedback.save_receipt(entry, output, 0)
            record = self.record([entry])
            self.assertTrue(feedback.receipts_intact(record, output))
            receipt = output / "receipts/check-000.json"
            original = receipt.read_bytes()
            receipt.write_text('{"malicious":true}')
            self.assertFalse(feedback.receipts_intact(record, output))
            receipt.write_bytes(original)
            self.assertTrue(feedback.receipts_intact(record, output))
            entry["receipt_ref"] = "../outside"
            self.assertFalse(feedback.receipts_intact(record, output))
            entry["receipt_ref"] = "receipts/check-000.json"
            receipt.unlink()
            self.assertFalse(feedback.receipts_intact(record, output))

    def test_output_is_bounded_even_with_large_logs_and_many_failures(self):
        observations = []
        for i in range(8):
            entry = self.fail_entry(stderr="failure " + "z" * 2500)
            entry["argv"] = ["/usr/bin/python", "--lots-of-arguments", str(i)] * 9
            observations.append(entry)
        record = self.record(observations)
        record["checks"] = [x["argv"] for x in observations]
        primary = "\n".join(feedback.format_lines(record))
        self.assertLess(len(primary), 2200)
        self.assertIn("5 additional check(s)", primary)
        self.assertLessEqual(len(feedback.summarize(record)["checks"][0]["stderr_excerpt"]), 280)


if __name__ == "__main__":
    unittest.main()
