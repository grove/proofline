"""The only Proofline skill is discoverable without duplicating instructions.

These tests exercise checked-in symlinks and install packaging/metadata.
They do not claim that a model is guaranteed to invoke the skill.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skills" / "proofline-check" / "SKILL.md"
ALIASES = (
    ROOT / ".agents" / "skills" / "proofline-check",
    ROOT / ".claude" / "skills" / "proofline-check",
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def frontmatter(source):
    match = FRONTMATTER.match(source)
    if match is None:
        raise ValueError("No skill frontmatter")
    entries = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep or key in entries:
            raise ValueError("Malformed or duplicated skill metadata")
        entries[key] = value.strip()
    return entries


class SkillDiscovery(unittest.TestCase):
    def test_one_canonical_skill_has_action_name_and_useful_trigger(self):
        self.assertTrue(CANONICAL.is_file())
        metadata = frontmatter(CANONICAL.read_text(encoding="utf-8"))
        self.assertEqual(set(metadata), {"name", "description"})
        self.assertEqual(metadata["name"], "proofline-check")
        description = metadata["description"].lower()
        for term in ("after", "implements", "check", "frozen", "failure",
                     "missing evidence", "optional", "no models"):
            with self.subTest(term=term):
                self.assertIn(term, description)
        body = CANONICAL.read_text(encoding="utf-8")
        for command in ("proofline.py check", "proofline.py run", "run --correct-once",
                        "proofline.py status", "--promises", "--intentline-export"):
            with self.subTest(command=command):
                self.assertIn(command, body)

    def test_codex_and_claude_use_the_same_real_skill_directory(self):
        expected = CANONICAL.parent
        found = set()
        for alias in ALIASES:
            with self.subTest(alias=str(alias.relative_to(ROOT))):
                self.assertTrue(alias.is_symlink())
                self.assertEqual(alias.readlink().as_posix(), "../../skills/proofline-check")
                self.assertEqual(alias.resolve(strict=True), expected)
                self.assertEqual((alias / "SKILL.md").resolve(strict=True), CANONICAL)
                self.assertEqual(
                    (alias / "SKILL.md").read_bytes(), CANONICAL.read_bytes())
                found.add((alias / "SKILL.md").resolve(strict=True))
        self.assertEqual(found, {CANONICAL})

    def test_root_file_remains_a_linkable_migration_pointer_not_a_second_skill(self):
        root = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIsNone(FRONTMATTER.match(root))
        self.assertIn("(skills/proofline-check/SKILL.md)", root)
        self.assertIn("$proofline-check", root)
        self.assertIn("/proofline-check", root)
        self.assertIn("not", root.lower())
        self.assertIn("proofline.py check", root)
        self.assertIn("proofline.py status", root)
        self.assertNotIn("name: proofline", root)
        manifests = [p for p in ROOT.rglob("SKILL.md")
                     if ".proofline" not in p.relative_to(ROOT).parts
                     and FRONTMATTER.match(p.read_text(encoding="utf-8"))]
        self.assertEqual(manifests, [CANONICAL])

    def test_canonical_skill_references_do_not_break_when_installed_elsewhere(self):
        # A copied global skill must not depend on relative links back to
        # the Proofline repo. Runtime calls use an explicit checkout path.
        body = CANONICAL.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)\s]+)\)", body):
            with self.subTest(link=link):
                if link.startswith(("https://", "http://", "#")):
                    continue
                path = (CANONICAL.parent / link.split("#")[0]).resolve()
                self.assertTrue(path.is_file(), link)
        with tempfile.TemporaryDirectory() as tmp:
            for parent in (".agents", ".claude"):
                install = Path(tmp) / parent / "skills" / "proofline-check"
                install.parent.mkdir(parents=True)
                shutil.copytree(CANONICAL.parent, install)
                installed = install / "SKILL.md"
                self.assertEqual(frontmatter(installed.read_text())["name"], "proofline-check")
                self.assertEqual(installed.read_bytes(), CANONICAL.read_bytes())

    def test_readme_describes_both_locations_and_explicit_invocations(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        skill = "skills/proofline-check/SKILL.md"
        self.assertIn(f"]({skill})", readme)
        for phrase in (".agents/skills/proofline-check",
                       ".claude/skills/proofline-check",
                       "$HOME/.agents/skills/proofline-check",
                       "$HOME/.claude/skills/proofline-check",
                       "$proofline-check", "/proofline-check",
                       "automatic invocation is **not", "remove or rename"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)
        self.assertTrue((ROOT / "proofline.py").is_file())
        status = subprocess.run([sys.executable, "-B", str(ROOT / "proofline.py"),
                                 "--help"], cwd=ROOT, capture_output=True, text=True,
                                timeout=20)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("{run,check,status}", status.stdout)


if __name__ == "__main__":
    unittest.main()
