import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks import local_run as runner


class BoundedRun(unittest.TestCase):
    def exercise(self,checks,completed=True,unavailable=False):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);repo=root/'source';repo.mkdir()
        (repo/'tiny.py').write_text('print("ok")\n')
        runner.p.host.git(repo,'init','--quiet','--template=');runner.p.freeze(repo)
        def boundary(codex,directory,inputs,*args):
            for name in ('canary.py','canary.json'):(inputs/name).write_text('canary')
            return {'assessment':{'status':'OBSERVED'}}
        def oracle(codex,inputs,private,receipts):
            def execute(argv,*,cwd,timeout):
                if unavailable:raise OSError('native execution unavailable')
                result=subprocess.run(argv,cwd=cwd,timeout=timeout,capture_output=True,text=True)
                receipts.append({'kind':'process_probe','argv':['sandbox',json.dumps(argv)],
                                 'exit_code':result.returncode,'timed_out':False})
                return result
            return execute
        with patch.object(runner.platform,'system',return_value='Darwin'),\
             patch.object(runner.p.host,'find_codex',return_value='/fake/codex'),\
             patch.object(runner.p.host,'run_command',wraps=runner.p.host.run_command) as command,\
             patch.object(runner.p.live,'preferences',return_value={'model':'fixture'}),\
             patch.object(runner.p.host,'probe_boundary',side_effect=boundary),\
             patch.object(runner.p.live,'launch',return_value={'kind':'codex_exec','exit_code':0,'timed_out':False}),\
             patch.object(runner.p.live,'read_events',return_value={'thread_id':'fixture','usage':None,'commands':{},
                 'report':{'completed':completed,'summary':'Self-report, not acceptance'}}),\
             patch.object(runner,'oracle_runner',side_effect=oracle):
            original=command._mock_wraps
            command.side_effect=lambda argv,*args,**kw:({'stdout':'codex-cli 0.162.1','exit_code':0,'timed_out':False}
                if argv==['/fake/codex','--version'] else original(argv,*args,**kw))
            result=runner.run(repo,'Preserve the tiny program.',checks,root/'run',30,10,5)
        self.assertEqual((repo/'tiny.py').read_text(),'print("ok")\n')
        self.assertEqual(result['model_dispatches'],1)
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
        with self.assertRaises(ValueError):runner.inspect(path)

    def test_invalid_commands_and_budgets_dispatch_nothing(self):
        for checks in ([],['echo ok'],[['']],[[True]],[['echo','\0']]):
            with self.assertRaises(ValueError):runner.validate_checks(checks)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):runner.run(Path(temporary),'request',[['echo','ok']],Path(temporary)/'run',float('nan'))
