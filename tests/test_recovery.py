"""Offline controls and spending-gate regressions; never dispatch a model."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.recovery import corpus, grader, probes, oracle
from evaluation.recovery import report, study


class RecoveryControls(unittest.TestCase):
    def test_all_predeclared_controls(self):
        with tempfile.TemporaryDirectory(prefix="issue34-controls-") as folder:
            result = grader.controls(Path(folder))
        self.assertTrue(result["all_matched"],[
            (r["task"],r["variant"],r["hidden"]["cases"])
            for r in result["controls"] if not r["matched"]])
        self.assertEqual(len(result["controls"]),24)
        self.assertEqual(result["model_dispatches"],0)

    def test_sources_and_programs_compile(self):
        self.assertEqual(set(corpus.REQUESTS),set(probes.PUBLIC))
        self.assertEqual(set(corpus.REQUESTS),set(oracle.HIDDEN))
        for task, source in corpus.REQUESTS.items():
            for quote in probes.QUOTES[task]:
                self.assertIn(quote,source)
            compile(probes.script(task),"public","exec")
            compile(oracle.script(task),"hidden","exec")
            for variant in (None,"reference","alternative","defective","coverage-gap"):
                for filename, text in corpus.files(task,variant).items():
                    compile(text,filename,"exec")


class RecoveryStudy(unittest.TestCase):
    def test_gate_and_all_assigned_denominator(self):
        rows=study.ledger()
        self.assertEqual(len(rows),24)
        self.assertEqual([r["arm"] for r in rows[:6]],["A"]*6)
        with self.assertRaises(ValueError): report.baseline_gate(rows)
        for row in rows[:6]:
            row["initial_grade"]={"available":True,"correct":True}
            row["final_grade"]=row["initial_grade"]
            row["status"]="CORRECT_DELIVERY"
            row["total_seconds"]=1
        self.assertFalse(report.baseline_gate(rows)["continue"])
        rows[0]["initial_grade"]["correct"]=False
        self.assertFalse(report.baseline_gate(rows)["continue"])
        rows[1]["initial_grade"]["correct"]=False
        self.assertTrue(report.baseline_gate(rows)["continue"])
        metrics=report.summarize(rows)
        self.assertEqual(metrics["arms"]["B"]["assigned"],6)
        self.assertEqual(metrics["arms"]["B"]["outcomes"],{"NOT_EXECUTED":6})
        self.assertEqual(metrics["recommendations"]["Proofline"],"INCONCLUSIVE")
        self.assertEqual(metrics["paired"],{})

    def test_execute_stops_after_all_baselines_or_runs_all_cells(self):
        for defects,expected,status in ((0,6,"EARLY_STOP_CORRECTNESS_CEILING"),
                                        (1,6,"EARLY_STOP_CORRECTNESS_CEILING"),
                                        (2,24,"COMPLETED")):
            with tempfile.TemporaryDirectory() as folder:
                store=Path(folder)
                rows=study.ledger()
                for row in rows: row["seed"]=str(store/"assignment/seed/product")
                (store/"results.json").write_text(json.dumps({
                    "status":"QUALIFIED_NOT_DISPATCHED","assignments":rows}))
                calls=[]
                def episode(row,*args):
                    calls.append((row["task"],row["arm"]))
                    correct=not (row["arm"]=="A" and len(calls)<=defects)
                    row.update(initial_grade={"available":True,"correct":correct},
                        final_grade={"available":True,"correct":correct},total_seconds=1,
                        status="CORRECT_DELIVERY" if correct else "FALSE_ACCEPTANCE")
                with patch.object(study,"STORE",store),patch.object(study,"approved"),patch.object(
                    study,"verify",return_value={"assignments":[{}]*24}),patch.object(study,"episode",side_effect=episode):
                    study.execute()
                result=json.loads((store/"results.json").read_text())
                self.assertEqual(len(calls),expected)
                self.assertEqual(result["status"],status)
                self.assertEqual(len(set(calls)),expected)

    def test_green_or_unqualified_checks_never_dispatch_sol_or_correction(self):
        from checks import host_probe as host
        for arm in ("B","C","D"):
            with tempfile.TemporaryDirectory() as folder:
                folder=Path(folder)
                task="report-columns"
                seed=study.runner.initialize(task,folder/"seed","reference")
                frozen={"seed_tree":host.git(seed,"rev-parse","HEAD^{tree}"),
                        "source_sha256":host.sha256(corpus.REQUESTS[task].encode()),"checks":study.checks(task)}
                row={"task":task,"arm":arm,"seed":str(seed),"stages":[],"checks":[],"correction":{"attempted":False}}
                (folder/"episode").mkdir()
                def implement(*args,**kwargs):
                    self.assertEqual(args[5],[]) # No public probes before initial capture.
                    kwargs["on_dispatch"]()
                    return {"candidate":str(seed),"accepted":True,"stages":[{"status":"OBSERVED"}]}
                record={"status":"CHECKS PASSED","elapsed_seconds":1,"observations":[{"status":"PASSED"},{"status":"PASSED"}]}
                with patch.object(study,"verify"),patch.object(study.runner,"implement",side_effect=implement),patch.object(
                    study.runner,"checked",return_value=record),patch.object(study,"ordinary",return_value=record),patch.object(
                    study.runner,"correction_allowed",return_value=False),patch.object(study,"ordinary_allowed",return_value=False),patch.object(
                    grader,"grade",return_value={"available":True,"correct":False}),patch.object(
                    study.runner,"advisory") as advisory,patch.object(study.runner,"recover_stages"):
                    study.episode(row,frozen,folder/"episode",lambda:None)
                advisory.assert_not_called()
                self.assertFalse(row["correction"]["attempted"])
                self.assertEqual(len(row["stages"]),1)
                self.assertFalse(row["initial_grade"]["correct"])

    def test_live_spending_requires_this_fresh_freeze(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(study,"STORE",Path(folder)),patch.object(
                study,"identities",return_value={"freeze_sha256":"fresh"}):
                with self.assertRaises(ValueError): study.approved()
                approval={"freeze_sha256":"old","study_id":study.protocol()["study_id"],
                    "max_native_dispatches":48,"max_seconds":28800,"user_authorization":"yes"}
                (Path(folder)/"approval.json").write_text(json.dumps(approval))
                with self.assertRaises(ValueError): study.approved()
                approval["freeze_sha256"]="fresh"
                (Path(folder)/"approval.json").write_text(json.dumps(approval))
                self.assertEqual(study.approved(),approval)

    def test_qualified_defect_uses_one_original_thread_correction(self):
        from checks import host_probe as host
        for arm in ("B","C","D"):
            with tempfile.TemporaryDirectory() as folder:
                folder=Path(folder); task="report-columns"
                seed=study.runner.initialize(task,folder/"seed","reference")
                (folder/"episode").mkdir()
                frozen={"seed_tree":host.git(seed,"rev-parse","HEAD^{tree}"),
                    "source_sha256":host.sha256(corpus.REQUESTS[task].encode()),"checks":study.checks(task)}
                row={"task":task,"arm":arm,"seed":str(seed),"stages":[],"checks":[],"correction":{"attempted":False}}
                turns=[]
                def implement(*args,**kwargs):
                    turns.append(kwargs.get("session_id"))
                    if len(turns)==1: self.assertEqual(args[5],[])
                    else:
                        self.assertEqual(args[5],study.checks(task))
                        self.assertNotIn("initial_grade",kwargs["guidance"])
                    kwargs["on_dispatch"]()
                    return {"candidate":str(seed),"accepted":True,
                        "stages":[{"status":"OBSERVED","thread_id":"original","receipt":{}}]}
                def checked(*args,**kwargs):
                    failed=len(turns)==1
                    return {"status":"CHECKS FAILED" if failed else "CHECKS PASSED",
                        "elapsed_seconds":1,"feedback":{"public":"assertion"},
                        "observations":[{"status":"FAILED" if failed else "PASSED"},{"status":"PASSED"}]}
                diagnosis={"status":"OBSERVED","report":{"findings":[]}}
                with patch.object(study,"verify"),patch.object(study.runner,"implement",side_effect=implement),patch.object(
                    study.runner,"checked",side_effect=checked),patch.object(study,"ordinary",side_effect=checked),patch.object(
                    study.runner,"correction_allowed",return_value=True),patch.object(study,"ordinary_allowed",return_value=True),patch.object(
                    grader,"grade",side_effect=[{"available":True,"correct":False},{"available":True,"correct":True}]),patch.object(
                    study.live,"reconcile_worker"),patch.object(study.live,"read_events",return_value={"thread_id":"original"}),patch.object(
                    study.runner,"advisory",return_value=diagnosis) as advisory,patch.object(
                    study.runner,"review_valid",return_value=True),patch.object(study.runner,"recover_stages"):
                    study.episode(row,frozen,folder/"episode",lambda:None)
                self.assertEqual(turns,[None,"original"])
                self.assertEqual(advisory.call_count,int(arm=="D"))
                self.assertTrue(row["correction"]["attempted"])
                self.assertEqual(row["reserved_native_dispatches"],3 if arm=="D" else 2)
                self.assertEqual(row["status"],"CORRECT_DELIVERY")
