"""Issue #36: zero-model, future-only qualification and regression controls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation import future_cache
from evaluation.recovery import corpus
from evaluation.source_preflight import qualify


QUOTES = {
    "compatibility": "Keep Cache(clock), Cache.get(key, loader), app.process, service.handle and CLI compatible.",
    "actions": ('For actions=[{"op":"get","key":"x","value":1,"at":0,"ttl":2},\n'
                '{"op":"get","key":"x","value":2,"at":2,"ttl":2},{"op":"clear"}],\n'
                'return {"values":[1,2,1],"loads":2}.'),
    "expiry": "Use the injected clock. A finite entry expires when now >= insertion_time + ttl;\nttl=0 loads on every call.",
    "copies": "Return deep copies on both misses and hits so caller changes cannot corrupt entries.",
    "invalidation": "Add Cache.invalidate(key) returning whether an entry existed, even if expired.",
    "invalid_ttl": ("Extend Cache.get(key, loader, ttl=None). None caches indefinitely; ttl is a finite\n"
                    "nonnegative int/float excluding bool; validate before any hit or loader call."),
    "loader_failure": "A loader exception must not populate the cache.",
}


def declaration(source=future_cache.SOURCE, allowed=("ValueError", "TypeError"),
                explicit=False):
    """Authored offline fixture. Not a real independently approved live study."""
    rows = []
    for identifier, item in future_cache.CASE_SPECS.items():
        row = {"id":identifier, "kind":item["kind"], "cases":item["cases"][:],
               "claim":"Source-bound "+identifier.replace("_"," "),
               "source_clause":QUOTES[identifier], "support":"source",
               "ambiguity":"", "acceptable_alternatives":[]}
        if identifier == "invalid_ttl":
            row["allowed_exceptions"] = list(allowed)
            if explicit:
                row["source_clause"] = "Invalid TTL must raise ValueError."
            else:
                row["ambiguity"] = "Original source requires validation but names no exception class."
                row["acceptable_alternatives"] = ["ValueError","TypeError"]
                row["exception_policy"] = "unprescribed_validation"
        rows.append(row)
    text = future_cache.script(allowed)
    return {
        "schema_version":1, "study_id":"issue36-offline-cache-controls",
        "author":"fixture author", "source_sha256":hashlib.sha256(source).hexdigest(),
        "oracle_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "expectations":rows,
    }


class SourceQualification(unittest.TestCase):
    def test_fully_source_bound_and_explicit_exception(self):
        current = declaration()
        self.assertEqual(qualify(current, source=future_cache.SOURCE,
                                 oracle_text=future_cache.script(),
                                 inventory=future_cache.CASE_SPECS)["status"],"QUALIFIED")
        explicit_source = future_cache.SOURCE + b"\nInvalid TTL must raise ValueError.\n"
        stricter=declaration(explicit_source, ("ValueError",), explicit=True)
        self.assertEqual(qualify(stricter,source=explicit_source,
                                 oracle_text=future_cache.script(("ValueError",)),
                                 inventory=future_cache.CASE_SPECS)["status"],"QUALIFIED")
        forbidden=copy.deepcopy(stricter)
        forbidden["expectations"][5]["allowed_exceptions"]=["TypeError"]
        result=qualify(forbidden,source=explicit_source,
                       oracle_text=future_cache.script(("TypeError",)),
                       inventory=future_cache.CASE_SPECS)
        self.assertEqual(result["status"],"NOT QUALIFIED")

    def test_missing_material_unsupported_citation_unknown_disagreement_and_tamper(self):
        for change in ("missing", "extra", "duplicate", "bad-cases", "wrong-clause",
                       "wrong-source", "wrong-oracle", "unknown", "disputed",
                       "narrow-invalid", "broad-invalid", "missing-ambiguity",
                       "unsupported-exception", "missing-author"):
            with self.subTest(change=change):
                spec=declaration()
                row=spec["expectations"][5]
                if change=="missing":
                    spec["expectations"].pop()
                elif change=="extra":
                    spec["expectations"].append({
                        "id":"unreviewed","kind":"negative","cases":["secret"],
                        "claim":"unreviewed"})
                elif change=="duplicate":
                    spec["expectations"].append(copy.deepcopy(row))
                elif change=="bad-cases":
                    row["cases"].append("extra assertion")
                elif change=="wrong-clause":
                    row["source_clause"]="No such original-source clause"
                elif change=="wrong-source":
                    spec["source_sha256"]="0"*64
                elif change=="wrong-oracle":
                    spec["oracle_sha256"]="f"*64
                elif change=="unknown":
                    row["support"]="unknown"
                elif change=="disputed":
                    row["support"]="disputed"
                elif change=="narrow-invalid":
                    row["allowed_exceptions"]=["ValueError"]
                elif change=="broad-invalid":
                    row["allowed_exceptions"]=["ValueError","TypeError","RuntimeError"]
                elif change=="missing-ambiguity":
                    row["ambiguity"]=""
                elif change=="unsupported-exception":
                    row["acceptable_alternatives"]=["ValueError","TypeError","RuntimeError"]
                elif change=="missing-author":
                    spec.pop("author")
                result=qualify(spec,source=future_cache.SOURCE,
                               oracle_text=future_cache.script(),
                               inventory=future_cache.CASE_SPECS)
                self.assertEqual(result["status"],"NOT QUALIFIED",change)
                self.assertEqual(result["model_dispatches"],0)
                self.assertTrue(result["problems"])

    def test_adjudicated_requires_separate_reviewer_and_supported_decision(self):
        spec=declaration()
        row=spec["expectations"][2]
        row.update(support="adjudicated",source_clause=None,
                   ambiguity="Interpretation not textually entailed",
                   acceptable_alternatives=["A","B"],
                   adjudication={"decision":"supported","reviewer":"independent audit",
                                 "reference":"independent written decision 001",
                                 "rationale":"Recorded scope excludes implementation-specific outputs"})
        self.assertEqual(qualify(spec,source=future_cache.SOURCE,
                                oracle_text=future_cache.script(),
                                inventory=future_cache.CASE_SPECS)["status"],"QUALIFIED")
        for decision,reviewer in (("disputed","independent audit"),
                                  ("supported","fixture author"),("unknown","reviewer")):
            with self.subTest(decision=decision, reviewer=reviewer):
                bad=copy.deepcopy(spec)
                bad["expectations"][2]["adjudication"].update(decision=decision,reviewer=reviewer)
                self.assertEqual(qualify(bad,source=future_cache.SOURCE,
                                        oracle_text=future_cache.script(),
                                        inventory=future_cache.CASE_SPECS)["status"],"NOT QUALIFIED")

    def test_qualification_stops_before_oracle_execution(self):
        bad=declaration()
        bad["expectations"][5]["allowed_exceptions"]=["ValueError"]
        with tempfile.TemporaryDirectory() as folder,patch.object(
                future_cache.grader,"invoke",side_effect=AssertionError("must not execute")):
            dest=Path(folder)/"grade"
            result=future_cache.grade(Path(folder)/"unused",bad,dest)
            self.assertEqual(result["status"],"NOT QUALIFIED")
            self.assertIsNone(result["correct"])
            self.assertEqual(result["model_dispatches"],0)
            self.assertFalse((dest/"oracle").exists())
            self.assertEqual(json.loads((dest/"qualification.json").read_text())["status"],
                             "NOT QUALIFIED")

    def test_oracle_unknown_receipts_are_not_false_acceptances(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(future_cache.grader,"invoke",return_value={
                    "available":False,"receipt":{} }):
                result=future_cache.grade(Path(folder)/"unused",declaration(),
                                          Path(folder)/"grade")
            self.assertEqual(result["status"],"ORACLE UNAVAILABLE")
            self.assertIsNone(result["correct"])
            self.assertIsNone(result["repository_tests_passed"])


class FutureCacheControls(unittest.TestCase):
    def product(self, root, variant="reference"):
        return corpus.seed("cache-expiry",root/"seed",variant)

    def test_reference_alternative_and_deliberate_defects(self):
        with tempfile.TemporaryDirectory(prefix="issue36-control-") as folder:
            root=Path(folder)
            cases=("reference","alternative","defective","coverage-gap",
                   "accepts-bool","arbitrary-exception","early-loader")
            for variant in cases:
                with self.subTest(variant=variant):
                    directory=root/variant
                    product=self.product(directory,variant if variant in
                                         ("reference","defective","coverage-gap") else "reference")
                    implementation=product/"cache.py"
                    code=implementation.read_text()
                    if variant=="alternative":
                        self.assertIn("raise ValueError('ttl')",code)
                        code=code.replace("raise ValueError('ttl')","raise TypeError('ttl')")
                    if variant=="accepts-bool":
                        code=code.replace("type(ttl) not in (int,float)",
                                          "not isinstance(ttl,(int,float))")
                    if variant=="arbitrary-exception":
                        code=code.replace("raise ValueError('ttl')","raise RuntimeError('ttl')")
                    if variant=="early-loader":
                        code=code.replace("if ttl is not None and",
                                          "loader()\n        if ttl is not None and")
                    implementation.write_text(code)
                    grade=future_cache.grade(product,declaration(),directory/"grade")
                    correct=variant in ("reference","alternative")
                    self.assertEqual(grade["status"],"PASSED" if correct else "FAILED",
                                     grade.get("cases"))
                    self.assertEqual(grade["correct"],correct)
                    self.assertEqual(grade["repository_tests_status"],"PASSED")
                    self.assertTrue(grade["repository_tests_passed"])
                    self.assertEqual(grade["model_dispatches"],0)
                    self.assertEqual(len(grade["cases"]),11)
                    receipt=grade["repository_tests_receipt"]
                    self.assertEqual(receipt["exit_code"],0)
                    self.assertEqual(receipt["argv"][1:],
                        ["-B","-m","unittest","discover","-s","tests"])
                    self.assertEqual(receipt["cwd"],str((directory/"grade/oracle/inputs/product").resolve()))
                    self.assertEqual(grade["qualification"]["status"],"QUALIFIED")
                    if variant=="arbitrary-exception":
                        self.assertFalse(next(case for case in grade["cases"]
                            if case["label"]=="reject TTL True")["passed"])
                    if variant=="early-loader":
                        self.assertFalse(next(case for case in grade["cases"]
                            if case["label"]=="reject TTL True")["passed"])

    def test_original_suite_failure_preserves_argv_status_and_receipt(self):
        with tempfile.TemporaryDirectory(prefix="issue36-suite-") as folder:
            root=Path(folder)
            product=self.product(root)
            original=(product/"tests/test_existing.py").read_text()
            (product/"tests/test_existing.py").write_text(
                original+"\nclass Broken(unittest.TestCase):\n"
                         "    def test_intentional_failure(self):\n"
                         "        self.fail('intentional repository test failure')\n")
            grade=future_cache.grade(product,declaration(),root/"grade")
            self.assertEqual(grade["status"],"PASSED")
            self.assertTrue(grade["correct"]) # Behavioral oracle is independent.
            self.assertEqual(grade["repository_tests_status"],"FAILED")
            self.assertFalse(grade["repository_tests_passed"])
            receipt=grade["repository_tests_receipt"]
            self.assertNotEqual(receipt["exit_code"],0)
            self.assertIn("intentional repository test failure",receipt["stderr"])
            self.assertEqual(receipt["argv"][1:],
                             ["-B","-m","unittest","discover","-s","tests"])
            self.assertEqual(receipt["cwd"],str((root/"grade/oracle/inputs/product").resolve()))
            self.assertEqual(grade["model_dispatches"],0)

    def test_explicit_valueerror_allows_reference_but_rejects_typeerror(self):
        source=future_cache.SOURCE + b"\nInvalid TTL must raise ValueError.\n"
        with tempfile.TemporaryDirectory(prefix="issue36-explicit-") as folder:
            root=Path(folder)
            manifest=declaration(source,("ValueError",),explicit=True)
            reference=self.product(root/"reference")
            alternative=self.product(root/"alternative")
            impl=alternative/"cache.py"
            impl.write_text(impl.read_text().replace("raise ValueError('ttl')",
                                                    "raise TypeError('ttl')"))
            green=future_cache.grade(reference,manifest,root/"reference-grade",source=source)
            red=future_cache.grade(alternative,manifest,root/"alternative-grade",source=source)
            self.assertEqual(green["status"],"PASSED")
            self.assertEqual(red["status"],"FAILED")
            self.assertFalse(red["correct"])
            self.assertEqual(green["qualification"]["status"],"QUALIFIED")
            self.assertEqual(red["qualification"]["status"],"QUALIFIED")


if __name__=="__main__":
    unittest.main()
