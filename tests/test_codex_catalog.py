"""Transport fault injection; fake servers never qualify model access."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks import codex_catalog as catalog
from evaluation.sol_luna import study


MODELS = study.protocol()['models']
SERVER = '''import json,select,sys,time
def receive(): return json.loads(sys.stdin.readline())
def send(value): print(json.dumps(value),flush=True)
assert receive()['method']=='initialize'
# A pipelined client would send initialized/model-list before successful init.
assert not select.select([sys.stdin],[],[],0.05)[0]
send({'id':1,'result':{}})
assert receive()['method']=='initialized'
request=receive()
assert request['method']=='model/list' and request['params']['includeHidden'] is True
send({'method':'remoteControl/status/changed','params':{}})
models=[{'id':m,'model':m,'supportedReasoningEfforts':[{'reasoningEffort':'high'}]}
        for m in ('gpt-6.1-sol','gpt-6-luna')]
send({'id':2,'result':{'data':models[:1],'nextCursor':'second'}})
request=receive()
assert request['id']==3 and request['params']['cursor']=='second'
send({'id':3,'result':{'data':models[1:],'nextCursor':None}})
time.sleep(10)
'''


class CatalogTests(unittest.TestCase):
    def run_server(self, code, *, timeout=3, limit=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        real_popen = subprocess.Popen
        processes = []
        def launch(argv, **kwargs):
            self.assertIn('app-server', argv)
            self.assertIn('stdio://', argv)
            self.assertNotIn('exec', argv)
            process = real_popen([sys.executable,'-I','-B','-c',code], **kwargs)
            processes.append(process)
            return process
        with patch.object(catalog.subprocess, 'Popen', side_effect=launch):
            try:
                with patch.object(catalog.live,'MAX_EVENTS_BYTES',limit or catalog.live.MAX_EVENTS_BYTES):
                    result = catalog.readback('codex', study.HERE/'model-catalog.json', MODELS, root, timeout=timeout)
            except Exception as error:
                result = error
        for process in processes:
            self.assertIsNotNone(process.poll())
            self.assertTrue(process.stdin.closed and process.stdout.closed and process.stderr.closed)
        return result, json.loads((root/'catalog-readback.json').read_text())

    def test_waits_for_initialization_and_reads_all_catalog_pages(self):
        result, record = self.run_server(SERVER)
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(record['model_dispatches'], 0)
        self.assertIn('NOT QUALIFIED', record['access'])
        self.assertEqual([m['id'] for m in record['responses'] if 'id' in m], [1,2,3])
        self.assertGreaterEqual(record['initialization_seconds'], .05)

    def test_startup_and_catalog_timeouts_are_distinct(self):
        for code, phase in [('import time; time.sleep(10)', 'initialize'),
                           (SERVER.split("send({'method':")[0]+'time.sleep(10)', 'model/list')]:
            result, record = self.run_server(code, timeout=.3)
            self.assertIsInstance(result, ValueError)
            self.assertIn('timeout during '+phase, record['error'])
            self.assertEqual(record['status'], 'NOT VERIFIED')

    def test_initialization_errors_exit_and_launch_failure_are_recorded(self):
        result, record = self.run_server("import json,sys; sys.stdin.readline(); print(json.dumps({'id':1,'error':{'message':'no'}}),flush=True)")
        self.assertIn('RPC failed during initialize', record['error'])
        result, record = self.run_server('import sys; sys.exit(7)')
        self.assertIn('EOF during initialize', record['error'])
        with tempfile.TemporaryDirectory() as temporary, patch.object(catalog.subprocess, 'Popen', side_effect=FileNotFoundError('missing')):
            with self.assertRaises(FileNotFoundError):
                catalog.readback('missing', study.HERE/'model-catalog.json', MODELS, Path(temporary))
            self.assertEqual(json.loads((Path(temporary)/'catalog-readback.json').read_text())['model_dispatches'],0)

    def test_wrong_effort_duplicate_model_and_repeated_cursor_fail_closed(self):
        for code in [SERVER.replace("'high'", "'medium'"),
                     SERVER.replace("models[1:]", "models"),
                     SERVER.replace("'data':models[1:],'nextCursor':None", "'data':models[1:],'nextCursor':'second'")]:
            result, record = self.run_server(code)
            self.assertIsInstance(result, ValueError)
            self.assertEqual(record['status'], 'NOT VERIFIED')

    def test_stderr_is_drained_and_oversized_output_is_rejected(self):
        result, record = self.run_server("import sys; sys.stderr.write('x'*10000); sys.stderr.flush();\n"+SERVER)
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(len(record['stderr']),10000)
        result, record = self.run_server("import sys,time; sys.stderr.write('x'*2000); sys.stderr.flush(); time.sleep(10)",limit=1000)
        self.assertIn('Oversized',record['error'])

    def test_existing_evidence_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'catalog-readback.json').write_text('preserve')
            with patch.object(catalog.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(ValueError,'overwrite'):
                    catalog.readback('codex',study.HERE/'model-catalog.json',MODELS,root)
            launch.assert_not_called()
            self.assertEqual((root/'catalog-readback.json').read_text(),'preserve')
