import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from checks import s6_baseline as baseline, s6_compare as s6


class BaselineTests(unittest.TestCase):
    def exercise(self, review=False, passed=True):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            item=s6.corpus.TASKS[0]
            s6.seed(root/'source',item)
            def boundary(codex,directory,inputs,*args):
                for name in ('canary.py','canary.json'):(inputs/name).write_text('canary')
                return {'assessment':{'status':'OBSERVED'}}
            responses=[{'thread_id':'coder','usage':{'input_tokens':10,'cached_input_tokens':0,'output_tokens':2},
                        'commands':{},'report':{'completed':True,'summary':'Finished'}}]
            if review:responses.append({'thread_id':'fresh-review','usage':responses[0]['usage'],'commands':{},
                                        'report':{'passed':passed,'summary':'Independent review'}})
            with patch.object(baseline.p.host,'probe_boundary',side_effect=boundary), \
                 patch.object(baseline.p.live,'launch',return_value={'exit_code':0,'timed_out':False,'elapsed_seconds':1}) as launch, \
                 patch.object(baseline.p.live,'read_events',side_effect=responses):
                result=baseline.run(root/'source',s6.corpus.source(item),s6.corpus.brief(item),root/'run',
                    review,'/fake/codex',{'model':'same'},900,240,s6.MAP)
            calls=launch.call_args_list
            first_schema=json.loads((root/'run/implementation/inputs/response.schema.json').read_text())
            self.assertEqual(set(first_schema['properties']),{'completed','summary'})
            self.assertNotIn('criterion IDs',calls[0].args[1])
            self.assertNotIn('binding',calls[0].args[1])
            self.assertGreater(calls[0].args[3],650 if review else 890)
            self.assertLessEqual(calls[0].args[3],660 if review else 900)
            if review:
                self.assertEqual(len(calls),2)
                self.assertLessEqual(calls[1].args[3],240)
                self.assertNotEqual(result['stages'][0]['thread_id'],result['stages'][1]['thread_id'])
            # A normal completion claim cannot bypass the separate acceptance oracle.
            score=s6.evaluate(Path(result['candidate']),item,directory=root/'oracle')
            self.assertFalse(score['correct'])
            return result

    def test_plain_agent_gets_whole_budget_and_no_proofline_handoff_protocol(self):
        result=self.exercise()
        self.assertTrue(result['accepted'])
        self.assertEqual(s6.classify(True,{'observed':True,'correct':False},result),'FALSE ACCEPTED')

    def test_independent_review_adds_no_correction_loop(self):
        result=self.exercise(review=True,passed=False)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['model_dispatches'],2)
