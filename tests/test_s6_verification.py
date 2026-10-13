"""Evidence admissibility gates use real Python probes; native quality is separate."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from checks import s6_verification as gate


class Qualification(unittest.TestCase):
    def test_native_probe_gate_distinguishes_bad_expectation_narrowing_and_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);frozen=root/'frozen';(frozen/'product').mkdir(parents=True)
            (frozen/'source.md').write_text('Original promise')
            (frozen/'product/value.txt').write_text('correct')
            case={'id':0,'frozen':str(frozen),'positive':True}
            def plan(probe):
                return {'model':'offline','stage':{'report':{'criteria':[
                    {'id':'R1','source_quote':'Original promise','probe':probe}]}}}
            # No fake model or sandbox verdict: these are actual process checks of gate mechanics.
            with patch.object(gate,'oracle_runner',return_value=subprocess.run):
                good=plan('import sys\nfrom pathlib import Path\nassert (Path(sys.argv[1])/"value.txt").read_text()=="correct"')
                result=gate.probe_control(root/'good',case,good,None,5)
                self.assertTrue(result['matched']);self.assertTrue(result['unchanged'])
                bad=plan('assert False, "incorrect expected behavior"')
                self.assertFalse(gate.probe_control(root/'bad',case,bad,None,5)['matched'])
                narrowed=plan('pass')
                self.assertFalse(gate.probe_control(root/'narrow',dict(case,positive=False),narrowed,None,5)['matched'])
                mutating=plan('import sys\nfrom pathlib import Path\n(Path(sys.argv[1])/"value.txt").write_text("changed")')
                result=gate.probe_control(root/'mutation',case,mutating,None,5)
                self.assertFalse(result['observed']);self.assertFalse(result['matched'])
            def unavailable(*args,**kwargs):
                raise OSError('Native initialization unavailable')
            with patch.object(gate,'oracle_runner',return_value=unavailable):
                result=gate.probe_control(root/'unavailable',case,good,None,5)
                self.assertFalse(result['observed'])
                self.assertEqual(result['observations'][0]['status'],'NOT VERIFIED')
            with patch.object(gate,'oracle_runner',return_value=lambda *a,**k:subprocess.CompletedProcess(
                    a,1,'','sandbox-exec: sandbox_apply: Operation not permitted')):
                result=gate.probe_control(root/'initialization',case,good,None,5)
                self.assertFalse(result['observed'])

    def test_read_only_git_inspection_preserves_frozen_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);product=root/'product';product.mkdir()
            path=product/'value.txt';path.write_text('initial')
            gate.p.host.git(product,'init','--quiet','--template=')
            gate.p.host.git(product,'add','--all')
            gate.p.host.git(product,'commit','--quiet','-m','base')
            # Change file stat metadata with identical bytes, the prior native integrity failure.
            path.unlink();path.write_text('initial')
            before=(product/'.git/index').read_bytes()
            self.assertEqual(gate.p.host.git(product,'status','--porcelain'),'')
            self.assertEqual((product/'.git/index').read_bytes(),before)

    def test_adapter_guidance_has_no_candidate_logic_or_private_answers(self):
        mapping=gate.interface_map()
        self.assertIn('value = process(json.loads(sys.argv[1]))',mapping)
        self.assertIn('print(json.dumps(value',mapping)
        self.assertNotIn('def process(',mapping)
        self.assertNotIn('probes',mapping)
