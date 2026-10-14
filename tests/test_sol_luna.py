"""Offline controls and simulated transport regressions; never efficacy evidence."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import zipfile
from unittest.mock import patch

from checks import candidate_snapshot as snapshots
from evaluation.sol_luna import corpus, grader, report, study


def stage(role, model, thread="worker", status="OBSERVED"):
    return {"stage": role, "model": "gpt-6.1-sol" if model == "sol" else "gpt-6-luna",
            "status": status, "reasoning_effort": "high", "elapsed_seconds": 1,
            "receipt": {}, "thread_id": thread, "usage": {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 10},
            "tool_executions": 2, "cost_usd": None}


class SolLunaPreparation(unittest.TestCase):
    def test_frozen_sources_and_preparation_record_are_exact_and_unexecuted(self):
        frozen = json.loads((study.HERE/'FREEZE.json').read_text())
        destination = study.ROOT/'evaluation/results/issue32-preparation'
        # Published runtime bytes stay pinned in the archive while the supported CLI evolves.
        with zipfile.ZipFile(destination/'frozen-source.zip') as archive:
            for name,digest in frozen['sha256'].items():
                self.assertEqual(study.host.sha256(archive.read(name)),digest,name)
            self.assertEqual(archive.read('evaluation/sol_luna/FREEZE.json'),(study.HERE/'FREEZE.json').read_bytes())
        record = json.loads((destination/'results.json').read_text())
        self.assertEqual(record['status'],'STOPPED')
        self.assertEqual(record['model_dispatches'],0)
        self.assertTrue(all(r['status']=='NOT_EXECUTED' for r in record['assignments']))
        self.assertEqual(record['metrics'],report.summarize(record['assignments']))
        controls = json.loads((destination/'offline-controls.json').read_text())
        self.assertTrue(controls['all_matched'])
        self.assertEqual(len(controls['controls']),17)
        for name,digest in json.loads((destination/'hashes.json').read_text()).items():
            self.assertEqual(study.host.sha256((destination/name).read_bytes()),digest,name)

    def test_bundle_retains_aliases_without_reading_targets_or_native_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root/'store'; store.mkdir()
            (store/'result.json').write_text('{}')
            (root/'outside').write_text('private content must never enter evidence')
            (store/'alias').symlink_to(root/'outside')
            (store/'catalog-state').mkdir()
            (store/'catalog-state/ignored').write_text('private native state')
            (root/'FREEZE.json').write_text(json.dumps({'sha256':{}}))
            (root/'LICENSE').write_text('test fixture license')
            with patch.object(study,'STORE',store), patch.object(study,'HERE',root), \
                 patch.object(study.infrastructure,'PRODUCER',root), \
                 patch.object(study.infrastructure,'producer_files',return_value={}):
                study.publish_record(root/'bundle')
            with zipfile.ZipFile(root/'bundle/raw-evidence.zip') as archive:
                self.assertEqual(set(archive.namelist()), {'result.json','alias'})
                self.assertEqual(archive.read('alias').decode(),str(root/'outside'))
                self.assertEqual(archive.getinfo('alias').external_attr >> 16,0o120777)
            self.assertTrue((root/'bundle/hashes.json').is_file())

    def test_interrupted_launch_keeps_unknown_model_cost_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            private=root/'coding/implementation/private'; private.mkdir(parents=True)
            (private/'worker.json').write_text(json.dumps({'state':'running','pid':123}))
            row={'arm':'luna','stages':[]}
            study.recover_stages(root,row)
            study.recover_stages(root,row)
        self.assertEqual(len(row['stages']),1)
        self.assertEqual(row['stages'][0]['model'],'gpt-6-luna')
        self.assertIsNone(row['stages'][0]['usage'])
        self.assertIsNone(row['stages'][0]['elapsed_seconds'])
        self.assertEqual(row['stages'][0]['status'],'NOT VERIFIED')

    def test_catalog_readback_parses_native_rpc_without_creating_a_turn(self):
        code = '''import json,sys
first=json.loads(sys.stdin.readline())
assert first['method']=='initialize'
print(json.dumps({'id':1,'result':{}}),flush=True)
assert json.loads(sys.stdin.readline())['method']=='initialized'
assert json.loads(sys.stdin.readline())['method']=='model/list'
models=[{'id':m,'model':m,'supportedReasoningEfforts':[{'reasoningEffort':'high'}]} for m in ('gpt-6.1-sol','gpt-6-luna')]
print(json.dumps({'id':2,'result':{'data':models}}),flush=True)
'''
        native_popen = subprocess.Popen
        def fake(argv, **kwargs):
            self.assertIn('app-server', argv)
            self.assertFalse(any('exec' == a for a in argv))
            return native_popen([sys.executable,'-I','-B','-c',code],**kwargs)
        with tempfile.TemporaryDirectory() as temporary, patch.object(study.subprocess,'Popen',side_effect=fake):
            result = study.catalog_readback(Path(temporary))
        self.assertEqual(result['status'],'OBSERVED')
        self.assertEqual(result['model_dispatches'],0)

    def test_deleted_required_cli_is_an_observed_product_defect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            product=corpus.seed('path-router',root/'seed','reference')
            (product/'cli.py').unlink()
            grade=grader.grade(product,'path-router',root/'grading',trusted=True)
            self.assertTrue(grade['available'])
            self.assertFalse(grade['correct'])

    def test_twenty_matched_slots_and_exact_models(self):
        rows = study.ledger()
        self.assertEqual(len(rows), 20)
        self.assertEqual({(r["task"], r["arm"]) for r in rows}, {(t,a) for t in corpus.REQUESTS for a in report.ARMS})
        for arm in report.ARMS:
            self.assertEqual(len({(r["sequence"]-1)%5 for r in rows if r["arm"] == arm}), 4)
        catalog = json.loads((study.HERE / "model-catalog.json").read_text())
        study.validate_models(catalog)
        with self.assertRaisesRegex(ValueError, "unavailable"):
            study.validate_models({"models": [m for m in catalog["models"] if m["slug"] != "gpt-6-luna"]})
        for model in ("sol", "luna"):
            args = study.live.command(study.CODEX, Path('/inputs'), Path('/scratch'), Path('/private'), study.preferences(model), implementer=True)
            self.assertIn('model_reasoning_effort="high"', args)
            self.assertIn('model_catalog_json='+study.host.toml(str(study.HERE/'model-catalog.json')), args)
        metrics = report.summarize(rows)
        self.assertEqual(metrics["executed"], 0)
        self.assertEqual(metrics["empirical_acceptance"], "INCOMPLETE")
        self.assertIsNone(metrics["paired_effects"])

    def test_independent_controls_reject_green_test_defects(self):
        result = grader.controls()
        self.assertTrue(result["all_matched"], result)
        self.assertEqual(len(result["controls"]), 17)
        for row in result["controls"]:
            self.assertTrue(row["grade"]["repository_tests_passed"])
            self.assertEqual(row["grade"]["correct"], row["variant"] in ("reference", "alternative"))
            if row["variant"] == "missing-batch":
                self.assertTrue(all(f["seam"] == "batch" for f in row["grade"]["failures"]))

    def test_spending_requires_exact_authorization(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(study, 'STORE', Path(temporary)), patch.object(study, 'identities', return_value={"freeze_sha256": "frozen"}):
            with self.assertRaisesRegex(ValueError, "Explicit authorization"):
                study.approved()
            value = {"freeze_sha256": "different", "study_id": study.protocol()["study_id"],
                "max_native_dispatches": 48, "max_seconds": 18360, "user_authorization": "test-only simulated approval"}
            (study.STORE/'approval.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "Explicit authorization"):
                study.approved()
            value['freeze_sha256'] = 'frozen'
            (study.STORE/'approval.json').write_text(json.dumps(value))
            self.assertEqual(study.approved(), value)

    def test_review_is_independent_and_never_sees_plan_or_grade(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product = study.initialize('path-router', root/'seed', 'reference')
            record = {"status": "CHECKS PASSED", "candidate_tree": study.host.git(product,'rev-parse','HEAD^{tree}'),
                "source_sha256": "source", "checks": [], "observations": [], "evidence_sha256": "bound",
                "intentline_advisory": {"secret_plan_marker": True}, "grade": {"private_expected_marker": True}}
            def observe(*args, **kwargs):
                inputs = args[2]
                text = kwargs['make_prompt']('reviewer', inputs, {}, 'canary')
                self.assertIn('COMPLETE original request', text)
                self.assertIn('No earlier plan', text)
                self.assertIn('receipt-bound', text)
                all_text = ''.join(p.read_text() for p in inputs.glob('*.json'))
                self.assertNotIn('secret_plan_marker', all_text)
                self.assertNotIn('private_expected_marker', all_text)
                self.assertFalse((inputs/'tool').exists())
                return stage('verification','sol')
            with patch.object(study.live,'run_stage',side_effect=observe):
                study.advisory('verification', corpus.REQUESTS['path-router'], product, root/'review', 30, [], record)

    def test_speculation_missing_checks_and_mutated_candidates_cannot_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product = study.initialize('path-router', root/'seed', 'defective')
            checks = study.selected_checks('path-router')
            record = {"checks": checks, "candidate_tree": study.host.git(product,'rev-parse','HEAD^{tree}'),
                "observations": [{"status":"PASSED"},{"status":"FAILED"}]}
            with patch.object(study.local_run,'actionable_failure',return_value=True):
                self.assertFalse(study.correction_allowed(record,root,checks,product))
                record['observations'][0]['status'] = 'FAILED'
                self.assertTrue(study.correction_allowed(record,root,checks,product))
                record['candidate_tree'] = 'different'
                self.assertFalse(study.correction_allowed(record,root,checks,product))
            record['candidate_tree'] = study.host.git(product,'rev-parse','HEAD^{tree}')
            with patch.object(study.local_run,'actionable_failure',return_value=False):
                self.assertFalse(study.correction_allowed(record,root,checks,product))
        source = corpus.REQUESTS['path-router']
        review = {"report":{"summary":"advice", "findings":[{"quote":"invented requirement", "defect":"speculation", "check_indices":[]}]}}
        self.assertFalse(study.review_valid(review, source, 2))


class SolLunaExecution(unittest.TestCase):
    def simulate(self, *, fail_transport=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        rows = study.ledger()
        frozen = []
        for row in rows:
            seed = study.initialize(row['task'], root/f"{row['sequence']:02d}-{row['task']}-{row['arm']}"/'seed')
            row['seed'] = str(seed)
            frozen.append({"source_sha256": study.host.sha256((seed.parent/'source.md').read_bytes()),
                "seed_tree": study.host.git(seed,'rev-parse','HEAD^{tree}'), "checks": study.selected_checks(row['task'])})
        (root/'results.json').write_text(json.dumps({"status":"QUALIFIED_NOT_DISPATCHED","assignments":rows}))
        manifest = {"assignments": frozen, "protocol": study.protocol()}
        dispatched = []
        def implement(source, seed, directory, model, seconds, checks, **kwargs):
            self.assertLessEqual(seconds,600)
            self.assertNotIn('initial_grade', kwargs.get('guidance', {}))
            correction = kwargs.get('session_id') is not None
            if correction:
                self.assertTrue(kwargs['guidance']['Sol_advice_not_proof'])
                self.assertEqual(kwargs['guidance']['Sol_advice_not_proof'][0]['check_indices'],[0])
            if kwargs.get('on_dispatch'): kwargs['on_dispatch']()
            inputs = directory/'inputs'; inputs.mkdir(parents=True)
            snapshots.capture_base(seed,inputs/'product')
            task = next(t for t,s in corpus.REQUESTS.items() if s == source)
            defect = task=='path-router' and seed.parent.parent.name.endswith(('-verify','-hybrid')) and not correction
            (inputs/'product/app.py').write_text(corpus.candidate(task,defective=defect))
            (inputs/'product/service.py').write_text(corpus.previous.SERVICE)
            snapshots.freeze(inputs/'product')
            thread = kwargs.get('session_id') or 'original-'+str(directory)
            s = stage('correction' if correction else 'implementation',model,thread,
                      'NOT VERIFIED' if fail_transport else 'OBSERVED')
            dispatched.append((task,model,correction,thread))
            return {"accepted":True,"candidate":str(inputs/'product'),"stages":[s]}
        def advisory(role, source, product, directory, seconds, checks, check_record=None):
            self.assertLessEqual(seconds,120)
            value = stage(role,'sol')
            value['report'] = {"summary":"simulated advisory review","findings":[{
                "quote":source.splitlines()[0],"defect":"Diagnose the concrete public assertion failure","check_indices":[0]}]}
            return value
        def check(product, source, checks, directory, **kwargs):
            directory.mkdir()
            failed = 'path-router' in str(product) and any(a in str(product) for a in ('-verify','-hybrid')) and '/coding/' in str(product)
            record = {"status":"CHECKS FAILED" if failed else "CHECKS PASSED", "model_dispatches":0,
                "checks":checks,"candidate_tree":study.host.git(product,'rev-parse','HEAD^{tree}'),
                "feedback":{},"observations":[{"status":"FAILED" if failed else "PASSED"},{"status":"PASSED"}],
                "elapsed_seconds":1}
            (directory/'report.json').write_text(json.dumps(record))
            return record
        def grade(product, task, directory, **kwargs):
            failed = task=='path-router' and any(a in str(product) for a in ('-verify','-hybrid')) and '/coding/' in str(product)
            return {"available":True,"correct":not failed,"repository_tests_passed":True}
        with ExitStack() as patches:
            replacements = [(study,'STORE',root),(study,'approved',lambda: {}),(study,'verify',lambda:manifest),
                (study,'handoff_control',lambda:None),(study,'implement',implement),(study,'advisory',advisory),
                (study.grader,'grade',grade),(study.local_run,'check',check),
                (study.local_run,'inspect',lambda p:json.loads(p.read_text())),
                (study.local_run,'actionable_failure',lambda *args:True),
                (study.live,'reconcile_worker',lambda *args: {}),
                (study.live,'read_events',lambda receipt:{"thread_id":'original-'+receipt['directory']})]
            # Simulated native stage identity readback, without an actual model.
            original_implement = implement
            def identified(*args, **kwargs):
                r = original_implement(*args, **kwargs)
                r['stages'][0]['receipt'] = {"directory":str(args[2])}
                return r
            replacements[4] = (study,'implement',identified)
            for owner,name,value in replacements: patches.enter_context(patch.object(owner,name,value))
            patches.enter_context(patch.object(study.adapter,'load_export',side_effect=ValueError('invalid worker export')))
            patches.enter_context(patch('builtins.print'))
            if fail_transport:
                with self.assertRaisesRegex(ValueError,'native advisory model'):
                    study.execute()
            else:
                study.execute()
        return json.loads((root/'results.json').read_text()), dispatched

    def test_all_five_arms_correct_once_preserve_initial_grades_and_invalid_advice(self):
        result, calls = self.simulate()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(len(calls),22)
        self.assertEqual(sum(c[1]=='sol' for c in calls),4)
        corrected = [r for r in result['assignments'] if r['correction']['attempted']]
        self.assertEqual(len(corrected),2)
        for row in corrected:
            self.assertFalse(row['initial_grade']['correct'])
            self.assertTrue(row['final_grade']['correct'])
            self.assertEqual(len(row['checks']),2)
            self.assertNotEqual(row['initial_candidate']['tree'],row['final_candidate']['tree'])
            impl = [s for s in row['stages'] if s['stage'] in ('implementation','correction')]
            self.assertEqual(impl[0]['thread_id'],impl[1]['thread_id'])
        self.assertTrue(all(r['status']=='CORRECT_DELIVERY' for r in result['assignments']))
        self.assertEqual(sum(r.get('plan_status')=='MISSING_OR_INVALID' for r in result['assignments']),8)
        self.assertEqual(sum(len(r['checks']) for r in result['assignments']),10)
        self.assertEqual(sum(len(r['stages']) for r in result['assignments']),38)
        self.assertEqual(result['metrics']['cost_effectiveness'],'INCONCLUSIVE')

    def test_native_failure_stops_and_preserves_usage_and_missing_slots(self):
        result, calls = self.simulate(fail_transport=True)
        self.assertEqual(result['status'],'STOPPED')
        self.assertEqual(len(calls),1)
        self.assertEqual(result['assignments'][0]['status'],'UNAVAILABLE')
        self.assertEqual(result['assignments'][0]['stages'][0]['usage']['input_tokens'],100)
        self.assertEqual(sum(r['status']=='NOT_EXECUTED' for r in result['assignments']),19)
        self.assertIsNone(result['metrics']['paired_effects'])


class SolLunaAccounting(unittest.TestCase):
    def test_cached_usage_is_a_subset_and_unknown_usage_and_prices_remain_unknown(self):
        rows = study.ledger()
        rows[0].update(status='FALSE_ACCEPTANCE', stages=[stage('implementation','luna')],
            initial_grade={"correct":False}, final_grade={"correct":False}, total_seconds=3)
        metrics = report.summarize(rows)
        m = metrics['arms'][rows[0]['arm']]['models']['gpt-6-luna']
        self.assertEqual(m['tokens'], {"input_tokens":100,"cached_input_tokens":80,"output_tokens":10})
        self.assertIsNone(metrics['arms'][rows[0]['arm']]['total_cost_usd'])
        rows[0]['stages'][0]['usage'] = None
        self.assertIsNone(report.summarize(rows)['arms'][rows[0]['arm']]['models']['gpt-6-luna']['tokens']['input_tokens'])
        with self.assertRaisesRegex(ValueError,'every unique'):
            report.summarize(rows[:-1])

    def test_all_first_pass_ceiling_does_not_claim_success_or_monetary_savings(self):
        rows = study.ledger()
        for row in rows:
            row.update(status='CORRECT_DELIVERY', initial_grade={"correct":True}, final_grade={"correct":True},
                stages=[stage('implementation','luna')], total_seconds=3,workflow_seconds=2,grading_seconds=1)
        metrics = report.summarize(rows)
        self.assertTrue(metrics['ceiling_effect'])
        self.assertEqual(metrics['cost_effectiveness'],'INCONCLUSIVE')
        self.assertEqual(metrics['paired_effects']['hybrid_vs_sol']['final_delivery']['percentage_points'],0)
        self.assertTrue(all(v.startswith('SIMPLIFY') for v in metrics['recommendations'].values()))


if __name__ == '__main__':
    unittest.main()
