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
                 mutate_candidate=False,boundary_ready=True,model_usage=None, failure_details=None):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);repo=root/'source';repo.mkdir()
        (repo/'tiny.py').write_text('print("ok")\n')
        runner.host.git(repo,'init','--quiet','--template=');candidate_snapshot.freeze(repo)
        def boundary(codex,directory,inputs,*args):
            for name in ('canary.py','canary.json'):(inputs/name).write_text('canary')
            return {'assessment':{'status':'OBSERVED' if boundary_ready else 'NOT VERIFIED'}}
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
                return result
            return execute
        with patch.object(runner.platform,'system',return_value='Darwin'),\
             patch.object(runner.host,'find_codex',return_value='/fake/codex'),\
             patch.object(runner.host,'run_command',wraps=runner.host.run_command) as command,\
             patch.object(runner.live,'preferences',return_value={'model':'fixture'}),\
             patch.object(runner.host,'probe_boundary',side_effect=boundary),\
             patch.object(runner.live,'launch',return_value={'kind':'codex_exec','exit_code':0,'timed_out':False}),\
             patch.object(runner.live,'read_events',return_value={'thread_id':'fixture','usage':model_usage,'commands':{},
                 'report':{'completed':completed,'summary':'Self-report, not acceptance'}}),\
             patch.object(runner,'oracle_runner',side_effect=oracle):
            original=command._mock_wraps
            command.side_effect=lambda argv,*args,**kw:({'stdout':'codex-cli 0.162.1','exit_code':0,'timed_out':False}
                if argv==['/fake/codex','--version'] else original(argv,*args,**kw))
            result=runner.run(repo,'Preserve the tiny program.',checks,root/'run',30,10,5,
                              failure_details=failure_details)
        self.assertEqual((repo/'tiny.py').read_text(),'print("ok")\n')
        self.assertEqual(result['model_dispatches'],1 if boundary_ready else 0)
        self.assertFalse(result['published']);self.assertFalse(result['merged'])
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
