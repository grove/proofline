"""Supplied source contracts keep strict execution, provenance and bounded recovery."""
from copy import deepcopy
from pathlib import Path
import unittest

import proofline as p
from tests import test_source_challenges as blind


def contract(helper):
    report=blind.plan({},['D1','D2','D3','D4'])
    return {'format':'source-evidence-v1','source_sha256':p.host.sha256(b'Complete source'),
            'base_tree':p.host.git(helper.repo,'rev-parse','HEAD^{tree}'),
            'interface':'Original public value.py module; source requires complete behavior.',
            'criteria':[{**row,'invariants':['The complete source obligation holds']} for row in report['criteria']],
            'unresolved':[]}


class SourceEvidence(unittest.TestCase):
    def test_three_stage_path_binds_supplied_contract_and_rejects_drift(self):
        with blind.fixture() as helper:
            result=helper.deliver(source_evidence=contract(helper))
            self.assertEqual(result['status'],'LOCAL ACCEPTED',result['next_action'])
            self.assertEqual([x[0] for x in helper.calls],['implementer','reviewer','prover'])
            self.assertEqual(p.inspect_record(helper.output/'report.json')['status'],'LOCAL ACCEPTED')
            inputs=Path(result['candidate_path']).parent
            (inputs/'challenges/D1.py').write_text('pass')
            self.assertEqual(p.inspect_record(helper.output/'report.json')['status'],'NOT VERIFIED')

    def test_unresolved_or_ungrounded_contract_dispatches_nothing(self):
        for field,value in [('unresolved',['Full named standard is not discharged']),
                            ('source_sha256','0'*64),('base_tree','0'*40)]:
            with self.subTest(field=field),blind.fixture() as helper:
                evidence=contract(helper);evidence[field]=value
                result=helper.deliver(source_evidence=evidence)
                self.assertEqual(result['status'],'INPUT NOT READY',result['next_action'])
                self.assertEqual(result['model_dispatches'],0)
                self.assertEqual(helper.calls,[])

    def test_contract_cannot_drop_ids_invariants_source_quotes_or_executable_checks(self):
        with blind.fixture() as helper:
            valid=contract(helper)
            mutations=[]
            for key,value in [('invariants',[]),('source_quote','Invented obligation'),('probe','if !')]:
                evidence=deepcopy(valid);evidence['criteria'][0][key]=value;mutations.append(evidence)
            evidence=deepcopy(valid);evidence['criteria'].pop();mutations.append(evidence)
            for evidence in mutations:
                with self.assertRaises(ValueError):p.challenges.validate_contract(
                    evidence,'Complete source',['D1','D2','D3','D4'],valid['base_tree'])

    def test_unchanged_evidence_recovery_keeps_contract_and_candidate(self):
        with blind.fixture() as helper:
            helper.outcome=lambda role,v,s,f:('NOT VERIFIED',0,[]) if role=='prover' and helper.proofs==1 else (v,s,f)
            result=helper.deliver(source_evidence=contract(helper))
            self.assertEqual(result['status'],'LOCAL ACCEPTED',result['next_action'])
            self.assertEqual([x[0] for x in helper.calls],['implementer','reviewer','prover','prover'])
            proofs=[s for s in result['stages'] if s['role']=='prover']
            self.assertEqual(proofs[0]['binding'],proofs[1]['binding'])
            self.assertEqual(result['correction_rounds'],0)

    def test_source_contract_and_blind_author_are_mutually_exclusive(self):
        with blind.fixture() as helper:
            result=helper.deliver(source_evidence=contract(helper),source_challenges=True)
            self.assertEqual(result['status'],'INPUT NOT READY')
            self.assertEqual(result['model_dispatches'],0)
