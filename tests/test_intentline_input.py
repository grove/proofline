"""Real producer bundles with authored offline controls; no live qualification."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import proofline
import intentline_input as native

FIXTURES=Path(__file__).parent/'fixtures/intentline'


class NativeInput(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();self.bundle=self.root/'bundle';shutil.copytree(FIXTURES/'successor',self.bundle)
        self.repo=self.root/'product';self.repo.mkdir();(self.repo/'entry.py').write_text("print('original')\n")
        (self.repo/'policy.md').write_bytes(b'Existing valid usernames remain unchanged\n')
        proofline.host.git(self.repo,'init','--quiet','--template=');proofline.host.git(self.repo,'add','--all');proofline.host.git(self.repo,'commit','--quiet','-m','Authored offline product')
        metadata,_,_=native.inspect_intentline(self.bundle)
        self.request={'path':self.bundle,'contract_sha256':metadata['contract_sha256'],'source_chain_sha256':metadata['source_chain_sha256'],
                      'bundle_sha256':metadata['bundle_sha256'],'approval_reference':'Synthetic caller fixture; sensitive reference; NOT real approval'}

    def deliver(self,request=None,name='run'):
        return proofline.deliver(self.repo,'','',self.root/name,intentline_request=self.request if request is None else request)

    def stage_result(self,directory,inputs,identity,role,verdict=None,findings=None):
        verdict=verdict or {'implementer':'READY','reviewer':'PASS','prover':'PROVEN'}[role]
        report={'role':role,'binding':proofline.live.binding_for(identity),'verdict':verdict,
                'findings':findings or [],'summary':'Authored offline transport double, not real model evidence',
                'criteria':[{'id':key,'status':'NOT VERIFIED' if verdict=='NOT VERIFIED' else 'SATISFIED',
                             'observation':'Authored mechanical control','commands':['probe'] if role=='prover' else []}
                            for key in ('R1','R2')]}
        thread=str(uuid.uuid4());private=directory/'private';private.mkdir()
        events=[{'type':'thread.started','thread_id':thread},{'type':'turn.started'},
                {'type':'item.completed','item':{'id':'probe','type':'command_execution','command':'offline probe',
                                               'exit_code':0,'status':'completed','aggregated_output':'controlled'}},
                {'type':'item.completed','item':{'id':'handoff','type':'agent_message','text':json.dumps(report)}},
                {'type':'turn.completed'}]
        raw='\n'.join(json.dumps(event) for event in events).encode();path=private/'events.jsonl';path.write_bytes(raw)
        receipt={'kind':'codex_exec','exit_code':0,'timed_out':False,'events_path':str(path),
                 'events.jsonl_sha256':proofline.host.sha256(raw)}
        proofline.live.save_worker(private,{'state':'finished','receipt':receipt})
        result={'role':role,'identities':identity,'binding':report['binding'],'status':'OBSERVED',
                'thread_id':thread,'report':report,'receipt':receipt,'inputs_unchanged':True,
                'snapshot':proofline.host.snapshot(inputs)['sha256'],'boundary':{'status':'OBSERVED'},'usage':None}
        (directory/'stage.json').write_text(json.dumps(result))
        return result

    def test_actual_producer_fixtures_and_dependency_free_inspection(self):
        identity=json.loads((FIXTURES/'identity.json').read_text())
        for name,expected in identity['files'].items():self.assertEqual(native.sha((FIXTURES/name).read_bytes()),expected)
        for name in ('original','successor'):
            result=subprocess.run([sys.executable,'-I','-B',str(Path(proofline.__file__)), 'inspect-intentline',str(FIXTURES/name)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['authorization'],'not_established')
        self.assertEqual(native.inspect_intentline(self.bundle)[0]['criterion_ids'],['R1','R2'])
        with patch('subprocess.Popen',side_effect=AssertionError('exec')),patch('socket.socket',side_effect=AssertionError('egress')):
            native.inspect_intentline(self.bundle)

    def test_missing_false_stale_adoption_stops_before_host_or_model(self):
        for field in ('contract_sha256','source_chain_sha256','bundle_sha256','approval_reference'):
            for value in (None,'wrong'):
                request={**self.request,field:value}
                if field=='approval_reference' and value=='wrong':continue
                with patch.object(proofline.host,'find_codex') as host,patch.object(proofline.live,'run_stage') as stage:
                    record=self.deliver(request,name=field+str(value))
                host.assert_not_called();stage.assert_not_called();self.assertEqual(record['status'],'INPUT NOT READY');self.assertEqual(record['model_dispatches'],0)
        # A self-produced approval label alone cannot populate exact trusted-caller flags.
        label=self.root/'approved.json';label.write_text('{"approved":true}')
        with patch.object(proofline.host,'find_codex') as host:
            result=self.deliver({**self.request,'contract_sha256':None,'approval_path':label,'approval_sha256':native.sha(label.read_bytes())},'label')
        host.assert_not_called();self.assertEqual(result['status'],'INPUT NOT READY')

    def test_mutation_deleted_amendment_omitted_lineage_and_no_fallback(self):
        original=(self.bundle/'source-S2.txt').read_bytes()
        for action in ('change','delete','link'):
            path=self.bundle/'source-S2.txt'
            if path.exists():path.unlink()
            if action=='change':path.write_bytes(b'Invented scope\n')
            if action=='link':path.symlink_to(self.repo/'entry.py')
            with patch.object(proofline.host,'find_codex') as host,patch.object(proofline.live,'run_stage') as stage:
                record=self.deliver(name=action)
            host.assert_not_called();stage.assert_not_called();self.assertEqual(record['status'],'INPUT NOT READY')
        path.unlink();path.write_bytes(original)
        marker=native.parse((self.bundle/'native-manifest.json').read_bytes());marker['requirement_ids']=['R1'];(self.bundle/'native-manifest.json').write_bytes(native.canonical(marker))
        with self.assertRaises(ValueError):native.inspect_intentline(self.bundle)
        result=subprocess.run([sys.executable,'-I','-B',str(Path(proofline.__file__)),'deliver','--experimental','--repo',str(self.repo),'--intentline-bundle',str(self.bundle),'--source',str(self.repo/'entry.py'),'--brief',str(self.repo/'entry.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertIn('mutually exclusive',result.stderr)

    def test_admission_then_missing_host_and_current_document_gate(self):
        with patch.object(proofline.platform,'system',return_value='Darwin'),patch.object(proofline.host,'find_codex',return_value=None),patch.object(proofline.live,'run_stage') as stage:
            record=self.deliver()
        stage.assert_not_called();self.assertEqual(record['accepted_contract']['format'],'intentline-native');self.assertEqual(record['model_dispatches'],0)
        with patch.object(proofline.platform,'system',return_value='Darwin'),patch.object(proofline.host,'find_codex',return_value=None):
            positional=proofline.deliver(self.repo,'','',self.root/'positional',900,240,120,'Inspect entry.py',None,self.request)
        self.assertEqual(positional['accepted_contract']['format'],'intentline-native')
        (self.repo/'policy.md').write_text('Changed policy\n')
        with patch.object(proofline.host,'find_codex') as host:
            record=self.deliver(name='changed-policy')
        host.assert_not_called();self.assertEqual(record['status'],'INPUT NOT READY')

    def test_fake_host_preserves_all_role_bindings_and_protects_authority(self):
        calls=[]
        actual_command=proofline.host.run_command
        def command(argv,*args,**kwargs):
            if argv[1:] == ['--version']: return {'exit_code':0,'timed_out':False,'stdout':'codex-cli 0.162.1'}
            return actual_command(argv,*args,**kwargs)
        def boundary(codex,directory,inputs,*args):
            for name in ('canary.py','canary.json'):(inputs/name).write_text('Authored offline transport double')
            return {'assessment':{'status':'OBSERVED'}}
        def stage(codex,directory,inputs,identity,role,preferences,allowance,**kwargs):
            context=json.loads((inputs/'contract-context.json').read_text())
            self.assertNotIn('sensitive reference',json.dumps(context));self.assertNotIn('reference',context['approval'])
            self.assertEqual(kwargs['criterion_ids'],['R1','R2']);self.assertTrue((inputs/'intentline/source-S2.txt').exists())
            self.assertEqual(native.inspect_bundle(inputs/'intentline')['source_chain_sha256'],self.request['source_chain_sha256'])
            calls.append((role,identity))
            return self.stage_result(directory,inputs,identity,role)
        with patch.object(proofline.platform,'system',return_value='Darwin'),patch.object(proofline.host,'find_codex',return_value=sys.executable),patch.object(proofline.host,'run_command',side_effect=command),patch.object(proofline.host,'probe_boundary',side_effect=boundary),patch.object(proofline.live,'preferences',return_value={}),patch.object(proofline.live,'run_stage',side_effect=stage):
            result=self.deliver()
        self.assertEqual(result['status'],'LOCAL ACCEPTED',result['next_action']);self.assertEqual([role for role,_ in calls],['implementer','reviewer','prover'])
        self.assertEqual(len({identity['native_source_chain_sha256'] for _,identity in calls}),1)
        # Synthetic receipts exercise controller mechanics, not live model qualification.
        self.assertEqual(proofline.inspect_record(self.root/'run/report.json')['status'],'LOCAL ACCEPTED')
        record_path=self.root/'run/report.json';saved=json.loads(record_path.read_text())
        original=saved['stages'][0]['receipt']['events.jsonl_sha256']
        saved['stages'][0]['receipt']['events.jsonl_sha256']='0'*64;record_path.write_text(json.dumps(saved))
        with self.assertRaises(ValueError):proofline.inspect_record(record_path)
        saved['stages'][0]['receipt']['events.jsonl_sha256']=original;record_path.write_text(json.dumps(saved))
        (self.bundle/'source-S2.txt').write_text('Altered amendment')
        self.assertEqual(proofline.inspect_record(self.root/'run/report.json')['status'],'INPUT NOT READY')
        candidate=Path(result['candidate_path']);(candidate/'entry.py').write_text('post-proof tamper')
        self.assertEqual(proofline.inspect_record(self.root/'run/report.json')['status'],'NOT VERIFIED')

    def test_approval_reference_race_and_omission_findings_preserve_no_fallback(self):
        inspected=self.root/'external-reference.txt';inspected.write_text(self.request['contract_sha256']+'\n'+self.request['source_chain_sha256']+'\nSynthetic fixture, not human adoption\n')
        request={**self.request,'approval_path':inspected,'approval_sha256':native.sha(inspected.read_bytes())}
        metadata,_,_=native.adopted_intentline(**request)
        self.assertNotIn(str(inspected),json.dumps(native.worker_metadata(metadata)))
        inspected.write_text('changed')
        with patch.object(proofline.host,'find_codex') as host:
            result=self.deliver(request,'changed-approval')
        host.assert_not_called();self.assertEqual(result['status'],'INPUT NOT READY')
        # Independent semantic judgments are delegated to the existing roles, not fabricated by a parser.
        actual_command=proofline.host.run_command
        def command(argv,*args,**kwargs):
            if argv[1:]==['--version']:return {'exit_code':0,'timed_out':False,'stdout':'codex-cli 0.162.1'}
            return actual_command(argv,*args,**kwargs)
        def boundary(codex,directory,inputs,*args):
            for name in ('canary.py','canary.json'):(inputs/name).write_text('offline boundary double')
            return {'assessment':{'status':'OBSERVED'}}
        for kind in ('omitted-source-promise','invented-scope'):
            calls=[]
            def stage(codex,directory,inputs,identity,role,preferences,allowance,**kwargs):
                calls.append(role)
                return self.stage_result(directory,inputs,identity,role,'READY' if role=='implementer' else 'NOT VERIFIED',
                                         [] if role=='implementer' else ['INPUT NOT READY: Authored '+kind+' negative judgment'])
            with patch.object(proofline.platform,'system',return_value='Darwin'),patch.object(proofline.host,'find_codex',return_value=sys.executable),patch.object(proofline.host,'run_command',side_effect=command),patch.object(proofline.host,'probe_boundary',side_effect=boundary),patch.object(proofline.live,'preferences',return_value={}),patch.object(proofline.live,'run_stage',side_effect=stage):
                result=self.deliver(name=kind)
            self.assertEqual(result['status'],'INPUT NOT READY');self.assertEqual(calls,['implementer','reviewer'])

    def test_evidence_refresh_preserves_binding_but_outcome_change_refuses(self):
        manifest=json.loads((self.bundle/'source-manifest.json').read_bytes())
        predecessor=json.loads((self.bundle/('archive-'+manifest['predecessor']['snapshot_sha256']+'.json')).read_bytes())
        draft=json.loads((self.bundle/'initial-contract.json').read_bytes())
        mapping=json.loads((self.bundle/'continuity.json').read_bytes())
        blobs={row['source_id']:(self.bundle/('source-'+row['source_id']+'.txt')).read_bytes() for row in manifest['sources']}
        draft['requirements'][0]['plan_state']='gap';draft['requirements'][0]['planned_evidence']='Await unavailable harness'
        mapping['contract_sha256']=native.sha(native.canonical(draft))
        native.continuity(mapping,predecessor['history'][-1],draft,manifest,blobs,predecessor['manifest'])
        draft['requirements'][0]['statement']='Accept empty usernames'
        mapping['contract_sha256']=native.sha(native.canonical(draft))
        with self.assertRaisesRegex(ValueError,'False mechanical preservation'):
            native.continuity(mapping,predecessor['history'][-1],draft,manifest,blobs,predecessor['manifest'])

    def test_native_resume_rechecks_changed_authority_before_dispatch(self):
        from tests import test_recovery
        transport=test_recovery.RecoveryTests();transport.setUp();self.addCleanup(transport.doCleanups)
        calls=[]
        def stage(codex,directory,inputs,identity,role,preferences,allowance,**kwargs):
            calls.append(role)
            return self.stage_result(directory,inputs,identity,role,'READY' if role=='implementer' else 'NOT VERIFIED')
        with transport.patches(stage):
            result=self.deliver()
        self.assertEqual(result['status'],'NOT VERIFIED');self.assertEqual(calls,['implementer','reviewer','reviewer','reviewer'])
        (self.bundle/'source-S2.txt').write_text('Changed after the evidence gap')
        with transport.patches(stage):
            result=proofline.resume(self.root/'run/report.json')
        self.assertEqual(result['status'],'INPUT NOT READY');self.assertEqual(len(calls),4)

    def test_native_adoption_change_between_stages_stops_and_remote_target_is_unavailable(self):
        from tests import test_recovery
        transport=test_recovery.RecoveryTests();transport.setUp();self.addCleanup(transport.doCleanups)
        calls=[]
        def stage(codex,directory,inputs,identity,role,preferences,allowance,**kwargs):
            calls.append(role)
            result=self.stage_result(directory,inputs,identity,role)
            (self.bundle/'source-S2.txt').write_text('Changed before independent checking')
            return result
        with transport.patches(stage):
            result=self.deliver()
        self.assertEqual(result['status'],'INPUT NOT READY');self.assertEqual(calls,['implementer'])
        with patch.object(proofline.publication,'publish') as publish,patch.object(proofline.host,'find_codex') as host:
            result=proofline.deliver(self.repo,'','',self.root/'remote',intentline_request=self.request,effect_grant={})
        publish.assert_not_called();host.assert_not_called();self.assertEqual(result['status'],'INPUT NOT READY')
