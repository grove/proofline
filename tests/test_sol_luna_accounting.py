import json
from pathlib import Path
import tempfile
import unittest

from evaluation.sol_luna import study
from evaluation.sol_luna_host.accounting import normalize


class NativeAccountingTests(unittest.TestCase):
    def result(self, initial=None, correction=None):
        stages=[]
        for name,usage in (('implementation',initial),('correction',correction)):
            stages.append({'stage':name,'model':'gpt-6-luna','reasoning_effort':'high',
                'thread_id':'same-luna','elapsed_seconds':1,'tool_executions':1,'usage':usage,'cost_usd':None})
        rows=study.ledger();rows[0].update(status='INCORRECT_NO_HANDOFF',stages=stages)
        return {'assignments':rows}

    def test_resumed_total_is_not_counted_twice_and_raw_evidence_is_unchanged(self):
        initial={'input_tokens':79736,'cached_input_tokens':59392,'output_tokens':1493}
        resumed={'input_tokens':158579,'cached_input_tokens':133120,'output_tokens':2169}
        raw=self.result(initial,resumed);before=json.dumps(raw)
        result=normalize(raw)
        corrected=result['assignments'][0]['stages'][1]
        self.assertEqual(corrected['usage'],{'input_tokens':78843,'cached_input_tokens':73728,'output_tokens':676})
        self.assertEqual(corrected['observed_session_usage'],resumed)
        self.assertEqual(result['metrics']['arms']['verify']['models']['gpt-6-luna']['tokens'],resumed)
        self.assertEqual(json.dumps(raw),before)

    def test_missing_initial_total_does_not_invent_correction_usage(self):
        result=normalize(self.result(None,{'input_tokens':100,'cached_input_tokens':50,'output_tokens':10}))
        self.assertIsNone(result['assignments'][0]['stages'][1]['usage'])
        self.assertIsNone(result['metrics']['arms']['verify']['models']['gpt-6-luna']['tokens']['input_tokens'])

    def test_counter_resets_bad_cache_and_changed_model_fail_closed(self):
        for initial,resumed in ((100,90),(100,110)):
            raw=self.result({'input_tokens':initial,'cached_input_tokens':50,'output_tokens':10},
                {'input_tokens':resumed,'cached_input_tokens':60,'output_tokens':20})
            if resumed==110:raw['assignments'][0]['stages'][1]['model']='gpt-6.1-sol'
            with self.assertRaises(ValueError):normalize(raw)
        raw=self.result({'input_tokens':100,'cached_input_tokens':101,'output_tokens':10})
        with self.assertRaises(ValueError):normalize(raw)

    def test_completed_usage_is_retained_after_timeout_without_upgrading_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'events.jsonl'
            usage={'input_tokens':100,'cached_input_tokens':50,'output_tokens':10}
            raw_events='\n'.join(json.dumps(e) for e in (
                {'type':'thread.started','thread_id':'same-luna'},
                {'type':'turn.completed','usage':usage}))+'\n'
            path.write_text(raw_events)
            raw=self.result(None,None);stage=raw['assignments'][0]['stages'][0]
            stage.update(status='NOT VERIFIED',receipt={'events_path':str(path),
                'events.jsonl_sha256':study.host.sha256(path.read_bytes()),'timed_out':True})
            result=normalize(raw)
            self.assertEqual(result['assignments'][0]['stages'][0]['usage'],usage)
            self.assertEqual(result['assignments'][0]['stages'][0]['status'],'NOT VERIFIED')
            self.assertTrue(result['assignments'][0]['stages'][0]['receipt']['timed_out'])
            path.write_text(raw_events+'{}\n')
            with self.assertRaisesRegex(ValueError,'evidence changed'):normalize(raw)
