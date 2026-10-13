"""Continuation boundaries; offline tests are not live handoff evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.sol_luna import study as original
from evaluation.sol_luna_host import study


class HostContinuationTests(unittest.TestCase):
    def test_result_denial_canary_exists_before_native_catalog_and_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            def observe(codex, catalog, models, output):
                record = json.loads((output/'results.json').read_text())
                self.assertEqual(record['model_dispatches'],0)
                self.assertEqual(len(record['assignments']),20)
                self.assertEqual(record['status'],'PREPARING')
                return {'status':'OBSERVED'}
            with patch.object(study.codex_catalog,'readback',side_effect=observe):
                self.assertEqual(study.catalog_readback(directory)['status'],'OBSERVED')

    def test_only_declaration_and_qualification_change(self):
        previous = original.protocol()
        current = study.runner.protocol()
        for key in previous:
            if key not in ('study_id','status','limits','handoff_qualification','budget_policy','authorization'):
                self.assertEqual(current[key],previous[key],key)
        for key,value in previous['limits'].items():
            if key not in ('episode_seconds','model_seconds','planning_seconds','verification_seconds','max_native_dispatches','handoff_seconds','handoff_model_seconds_per_call','max_campaign_seconds'):
                self.assertEqual(current['limits'][key],value,key)
        self.assertNotEqual(study.STORE,original.STORE)
        self.assertEqual(study.runner.native_boundary.STORE,study.STORE)
        for name in ('correction_allowed','advisory','execute'):
            self.assertEqual(getattr(study.runner,name).__code__,getattr(original,name).__code__,name)
        self.assertTrue((study.HERE/'corpus.py').is_file())
        self.assertEqual((study.HERE/'corpus.py').resolve(),Path(original.corpus.__file__).resolve())

    def test_original_and_continuation_freezes_remain_bound_to_their_sources(self):
        for here in (original.HERE,study.HERE):
            frozen=json.loads((here/'FREEZE.json').read_text())
            for name,digest in frozen['sha256'].items():
                self.assertEqual(original.host.sha256((original.ROOT/name).read_bytes()),digest,name)
        self.assertEqual(study.runner.ledger(),original.ledger())
        self.assertEqual(json.loads((study.HERE/'FREEZE.json').read_text())['tasks'],
                         json.loads((original.HERE/'FREEZE.json').read_text())['tasks'])

    def test_live_approval_cannot_be_inherited_from_the_stopped_declaration(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(study,'STORE',Path(temporary)), \
             patch.object(study.runner,'identities',return_value={'freeze_sha256':'new-freeze'}):
            value={'study_id':original.protocol()['study_id'],'freeze_sha256':'old-freeze',
                'max_native_dispatches':48,'max_seconds':18360,'user_authorization':'historical approval'}
            (Path(temporary)/'approval.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'Explicit authorization'):
                study.runner.approved()

    def test_changed_qualification_budget_requires_current_declared_authorization(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(study,'STORE',Path(temporary)), \
             patch.object(study.runner,'identities',return_value={'freeze_sha256':'current'}):
            value={'study_id':study.runner.protocol()['study_id'],'freeze_sha256':'current',
                'max_native_dispatches':study.runner.protocol()['limits']['max_native_dispatches'],
                'max_seconds':18360,'user_authorization':'old limit'}
            (Path(temporary)/'approval.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'Explicit authorization'):
                study.approved()
            value['max_seconds']=study.runner.protocol()['limits']['max_campaign_seconds']
            (Path(temporary)/'approval.json').write_text(json.dumps(value))
            self.assertEqual(study.approved(),value)

    def test_bundle_keeps_both_freezes_without_duplicates_or_native_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=root/'store';store.mkdir()
            (store/'result.json').write_text('{}')
            (store/'catalog-state').mkdir();(store/'catalog-state/hidden').write_text('private native state')
            with patch.object(study,'STORE',store):
                study.publish_record(root/'bundle')
            import zipfile
            with zipfile.ZipFile(root/'bundle/frozen-source.zip') as archive:
                self.assertEqual(len(archive.namelist()),len(set(archive.namelist())))
                for here in (original.HERE,study.HERE):
                    name=str((here/'FREEZE.json').relative_to(original.ROOT))
                    self.assertEqual(archive.read(name),(here/'FREEZE.json').read_bytes())
            with zipfile.ZipFile(root/'bundle/raw-evidence.zip') as archive:
                self.assertEqual(archive.namelist(),['result.json'])

    def test_stopped_live_attempt_retains_its_exact_sources_and_unexecuted_slots(self):
        import zipfile
        directory=original.ROOT/'evaluation/results/issue32-native-stopped'
        for name,digest in json.loads((directory/'hashes.json').read_text()).items():
            self.assertEqual(original.host.sha256((directory/name).read_bytes()),digest,name)
        with zipfile.ZipFile(directory/'frozen-source.zip') as archive:
            self.assertEqual(len(archive.namelist()),len(set(archive.namelist())))
            frozen=json.loads(archive.read('evaluation/sol_luna_host/FREEZE.json'))
            self.assertEqual(original.host.sha256(archive.read('evaluation/sol_luna_host/FREEZE.json')),
                '25486e814d0060a59f48f40eba7eebab76a125dba9998db8e5c0e1cd2bdf1f8f')
            for name,digest in frozen['sha256'].items():
                self.assertEqual(original.host.sha256(archive.read(name)),digest,name)
        result=json.loads((directory/'results.json').read_text())
        self.assertEqual(result['status'],'STOPPED')
        self.assertEqual(result['model_dispatches'],1)
        self.assertTrue(all(r['status']=='NOT_EXECUTED' for r in result['assignments']))

    def test_reused_native_handoff_rejects_identity_drift_without_new_model_calls(self):
        from copy import deepcopy
        prior=json.loads((original.ROOT/'evaluation/results/issue32-qualified-stopped/results.json').read_text())
        control=prior['handoff_qualification']
        study.validate_handoff(control)
        for change in ('review_thread','correction_thread','model','effort'):
            changed=deepcopy(control)
            if change=='review_thread':changed['stages'][2]['thread_id']=changed['stages'][0]['thread_id']
            elif change=='correction_thread':changed['stages'][3]['thread_id']='different'
            elif change=='model':changed['stages'][1]['model']='gpt-6.1-sol'
            else:changed['stages'][1]['reasoning_effort']='medium'
            with self.assertRaises(ValueError):study.validate_handoff(changed)
        with tempfile.TemporaryDirectory() as temporary, patch.object(study,'STORE',Path(temporary)), \
             patch.object(study.runner,'advisory') as advisory, patch.object(study.runner,'implement') as implement:
            study.handoff_control()
            advisory.assert_not_called();implement.assert_not_called()
            result=json.loads((Path(temporary)/'qualification/handoff/result.json').read_text())
            self.assertEqual(result['model_dispatches'],0)
            self.assertEqual(result['source_control'],control)

    def test_episode_uses_declared_stage_and_shared_budgets_without_changing_grading_or_repair(self):
        from contextlib import ExitStack
        from tests.test_sol_luna import stage
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as patches:
            root=Path(temporary)
            product=original.initialize('path-router',root/'seed','reference')
            row=study.runner.ledger()[0];row.update(task='path-router',arm='hybrid',seed=str(product))
            source=(product.parent/'source.md').read_text()
            frozen={'source_sha256':original.host.sha256(source.encode()),
                'seed_tree':original.host.git(product,'rev-parse','HEAD^{tree}'),
                'checks':original.selected_checks('path-router')}
            def advisory(role,source,candidate,directory,seconds,checks,*args):
                self.assertGreater(seconds,120);self.assertLessEqual(seconds,300)
                value=stage(role,'sol',role);value['elapsed_seconds']=200
                value['report']={'summary':'offline simulation','findings':[]}
                return value
            def implement(source,seed,directory,model,seconds,checks,**kwargs):
                self.assertEqual(model,'luna');self.assertAlmostEqual(seconds,400,delta=1)
                value=stage('implementation','luna','luna');value['elapsed_seconds']=200
                return {'accepted':True,'candidate':str(product),'stages':[value]}
            patches.enter_context(patch.object(study.runner,'verify'))
            patches.enter_context(patch.object(study.runner,'advisory',side_effect=advisory))
            patches.enter_context(patch.object(study.runner,'implement',side_effect=implement))
            patches.enter_context(patch.object(study.runner.adapter,'load_export',side_effect=ValueError('invalid advisory fixture')))
            patches.enter_context(patch.object(study.runner,'checked',return_value={'status':'CHECKS PASSED','elapsed_seconds':1}))
            patches.enter_context(patch.object(study.runner,'correction_allowed',return_value=False))
            grade=patches.enter_context(patch.object(study.grader,'grade',return_value={'available':True,'correct':True}))
            study.runner.episode(row,frozen,root,lambda:None)
            self.assertEqual(row['status'],'CORRECT_DELIVERY')
            self.assertEqual(row['model_seconds'],600)
            self.assertFalse(row['correction']['attempted'])
            self.assertLessEqual(grade.call_args.kwargs['seconds'],120)
