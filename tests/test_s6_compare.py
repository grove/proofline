"""S6 controls and accounting are deterministic; native judgments are separate."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from checks import s6_compare as s6


class PilotTests(unittest.TestCase):
    def manifest(self):
        return {'models': {'sol': {'model': 'sol'}, 'luna': {'model': 'luna'}},
                'hypothesis': {'maximum_false_blocking_rate': .1},
                'limits_of_inference': [], 'remote_target_coverage': 'NOT EXECUTED'}

    def assignment(self, cohort='proofline', outcome='ACCEPTED CORRECTLY', **extra):
        return {'task':'one','input_mode':'raw-request','model':'sol','cohort':cohort,'repeat':0,
                'outcome':outcome,'end_to_end_seconds':10,'human_interventions':0,'human_attention_seconds':0,
                'delivery':{'elapsed_seconds':8,'model_dispatches':1,'stages':[
                    {'role':'implementer','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':10},
                     'receipt':{'elapsed_seconds':8}}]}, **extra}

    def summary(self, assignments, status='COMPLETE', rates=None):
        return s6.summarize(self.manifest(), {'status':status,'manifest_sha256':'fixed','assignments':assignments}, rates)

    def test_all_twenty_task_evaluators_accept_valid_controls_and_reject_defects(self):
        self.assertEqual(len(s6.corpus.TASKS),20)
        self.assertEqual(len({t['id'] for t in s6.corpus.TASKS}),20)
        self.assertGreaterEqual(sum('held-out' in t['tags'] for t in s6.corpus.TASKS),8)
        with tempfile.TemporaryDirectory() as temporary:
            controls = s6.controls(s6.corpus.TASKS,Path(temporary))
        self.assertEqual(len(controls),46)
        self.assertTrue(all(c['evaluation']['observed'] for c in controls))

    def test_false_acceptance_overrides_speed_and_quality_gate(self):
        result=self.summary([self.assignment(outcome='FALSE ACCEPTED'),self.assignment('p2p')])
        self.assertIn('STRENGTHEN VERIFICATION',result['decision'])
        self.assertFalse(result['hypotheses'][0]['quality_gate'])
        self.assertEqual(result['hypotheses'][0]['25_percent_target'],'INCONCLUSIVE')

    def test_failed_attempt_costs_are_divided_by_successes(self):
        result=self.summary([self.assignment(),self.assignment(outcome='FAILED',end_to_end_seconds=20)])
        row=result['cohorts']['sol/raw-request/proofline']
        self.assertEqual(row['seconds_per_satisfactory_delivery'],30)
        self.assertEqual(row['tokens_per_satisfactory_delivery'],220)
        self.assertEqual(row['reliability'],.5)
        self.assertEqual(row['satisfactory_deliveries_per_hour'],120)
        self.assertIsNone(row['cost_per_satisfactory_delivery_usd'])

    def test_unknown_usage_and_unexecuted_cases_cannot_appear_as_zero_cost(self):
        unknown=self.assignment(delivery={'model_dispatches':3,'stages':[]})
        missing=self.assignment(outcome='NOT EXECUTED')
        for key in ('delivery','end_to_end_seconds','human_interventions','human_attention_seconds'):missing.pop(key)
        row=self.summary([unknown,missing],status='INCOMPLETE')['cohorts']['sol/raw-request/proofline']
        self.assertEqual(row['unknown_usage_calls'],3)
        self.assertIsNone(row['tokens_per_satisfactory_delivery'])
        self.assertIsNone(row['seconds_per_satisfactory_delivery'])
        self.assertEqual(row['known_calls'],3)
        self.assertEqual(row['unknown_human_attention'],1)

    def test_cached_tokens_are_included_in_input_and_not_double_charged(self):
        rates={'sol':{'input':10,'cached':2,'output':30}}
        row=self.summary([self.assignment()],rates=rates)['cohorts']['sol/raw-request/proofline']
        self.assertAlmostEqual(row['cost_per_satisfactory_delivery_usd'],.00114)
        self.assertAlmostEqual(row['satisfactory_deliveries_per_dollar'],1/.00114)
        self.assertEqual(row['tokens_per_satisfactory_delivery'],110)

    def test_negative_or_invalid_provider_usage_remains_unknown(self):
        for usage in ({'input_tokens':1,'cached_input_tokens':2,'output_tokens':1},
                      {'input_tokens':-1,'cached_input_tokens':0,'output_tokens':1},None,'unknown'):
            _, missing=s6.stage_usage([{'usage':usage}],1)
            self.assertEqual(missing,1)

    def test_zero_deliveries_and_fast_failures_do_not_prove_a_time_advantage(self):
        rows=[self.assignment('p2p',outcome='FAILED',end_to_end_seconds=1),self.assignment()]
        result=self.summary(rows)
        self.assertIsNone(result['cohorts']['sol/raw-request/p2p']['seconds_per_satisfactory_delivery'])
        self.assertEqual(result['hypotheses'][0]['25_percent_target'],'INCONCLUSIVE')

    def test_target_requires_ten_distinct_paired_tasks_and_matching_success_sets(self):
        rows=[]
        for index in range(10):
            rows += [self.assignment(task=str(index),end_to_end_seconds=6),self.assignment('p2p',task=str(index))]
        result=self.summary(rows)
        self.assertEqual(result['hypotheses'][0]['25_percent_target'],'SUPPORTED ON PILOT')
        rows[-1]['outcome']='FAILED'
        result=self.summary(rows)
        self.assertEqual(result['hypotheses'][0]['25_percent_target'],'INCONCLUSIVE')
        self.assertNotIn('CONTINUE CAUTIOUSLY',result['decision'])

    def test_repeated_samples_do_not_replace_distinct_tasks(self):
        rows=[]
        for index in range(20):
            rows += [self.assignment(repeat=index,end_to_end_seconds=6),self.assignment('p2p',repeat=index)]
        self.assertEqual(self.summary(rows)['hypotheses'][0]['25_percent_target'],'INCONCLUSIVE')

    def test_recoverable_false_rejection_is_retained(self):
        candidate=self.assignment(judgment_errors=[{'role':'prover','false_rejection':True}])
        row=self.summary([candidate])['cohorts']['sol/raw-request/proofline']
        self.assertEqual(row['false_rejections'],1)
        self.assertEqual(row['satisfactory'],1)

    def test_preparation_calls_time_and_usage_count_with_delivery(self):
        candidate=self.assignment(planning_stages=[{'role':'planning','receipt':{'elapsed_seconds':2},'usage':None}],preparation_seconds=2)
        row=self.summary([candidate])['cohorts']['sol/raw-request/proofline']
        self.assertEqual(row['known_calls'],2)
        self.assertEqual(row['upstream_planning_seconds'],2)
        self.assertIsNone(row['tokens_per_satisfactory_delivery'])

    def test_correct_but_undelivered_is_distinct_from_wrong_code(self):
        row=self.summary([self.assignment(outcome='BUDGET EXHAUSTED',evaluation={'correct':True,'observed':True}),
                          self.assignment(outcome='FAILED',evaluation={'correct':False,'observed':True})])['cohorts']['sol/raw-request/proofline']
        self.assertEqual(row['correct_but_undelivered'],1)
        self.assertEqual(row['false_blocked'],0)

    def test_incomplete_native_handoff_retains_its_actual_timeout_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);private=root/'private';private.mkdir()
            for name in ('events.jsonl','stderr.txt'):(private/name).write_text('')
            receipt={'invocation_id':'one','timed_out':True,'elapsed_seconds':240,
                     **{name+'_sha256':s6.p.host.sha256(b'') for name in ('events.jsonl','stderr.txt')}}
            stage={'role':'implementer','binding':'exact','status':'NOT VERIFIED','receipt':receipt}
            s6.p.write_record(root/'stage.json',stage)
            s6.p.write_record(private/'worker.json',{'state':'finished','receipt':receipt})
            original={'model_dispatches':1,'stages':[],'active_stage':{'role':'implementer','binding':'exact','directory':str(root)}}
            measured=s6.account_delivery(original)
            self.assertEqual(s6.classify(False,{'correct':True,'observed':True},measured),'BUDGET EXHAUSTED')
            self.assertEqual(s6.stage_usage(measured['stages'],1)[1],1)
            self.assertEqual(original['stages'],[])
            (private/'events.jsonl').write_text('changed')
            with self.assertRaisesRegex(ValueError,'evidence changed'):s6.account_delivery(original)

    def test_raw_p2p_readiness_is_decided_by_the_current_p2p_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'source.md').write_text('original')
            controller=root/'p2p_delivery.py'
            plan='Source: [Original request](source.md)\n## Unresolved gaps\n- None in this proposed outcome.\n'
            with patch.dict('sys.modules',{'p2p_delivery':SimpleNamespace(parse_contract=lambda data: self.assertEqual(data,plan.encode()))}), \
                 patch.object(s6.p.contract_input,'inspect_contract',side_effect=AssertionError('Proofline adapter must not judge P2P')):
                s6.validate_p2p_plan(plan,root,controller)
                for source in ('../private.md','source.md)\nSource: [Other](source.md','https://example.com/source.md'):
                    with self.assertRaises(ValueError):s6.validate_p2p_plan(plan.replace('source.md',source),root,controller)

    def test_declaration_rejects_nonfinite_limits_and_identical_model_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for options in ({'seconds':float('nan')},{'stage_seconds':float('inf')},{'jobs':True},
                            {'models':{'luna':'same','sol':'same'}}):
                with self.assertRaises(ValueError):s6.declare(root/'not-created',root,**options)
                self.assertFalse((root/'not-created').exists())

    def test_a_host_failure_is_not_a_false_blocking_judgment(self):
        score={'observed':True,'correct':True}
        self.assertEqual(s6.classify(False,score,{'stages':[]}),'FAILED')
        self.assertEqual(s6.classify(True,{'observed':True,'correct':False},{}),'FALSE ACCEPTED')
        self.assertEqual(s6.classify(False,score,{'stages':[{'role':'reviewer','status':'OBSERVED'}]}),'FALSE BLOCKED')
        self.assertEqual(s6.classify(False,score,{'status':'BUDGET EXHAUSTED'}),'BUDGET EXHAUSTED')
        self.assertEqual(s6.classify(True,{'observed':False,'correct':False},{}),'NOT VERIFIED')

    def test_freeze_rejects_runtime_evaluator_population_and_rate_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            checkout=root/'p2p'; checkout.mkdir()
            for name in (s6.s3.SCRIPT,'skills/productivity/plan-acceptance/SKILL.md','skills/productivity/plan-acceptance/references/acceptance-contract-protocol.md'):
                path=checkout/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
            s6.p.host.git(checkout,'init','--quiet','--template=');s6.p.freeze(checkout)
            output=root/'pilot'
            s6.declare(output,checkout)
            manifest,report=s6.verify_declaration(output)
            self.assertEqual(len(manifest['assignments']),120)
            self.assertEqual(sum(a['input_mode']=='raw-request' for a in manifest['assignments']),60)
            self.assertEqual(sum(a['cohort']=='p2p' for a in manifest['assignments']),20)
            runtime=checkout/s6.s3.SCRIPT
            runtime.write_text('changed')
            with self.assertRaisesRegex(ValueError,'runtime/instruction changed'):s6.verify_declaration(output)
            self.assertEqual(len(s6.verify_declaration(output,runtime=False)[0]['assignments']),120)
            runtime.write_text('fixture')
            tasks=output/'operator/tasks.json';original=tasks.read_bytes();tasks.write_text('[]')
            with self.assertRaisesRegex(ValueError,'evaluator or pricing changed'):s6.verify_declaration(output)
            tasks.write_bytes(original)
            report['assignments'].pop();s6.p.write_record(output/'operator/report.json',report)
            with self.assertRaisesRegex(ValueError,'population changed'):s6.verify_declaration(output)

    def test_declared_model_override_preserves_transport_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            args=['exec','--sandbox','workspace-write','-C',temporary,'-c','model="old"',
                  '-c','sandbox_workspace_write.network_access=false','-c','sandbox_workspace_write.exclude_slash_tmp=true',
                  '-c','sandbox_workspace_write.exclude_tmpdir_env_var=true','-']
            with patch.object(s6.s3.s3_p2p_transport.os,'execv') as execute:
                s6.s3.s3_p2p_transport.launch('/codex',args,[],temporary,{'model':'luna','model_reasoning_effort':'high'})
            argv=execute.call_args.args[1]
            self.assertIn('model="luna"',argv)
            self.assertIn('model_reasoning_effort="high"',argv)
            self.assertNotIn('model="old"',argv)
            self.assertTrue(any(value.startswith('permissions.s3_p2p=') for value in argv))
            with self.assertRaisesRegex(ValueError,'Only declared model'):
                s6.s3.s3_p2p_transport.launch('/codex',args,[],temporary,{'approval_policy':'never'})

class OriginalPromiseAuditTests(unittest.TestCase):
    def test_json_numbers_allow_equivalent_representation_but_never_boolean_substitution(self):
        self.assertTrue(s6.same_json({'rows':[1.0]}, {'rows':[1]}))
        self.assertFalse(s6.same_json({'rows':[True]}, {'rows':[1]}))
        self.assertFalse(s6.same_json([],{}))

    def test_cli_correct_input_mutation_is_independently_rejected_at_library_seam(self):
        from checks import s6_acceptance_audit as audit
        item=s6.corpus.TASKS[1]
        code=item['good'].replace('def process(', 'def original_process(')+'\ndef process(data):\n    result=original_process(data)\n    data["unexpected"]=True\n    return result\n'
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            s6.seed(root/'candidate',dict(item,good=code),'good')
            cli=s6.evaluate(root/'candidate',item,directory=root/'cli')
            library=audit.inspect(root/'candidate',item,root/'library')
            self.assertTrue(all(o['status']=='SATISFIED' for o in cli['observations']))
            self.assertFalse(cli['correct'])
            self.assertTrue(library['observed'])
            self.assertFalse(library['correct'])

    def test_unused_foreign_dependency_is_not_excused_by_green_behavior(self):
        from checks import s6_acceptance_audit as audit
        item=s6.corpus.TASKS[0]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            s6.seed(root/'candidate',dict(item,good=item['good']+'\nif False:\n    import unrequested_vendor_extension\n'),'good')
            result=audit.inspect(root/'candidate',item,root/'audit')
            self.assertTrue(result['observed'])
            self.assertFalse(result['correct'])
            self.assertEqual(result['foreign_imports'][0]['module'],'unrequested_vendor_extension')

    def test_source_required_value_error_is_not_replaced_by_key_error(self):
        from checks import s6_acceptance_audit as audit
        item=s6.corpus.TASKS[0]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            code=item['good'].replace('raise ValueError("blank")','raise KeyError("blank")')
            s6.seed(root/'candidate',dict(item,good=code),'good')
            cli=s6.evaluate(root/'candidate',item,directory=root/'cli')
            result=audit.inspect(root/'candidate',item,root/'audit')
            self.assertTrue(all(o['status']=='SATISFIED' for o in cli['observations']))
            self.assertFalse(cli['correct'])
            self.assertFalse(result['correct'])

    def test_value_error_subclasses_are_valid_alternative_implementations(self):
        from checks import s6_acceptance_audit as audit
        item=s6.corpus.TASKS[0]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            code='class ValidationError(ValueError):\n    pass\n\n'+item['good'].replace('raise ValueError(', 'raise ValidationError(')
            s6.seed(root/'candidate',dict(item,good=code),'good')
            self.assertTrue(audit.inspect(root/'candidate',item,root/'audit')['correct'])
