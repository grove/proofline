"""Packaging observations; equivalent wording/layout is judged by source audit."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SkillPackaging(unittest.TestCase):
    def canonical(self):
        found = []
        for path in ROOT.rglob('SKILL.md'):
            if path.is_file() and re.search(r'''(?m)^name:\s*['"]?proofline-check['"]?\s*$''', path.read_text()):
                found.append(path.resolve())
        self.assertEqual(len(set(found)), 1, 'one maintained canonical definition')
        return found[0]

    def test_metadata_and_one_maintained_definition(self):
        self.assertTrue(self.canonical().read_text().startswith('---\n'))

    def test_root_entry_and_supported_installation_documented(self):
        self.assertTrue((ROOT / 'SKILL.md').is_file())
        text = (ROOT / 'README.md').read_text().lower()
        for term in ('proofline-check', 'codex', 'claude'):
            self.assertIn(term, text)

    def test_local_links_resolve_in_the_selected_layout(self):
        canonical = self.canonical()
        for match in re.finditer(r'\[[^\]]+\]\(([^)]+)\)', canonical.read_text()):
            target = match.group(1).split('#', 1)[0]
            if target and not re.match(r'[a-z]+:', target):
                self.assertTrue((canonical.parent / target).exists(), target)
        for agent in ('.agents', '.claude'):
            entry = ROOT / agent / 'skills' / 'proofline-check' / 'SKILL.md'
            if entry.exists():
                self.assertEqual(entry.resolve(), canonical)

    def test_install_copy_retains_skill_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            shutil.copytree(self.canonical().parent, Path(temporary) / 'proofline-check')
            copied = (Path(temporary) / 'proofline-check' / 'SKILL.md').read_bytes()
            self.assertEqual(copied, self.canonical().read_bytes())

    def test_python_cli_keeps_run_check_status(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'proofline.py'), '--help'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ('run', 'check', 'status'):
            self.assertIn(command, result.stdout)
