import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks import local_run as runner
from checks import candidate_snapshot


class BoundedRun(unittest.TestCase):
    def exercise(self,checks,completed=True,unavailable=False,simulate_timeout=False,
                 mutate_candidate=False,boundary_ready=True,model_usage=None, failure_details=None,
                 correct_once=False, correction_case=None, receipt_changes=None):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);repo=root/'source';repo.mkdir()
        (repo/'tiny.py').write_text('print("ok")\n')
        runner.host.git(repo,'init','--quiet','--template=');candidate_snapshot.freeze(repo)
        def boundary(codex,directory,inputs,*args):
            for name in ('canary.py','canary.json'):(inputs/name).write_text('canary')
            ready=boundary_ready and not (correction_case=='boundary-unavailable' and 'correction' in inputs.parts)
            return {'assessment':{'status':'OBSERVED' if ready else 'NOT VERIFIED'}}
        def oracle(codex,inputs,private,receipts):
            def execute(argv,*,cwd,timeout):
                if unavailable:raise OSError('native execution unavailable')
                if simulate_timeout:raise subprocess.TimeoutExpired(argv,timeout)
                if mutate_candidate:
                    (inputs/'product'/'tiny.py').write_text('print("changed")\n')
                result=subprocess.run(argv,cwd=cwd,timeout=timeout,capture_output=True,text=True)
                receipts.append({'kind':'process_probe','argv':['sandbox',json.dumps(argv)],
                                 'exit_code':result.returncode,'timed_out':False,
                                 'stdout':result.stdout,'stderr':result.stderr})
                if receipt_changes:receipts[-1].update(receipt_changes)
                return result
            return execute
        thread='11111111-1111-4111-8111-111111111111'
        launches=[]
        def launch(argv,prompt,private,timeout):
            launches.append((argv,prompt,private,timeout))
            correction='resume' in argv
            if correction_case:
                product=private.parent/'inputs'/'product'
                (product/'tiny.py').write_text('answer='+('42' if correction and correction_case!='repeated' else '0')+'\n')
            receipt={'kind':'codex_exec','exit_code':0,'timed_out':False,
                     'invocation_id':len(launches)}
            native=events(receipt)
            transcript=[{'type':'thread.started','thread_id':native['thread_id']},
                        {'type':'turn.started'},
                        {'type':'item.completed','item':{'type':'agent_message',
                            'text':json.dumps(native['report'])}},
                        {'type':'turn.completed','usage':native['usage']}]
            raw='\n'.join(json.dumps(row) for row in transcript).encode()
            (private/'events.jsonl').write_bytes(raw)
            (private/'stderr.txt').write_bytes(b'')
            receipt.update(events_path=str(private/'events.jsonl'),
                           **{'events.jsonl_sha256':runner.host.sha256(raw),
                              'stderr.txt_sha256':runner.host.sha256(b'')})
            runner.live.save_worker(private,{'state':'finished','receipt':receipt})
            if correction and correction_case=='interrupt':raise KeyboardInterrupt()
            return receipt
        def events(receipt):
            return {'thread_id':('22222222-2222-4222-8222-222222222222'
                    if receipt['invocation_id']==2 and correction_case=='wrong-thread' else thread),
                    'usage':model_usage,'commands':{},
                    'report':{'completed':completed and not (receipt['invocation_id']==2 and correction_case=='incomplete'),
                              'summary':'Self-report, not acceptance'}}
        with patch.object(runner.platform,'system',return_value='Darwin'),\
             patch.object(runner.host,'find_codex',return_value='/fake/codex'),\
             patch.object(runner.host,'run_command',wraps=runner.host.run_command) as command,\
             patch.object(runner.live,'preferences',return_value={'model':'fixture'}),\
             patch.object(runner.host,'probe_boundary',side_effect=boundary),\
             patch.object(runner.live,'launch',side_effect=launch),\
             patch.object(runner,'oracle_runner',side_effect=oracle):
            original=command._mock_wraps
            command.side_effect=lambda argv,*args,**kw:({'stdout':'codex-cli 0.162.1','exit_code':0,'timed_out':False}
                if argv==['/fake/codex','--version'] else original(argv,*args,**kw))
            result=runner.run(repo,'Preserve the tiny program.',checks,root/'run',30,10,5,
                              failure_details=failure_details,correct_once=correct_once)
        self.assertEqual((repo/'tiny.py').read_text(),'print("ok")\n')
        self.assertEqual(result['model_dispatches'],len(launches))
        self.assertFalse(result['published']);self.assertFalse(result['merged'])
        self.launches=launches
        return result,root/'run/report.json'

    def test_check_failure_and_unavailability_are_distinct(self):
        checks=[[sys.executable,'-c','pass'],[sys.executable,'-c','raise SystemExit(3)']]
        result,_=self.exercise(checks)
        self.assertEqual(result['status'],'CHECKS FAILED')
        self.assertEqual([x['status'] for x in result['observations']],['PASSED','FAILED'])
        result,_=self.exercise(checks,unavailable=True)
        self.assertEqual(result['status'],'CHECKS UNAVAILABLE')

    def test_success_is_scoped_to_commands_and_drift_invalidates_it(self):
        result,path=self.exercise([[sys.executable,'tiny.py']])
        self.assertEqual(result['status'],'CHECKS PASSED')
        self.assertIn('not certified',result['assurance'])
        self.assertEqual(runner.inspect(path)['status'],'CHECKS PASSED')
        (Path(result['candidate_path'])/'tiny.py').write_text('print("changed")\n')
        self.assertEqual(runner.inspect(path)['status'],'STALE CHECKS')

    def test_handoff_is_not_turned_into_accepted_or_checked_delivery(self):
        result,_=self.exercise([[sys.executable,'-c','pass']],completed=False)
        self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
        self.assertEqual(result['observations'],[])

    def test_a_different_receipt_cannot_support_the_declared_check(self):
        result,path=self.exercise([[sys.executable,'-c','pass']])
        result['observations'][0]['receipts'][0]['argv'][-1]=json.dumps([sys.executable,'-c','print("different")'])
        path.write_text(json.dumps(result))
        self.assertEqual(runner.inspect(path)['status'],'STALE CHECKS')

    def test_timeout_keeps_unavailable_distinct_from_failure(self):
        result,_=self.exercise([[sys.executable,'-c','pass']],simulate_timeout=True)
        self.assertEqual(result['status'],'CHECKS UNAVAILABLE')
        self.assertEqual(result['observations'][0]['status'],'UNAVAILABLE')
        self.assertIn('timed out',result['observations'][0]['error'])
        self.assertGreaterEqual(result['observations'][0]['elapsed_seconds'],0.0)
        self.assertEqual(len(result['stages']),1)

    def test_candidate_mutation_during_check_invalidates_all_success(self):
        result,_=self.exercise([[sys.executable,'-c','pass']],mutate_candidate=True)
        self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
        self.assertIn('Frozen check inputs changed',result['error'])
        self.assertNotEqual(result['status'],'CHECKS PASSED')

    def test_preflight_failure_refuses_model_dispatch(self):
        result,_=self.exercise([[sys.executable,'-c','pass']],boundary_ready=False)
        self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
        self.assertEqual(result['model_dispatches'],0)
        self.assertEqual(result['stages'],[])
        self.assertEqual(result['observations'],[])

    def test_real_check_elapsed_and_model_usage_are_recorded(self):
        usage={'input_tokens':123,'cached_input_tokens':40,'output_tokens':7}
        result,_=self.exercise([[sys.executable,'-c','pass']],model_usage=usage)
        self.assertEqual(result['stages'][0]['usage'],usage)
        self.assertEqual(result['limits']['seconds'],30)
        self.assertEqual(result['limits']['stage_seconds'],10)
        self.assertEqual(result['limits']['check_seconds'],5)
        self.assertEqual(len(result['stages']),1)
        self.assertGreaterEqual(result['observations'][0]['elapsed_seconds'],0.0)
        self.assertGreaterEqual(result['elapsed_seconds'],
                                result['observations'][0]['elapsed_seconds'])

    def test_managed_run_feedback_and_failed_receipt_status_readback(self):
        checks = [[sys.executable, '-c',
                   'import sys;print("observed wrong",file=sys.stderr);sys.exit(4)']]
        details = [{'index': 0, 'outcome_ids': ['R3'],
                    'expected': 'correct', 'observed': 'observed wrong'}]
        result,path = self.exercise(checks, failure_details=details)
        self.assertEqual(result['status'], 'CHECKS FAILED')
        self.assertEqual(result['feedback']['checks'][0]['caller_annotation']['observed'],
                         'observed wrong')
        self.assertEqual(result['feedback']['candidate_commit'], result['candidate_commit'])
        self.assertEqual(result['feedback']['candidate_tree'], result['candidate_tree'])
        self.assertEqual(runner.inspect(path)['status'], 'CHECKS FAILED')
        receipt = path.parent / result['observations'][0]['receipt_ref']
        receipt.unlink()
        self.assertEqual(runner.inspect(path)['status'], 'STALE CHECKS')

    def test_managed_run_metadata_rejected_before_model_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                runner.run(root, 'original request', [[sys.executable,'-c','pass']],
                           root/'output', 30, 10, 5,
                           failure_details=[{'index': 0, 'expected': 'required pair'}])
            self.assertFalse((root/'output').exists())

    def test_invalid_commands_and_budgets_dispatch_nothing(self):
        for checks in ([],['echo ok'],[['']],[[True]],[['echo','\0']]):
            with self.assertRaises(ValueError):runner.validate_checks(checks)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):runner.run(Path(temporary),'request',[['echo','ok']],Path(temporary)/'run',float('nan'))

    def defect_check(self):
        return [[sys.executable,'-B','-c',
                 'from tiny import answer; assert answer == 42, "expected 42; observed %s" % answer']]

    def test_opt_in_success_does_not_dispatch_a_correction(self):
        result,path=self.exercise([[sys.executable,'tiny.py']],correct_once=True)
        self.assertEqual(result['status'],'CHECKS PASSED')
        self.assertEqual(len(self.launches),1)
        self.assertFalse(result['correction']['attempted'])
        self.assertNotIn('--ephemeral',self.launches[0][0])
        self.assertEqual(runner.inspect(path)['status'],'CHECKS PASSED')

    def test_defect_corrected_on_same_thread_and_every_check_rerun(self):
        checks=self.defect_check()+[[sys.executable,'-c','print("compatibility")']]
        result,path=self.exercise(checks,correct_once=True,correction_case='fixed')
        self.assertEqual(result['status'],'CHECKS PASSED',result)
        self.assertEqual(len(self.launches),2)
        self.assertIn('resume',self.launches[1][0])
        self.assertIn(result['stages'][0]['thread_id'],self.launches[1][0])
        self.assertEqual(result['stages'][0]['thread_id'],result['stages'][1]['thread_id'])
        guidance=Path(result['candidate_path']).parent/'guidance.md'
        evidence=json.loads(guidance.read_text())
        self.assertIn('AssertionError: expected 42; observed 0',evidence['observations'][0]['receipts'][0]['stderr'])
        self.assertEqual(evidence['checks'],checks)
        self.assertEqual((guidance.parent/'source.md').read_text(),'Preserve the tiny program.')
        self.assertEqual(len(result['observations']),2)
        self.assertEqual(runner.inspect(path)['status'],'CHECKS PASSED')
        initial=runner.inspect(path.parent/'initial/report.json')
        self.assertEqual(initial['status'],'CHECKS FAILED')
        self.assertNotEqual(initial['candidate_tree'],result['candidate_tree'])
        (Path(initial['candidate_path'])/'tiny.py').write_text('answer=42\n')
        self.assertEqual(runner.inspect(path)['status'],'STALE CHECKS')

    def test_repeat_defect_stops_after_one_correction(self):
        result,path=self.exercise(self.defect_check(),correct_once=True,correction_case='repeated')
        self.assertEqual(result['status'],'CHECKS FAILED')
        self.assertEqual(len(self.launches),2)
        self.assertEqual(runner.inspect(path)['status'],'CHECKS FAILED')

    def test_correction_requires_opt_in_even_for_a_real_assertion_failure(self):
        result,_=self.exercise(self.defect_check(),correction_case='fixed')
        self.assertEqual(result['status'],'CHECKS FAILED')
        self.assertEqual(result['model_dispatches'],1)
        self.assertFalse(result['correction']['enabled'])

    def test_unavailable_correction_boundary_never_dispatches_a_second_turn(self):
        result,path=self.exercise(self.defect_check(),correct_once=True,
                                  correction_case='boundary-unavailable')
        self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
        self.assertEqual(result['model_dispatches'],1)
        self.assertFalse(result['correction']['attempted'])
        self.assertEqual(result['observations'],[])
        self.assertEqual(runner.inspect(path)['status'],'EXECUTION UNAVAILABLE')

    def test_changed_corrected_candidate_invalidates_new_checks(self):
        result,path=self.exercise(self.defect_check(),correct_once=True,correction_case='fixed')
        (Path(result['candidate_path'])/'tiny.py').write_text('answer=0\n')
        self.assertEqual(runner.inspect(path)['status'],'STALE CHECKS')

    def test_nonassertion_failure_and_environment_error_never_trigger(self):
        for code in ('raise SystemExit(4)',
                     'import sys; print("PermissionError: denied",file=sys.stderr); assert False'):
            result,_=self.exercise([[sys.executable,'-c',code]],correct_once=True)
            self.assertEqual(result['status'],'CHECKS FAILED')
            self.assertEqual(len(self.launches),1)

    def test_bad_receipts_unavailability_and_stale_candidate_never_trigger(self):
        for options in ({'receipt_changes':{'stderr_truncated':True}},
                        {'receipt_changes':{'exit_code':0}},
                        {'receipt_changes':{'argv':[]}},
                        {'receipt_changes':{'argv':['sandbox','invalid-json']}},
                        {'receipt_changes':{'error':'host failure'}},
                        {'simulate_timeout':True},{'unavailable':True},
                        {'mutate_candidate':True}):
            result,_=self.exercise(self.defect_check(),correct_once=True,
                                  correction_case='fixed',**options)
            self.assertEqual(len(self.launches),1)
            self.assertFalse(result['correction']['attempted'])

    def test_bad_correction_identity_or_handoff_withdraws_old_checks(self):
        for case in ('wrong-thread','incomplete'):
            result,path=self.exercise(self.defect_check(),correct_once=True,correction_case=case)
            self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
            self.assertEqual(result['observations'],[])
            self.assertNotIn('snapshot',result)
            self.assertEqual(runner.inspect(path)['status'],'EXECUTION UNAVAILABLE')

    def test_worker_transcript_drift_invalidates_success(self):
        result,path=self.exercise(self.defect_check(),correct_once=True,correction_case='fixed')
        events=Path(result['stages'][1]['receipt']['events_path'])
        events.write_bytes(events.read_bytes()+b'{}\n')
        self.assertEqual(runner.inspect(path)['status'],'STALE CHECKS')

    def test_forged_annotations_and_advisory_gaps_cannot_trigger_correction(self):
        # Neither caller advice nor R labels replace native assertion output.
        checks=[[sys.executable,'-c','print("wrong"); raise SystemExit(1)']]
        details=[{'index':0,'outcome_ids':['R1'],'expected':'right','observed':'wrong'}]
        result,_=self.exercise(checks,correct_once=True,failure_details=details)
        self.assertIn('assertion',result['observations'][0])
        self.assertEqual(len(self.launches),1)

    def test_worker_or_receipt_drift_before_correction_never_dispatches_again(self):
        original=runner.execute_checks
        def drift(record,*args,**kwargs):
            original(record,*args,**kwargs)
            events=Path(record['stages'][0]['receipt']['events_path'])
            events.write_bytes(events.read_bytes()+b'{}\n')
        with patch.object(runner,'execute_checks',side_effect=drift):
            result,_=self.exercise(self.defect_check(),correct_once=True,correction_case='fixed')
        self.assertEqual(len(self.launches),1)
        self.assertFalse(result['correction']['attempted'])

    def test_interruption_cannot_reuse_output_to_dispatch_again(self):
        result,path=self.exercise(self.defect_check(),correct_once=True,correction_case='interrupt')
        self.assertEqual(result['status'],'EXECUTION UNAVAILABLE')
        self.assertTrue(result['correction']['attempted'])
        self.assertEqual(result['model_dispatches'],2)
        self.assertEqual(result['observations'],[])
        self.assertNotIn('snapshot',result)
        with patch.object(runner.platform,'system',return_value='Darwin'),\
             patch.object(runner.live,'launch') as launch:
            with self.assertRaises(FileExistsError):
                runner.run(path.parent.parent/'source','Preserve the tiny program.',
                           self.defect_check(),path.parent,30,10,5,correct_once=True)
            launch.assert_not_called()

    def test_spent_episode_does_not_reset_budget_for_correction(self):
        original=runner.execute_checks
        monotonic=runner.time.monotonic
        offset=[0]
        def spend(record,*args,**kwargs):
            original(record,*args,**kwargs)
            offset[0]=30
        with patch.object(runner,'execute_checks',side_effect=spend),\
             patch.object(runner.time,'monotonic',side_effect=lambda: monotonic()+offset[0]):
            result,_=self.exercise(self.defect_check(),correct_once=True,correction_case='fixed')
        self.assertEqual(result['status'],'CHECKS FAILED')
        self.assertFalse(result['correction']['attempted'])
        self.assertEqual(len(self.launches),1)
        self.assertEqual(result['limits']['seconds'],30)
        self.assertGreaterEqual(result['elapsed_seconds'],30)
