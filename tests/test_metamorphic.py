"""Representation evidence is generic and discriminates unsupported operations."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from checks import metamorphic


class Relations(unittest.TestCase):
    def test_unrelated_interface_preserves_order_and_rejects_numeric_narrowing(self):
        probe=metamorphic.representation_probe('values','arrange',[['*']],[[5,2,5],[1,3]],['ordering'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'probe.py';script.write_text(probe)
            for program,expected in (('def arrange(data): return sorted(data,reverse=True)',0),
                                     ('def arrange(data): return sorted(data,key=lambda value:-value)',1)):
                (root/'values.py').write_text(program)
                result=subprocess.run([sys.executable,'-I','-B',str(script),str(root)],capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stderr)
                if expected:self.assertIn('source-declared representation',result.stderr)

    def test_text_relation_preserves_error_families_and_rejects_instance_dispatch(self):
        probe=metamorphic.representation_probe('labels','canonicalize',[[]],['alpha',''],['text'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'probe.py';script.write_text(probe)
            for operation,expected in (('str.upper(data)',0),('data.upper()',1)):
                (root/'labels.py').write_text('class Blank(ValueError): pass\ndef canonicalize(data):\n'
                    '    if str.__len__(data)==0: raise Blank("blank")\n    return '+operation+'\n')
                result=subprocess.run([sys.executable,'-I','-B',str(script),str(root)],capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stderr)
                if expected:self.assertIn('source-declared representation',result.stderr)

    def test_invalid_or_unbounded_relation_is_not_compiled(self):
        for module,paths,samples in [('invalid/path',[['*']],[[1]]),
                                     ('values',[[True]],[[1]]),('values',[['*']]*7,[[1]]),
                                     ('values',[['*']],[])]:
            with self.assertRaises(ValueError):metamorphic.representation_probe(module,'arrange',paths,samples,['ordering']*len(paths))

    def test_integer_relation_rejects_optional_conversion_and_operators(self):
        probe=metamorphic.representation_probe('padding','increase',[[]],[0,2],['integer'])
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'probe.py';script.write_text(probe)
            for expression,expected in (('int.__int__(data)+7',0),('int(data)+7',1),('data+7',1)):
                (root/'padding.py').write_text('def increase(data): return '+expression+'\n')
                result=subprocess.run([sys.executable,'-I','-B',str(script),str(root)],capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stderr)
