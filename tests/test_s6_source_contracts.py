"""Contract readiness gates dispatch; native semantic adjudication stays separate."""
import ast
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks import s6_contract_qualification as gate


class Contracts(unittest.TestCase):
    def test_ordering_predicate_accepts_both_structures_and_rejects_equality_narrowing(self):
        task=gate.specs.s6.corpus.TASKS[1]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);probe=root/'probe.py';probe.write_text(gate.specs.PAGINATION)
            for variant in ('good','alternative'):
                code=task[variant]
                narrowed=code.replace('if b["score"] < a["score"]:',
                                     'if a["score"] != b["score"] and b["score"] < a["score"]:') if variant=='good' else code.replace(
                                     'if other["score"] < row["score"]:',
                                     'if row["score"] != other["score"] and other["score"] < row["score"]:')
                self.assertNotEqual(code,narrowed)
                for name,program,expected in ((variant,code,0),(variant+'-narrowed',narrowed,1)):
                    product=root/name;product.mkdir();(product/'product.py').write_text(program)
                    result=subprocess.run([sys.executable,'-I','-B',str(probe),str(product)],capture_output=True,text=True)
                    self.assertEqual(result.returncode,expected,result.stderr)
                    if expected:self.assertIn('source-declared representation',result.stderr)

    def test_actual_clarification_reaches_source_and_indexed_brief_without_losing_originals(self):
        task=next(x for x in gate.specs.s6.corpus.TASKS if x['id']=='utc-timestamps')
        source=gate.specs.s6.corpus.source(task);brief=gate.specs.s6.corpus.brief(task)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'source.md').write_text(source);(root/'accepted-input.md').write_text(brief)
            gate.clarify(root);gate.clarify(root)
            self.assertEqual((root/'original-source.md').read_text(),source)
            self.assertEqual((root/'original-accepted-input.md').read_text(),brief)
            self.assertEqual((root/'source.md').read_text().count(gate.utc.CLARIFICATION),1)
            rows=(root/'accepted-input.md').read_text().splitlines()
            self.assertIn(gate.utc.CLARIFICATION,next(row for row in rows if row.startswith('| R1 |')))
            self.assertEqual([row for row in rows if row.startswith(('| R2 |','| R3 |'))],
                             [row for row in brief.splitlines() if row.startswith(('| R2 |','| R3 |'))])

    def test_source_profiles_are_executable_and_do_not_require_a_standard_pdf(self):
        for task in gate.specs.s6.corpus.TASKS:
            if task['id'] not in ('unicode-usernames','stable-pagination','utc-timestamps','interval-union'):
                continue
            source=gate.specs.s6.corpus.source(task)
            contract=gate.specs.contract(task['id'],source,'base')
            for row in contract['criteria']:ast.parse(row['probe'])
            if task['id']=='utc-timestamps':
                self.assertIn('23:59:60Z',contract['criteria'][0]['probe'])
                self.assertIn('clarification',contract['unresolved'][0])
                with self.assertRaises(ValueError):
                    gate.p.challenges.validate_contract(contract,source,['R1','R2','R3'],'base')
                clarified=source+'\n'+gate.utc.CLARIFICATION+'\n'
                gate.p.challenges.validate_contract(gate.specs.contract(task['id'],clarified,'base'),clarified,['R1','R2','R3'],'base')
            else:gate.p.challenges.validate_contract(contract,source,['R1','R2','R3'],'base')

    def test_readiness_gap_stops_all_model_judgments_and_recovery(self):
        task=next(x for x in gate.specs.s6.corpus.TASKS if x['id']=='utc-timestamps')
        source=gate.specs.s6.corpus.source(task)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);inputs=root/'frozen';inputs.mkdir()
            (inputs/'source.md').write_text(source)
            evidence=gate.specs.contract(task['id'],source,'base')
            evidence['unresolved']=['An expectation has not been supported by the source']
            (inputs/'source-evidence.json').write_bytes(gate.p.challenges.encoded(evidence))
            manifest={'cases':[{'id':0,'frozen':str(inputs),'base_commit':'base','task':task['id'],'positive':True}],
                      'tasks':{task['id']:task},'models':{'sol':{},'luna':{}},'limits':{'jobs':4,'probe_seconds':30}}
            gate.p.write_record(root/'report.json',{'status':'DECLARED','controls':[],'readiness':[],
                'judgments':[],'recovery':[],'model_dispatches':0})
            with patch.object(gate.previous,'validate',return_value=manifest),patch.object(gate.p.host,'git',return_value='base'),\
                 patch.object(gate.p.host,'find_codex',return_value='codex'),\
                 patch.object(gate.specs.s6,'evaluate',return_value={'observed':True,'correct':True}),\
                 patch.object(gate.previous,'probe_control',return_value={'matched':True}),\
                 patch.object(gate.p.live,'run_stage') as native,patch.object(gate,'recovery') as recovery:
                result=gate.run(root)
            native.assert_not_called();recovery.assert_not_called()
            self.assertEqual(result['status'],'TRUST QUALIFICATION FAILED')
            self.assertEqual(result['model_dispatches'],0)
            self.assertEqual(len(result['judgments']),4)
            self.assertTrue(all(x['status']=='NOT EXECUTED' for x in result['judgments']))
