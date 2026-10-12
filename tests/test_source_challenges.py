"""Blindness, required native citations, binding and cumulative recovery mechanics."""
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import unittest
import uuid

import proofline as p
from tests import test_recovery


def plan(identity, ids):
    return {'role':'challenger','binding':p.live.binding_for(identity),'verdict':'PLANNED',
            'summary':'Offline authored transport double','findings':[],
            'criteria':[{'id':key,'source_quote':'Complete source','domains':['Required value'],
                         'probe':'import sys\nfrom pathlib import Path\nassert "value =" in (Path(sys.argv[1])/"value.py").read_text()\n'} for key in ids]}


@contextmanager
def fixture():
    helper=test_recovery.RecoveryTests()
    helper.setUp()
    native=helper.stage
    def stage(codex,directory,inputs,identity,role,preferences,allowance,**kwargs):
        if role!='challenger':
            result=native(codex,directory,inputs,identity,role,preferences,allowance,**kwargs)
            if role=='prover':
                path=Path(result['receipt']['events_path'])
                events=[json.loads(line) for line in path.read_text().splitlines()]
                commands=p.challenges.commands(inputs)
                for index,row in enumerate(result['report']['criteria']):
                    ref='frozen'+str(index)
                    events.insert(2,{'type':'item.completed','item':{'id':ref,'type':'command_execution',
                        'command':commands[row['id']],'status':'completed','exit_code':0,'aggregated_output':'offline check'}})
                    row['commands'].append(ref)
                events[-2]['item']['text']=json.dumps(result['report'])
            else:
                return result
        else:
            helper.calls.append((role,None,identity['candidate_tree'],allowance))
            report=plan(identity,kwargs['criterion_ids'])
            private=directory/'private'; private.mkdir()
            path=private/'events.jsonl'
            events=[{'type':'thread.started','thread_id':str(uuid.uuid4())},{'type':'turn.started'},
                    {'type':'item.completed','item':{'type':'agent_message','id':'handoff','text':json.dumps(report)}},
                    {'type':'turn.completed'}]
            result={'role':role,'report':report,'identities':identity,'binding':report['binding'],
                    'status':'OBSERVED','thread_id':events[0]['thread_id'],'inputs_unchanged':True,
                    'boundary':{'status':'OBSERVED'},'snapshot':p.host.snapshot(inputs)['sha256']}
        raw='\n'.join(json.dumps(event) for event in events).encode(); path.write_bytes(raw)
        result['receipt']={'kind':'codex_exec','events_path':str(path),'events.jsonl_sha256':p.host.sha256(raw),
                           'exit_code':0,'timed_out':False}
        result['commands']=p.live.read_events(result['receipt'])['commands']
        p.live.save_worker(path.parent,{'state':'finished','receipt':result['receipt']})
        p.write_record(directory/'stage.json',result)
        return result
    try:
        with helper.patches(stage): yield helper
    finally:
        helper.doCleanups()


class SourceChallenges(unittest.TestCase):
    def test_prepare_excludes_candidate_and_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); original=root/'original'; original.mkdir()
            (original/'product').mkdir(); (original/'product'/'private.py').write_text('secret candidate')
            (original/'test.py').write_text('secret tests')
            for name in ('source.md','accepted-input.md'):(original/name).write_text('promise')
            stage=root/'stage'; stage.mkdir()
            inputs=p.challenges.prepare(stage,original,'Public interface only')
            self.assertEqual((inputs/'product'/'interface.txt').read_text(),'Public interface only')
            self.assertFalse((inputs/'product'/'private.py').exists())
            self.assertFalse((inputs/'test.py').exists())

    def test_positive_proof_cannot_skip_fail_or_replace_frozen_challenges(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs=Path(tmp); (inputs/'source.md').write_text('Complete source')
            report=plan({},['D1']); p.challenges.attach(inputs,report)
            command=p.challenges.commands(inputs)['D1']
            proof={'verdict':'PROVEN','criteria':[{'id':'D1','commands':['probe']}]}
            for observed in ({},{'probe':{'command':command,'exit_code':1}},
                             {'probe':{'command':command+' ignored','exit_code':0}}):
                with self.assertRaises(ValueError):p.challenges.validate_execution(proof,observed,inputs)
            p.challenges.validate_execution(proof,{'probe':{'command':command,'exit_code':0}},inputs)
            # A negative or uncertain judgment is available without inventing product success.
            p.challenges.validate_execution({**proof,'verdict':'NOT VERIFIED'},{},inputs)
            (inputs/'challenges/D1.py').write_text('print("pass")')
            with self.assertRaises(ValueError):p.challenges.validate_execution(proof,{},inputs)

    def test_invalid_source_quote_or_script_cannot_be_sealed(self):
        report=plan({},['D1']); report['criteria'][0]['probe']='if !'
        with self.assertRaises(ValueError):p.challenges.validate_report(report,'challenger',p.live.binding_for({}),{},['D1'])
        with tempfile.TemporaryDirectory() as tmp:
            inputs=Path(tmp); (inputs/'source.md').write_text('Different promise')
            with self.assertRaises(ValueError):p.challenges.attach(inputs,plan({},['D1']))

    def test_production_recovery_reuses_blind_design_and_rejects_drift(self):
        with fixture() as helper:
            helper.outcome=lambda role,v,s,f: ('FAIL',2,['D3/D4: reproduced failure']) if role=='reviewer' and helper.reviews==1 else (v,s,f)
            result=helper.deliver(source_challenges=True)
            self.assertEqual(result['status'],'LOCAL ACCEPTED',result['next_action'])
            self.assertEqual([x[0] for x in helper.calls],['challenger','implementer','reviewer','implementer','reviewer','prover'])
            self.assertEqual(result['model_dispatches'],6)
            self.assertEqual(result['correction_rounds'],1)
            self.assertEqual(p.inspect_record(helper.output/'report.json')['status'],'LOCAL ACCEPTED')
            inputs=Path(result['candidate_path']).parent
            (inputs/'challenges/D1.py').write_text('pass')
            self.assertEqual(p.inspect_record(helper.output/'report.json')['status'],'NOT VERIFIED')

    def test_source_design_uses_dispatch_budget_before_coding(self):
        with fixture() as helper:
            result=helper.deliver(source_challenges=True,dispatches=3)
            self.assertEqual(result['status'],'BUDGET EXHAUSTED')
            self.assertEqual(result['model_dispatches'],0)
            self.assertEqual(helper.calls,[])

    def test_evidence_recovery_keeps_candidate_and_sealed_design(self):
        with fixture() as helper:
            helper.outcome=lambda role,v,s,f: ('NOT VERIFIED',0,[]) if role=='prover' and helper.proofs==1 else (v,s,f)
            result=helper.deliver(source_challenges=True)
            self.assertEqual(result['status'],'LOCAL ACCEPTED',result['next_action'])
            self.assertEqual([x[0] for x in helper.calls],['challenger','implementer','reviewer','prover','prover'])
            proofs=[stage for stage in result['stages'] if stage['role']=='prover']
            self.assertEqual(proofs[0]['binding'],proofs[1]['binding'])
            self.assertEqual(result['correction_rounds'],0)

    def test_unavailable_design_is_environment_gap_not_product_rejection(self):
        record={'stages':[]}
        p.accept_stage(record,{'role':'challenger','status':'NOT VERIFIED',
                              'receipt':{'exit_code':None,'timed_out':True},'error':'Unavailable'},None,lambda:None)
        self.assertEqual(record['status'],'ENVIRONMENT FAILURE')
        self.assertEqual(record['failure_class'],'environment failure')
        self.assertIsNone(record['next_role'])
