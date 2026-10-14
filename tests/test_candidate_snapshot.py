"""Exact Git snapshot and frozen-candidate regressions; no model dispatches."""
import os
import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from checks import candidate_snapshot as snapshot
from checks import host_probe as host


class CandidateSnapshotTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix="proofline-snapshot-test-")
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.source=self.root/"source"
        self.source.mkdir()
        (self.source/"readme.md").write_text("original\n")
        (self.source/"script.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.source/"script.sh").chmod(0o755)
        host.git(self.source,"init","--quiet","--template=")
        host.git(self.source,"add","--all")
        host.git(self.source,"commit","--quiet","-m","Clean baseline")
        self.original=host.git(self.source,"rev-parse","HEAD")

    def test_copy_and_freeze_preserve_original_source(self):
        product=self.root/"candidate"
        source_sha,base_sha=snapshot.capture_base(self.source,product)
        self.assertEqual(source_sha,self.original)
        self.assertEqual((product/"readme.md").read_text(),"original\n")
        self.assertEqual(stat.S_IMODE((product/"script.sh").stat().st_mode),0o755)
        self.assertEqual(host.git(product,"rev-parse","HEAD"),base_sha)
        (product/"readme.md").write_text("changed candidate\n")
        candidate_sha,candidate_tree=snapshot.freeze(product)
        self.assertEqual(host.git(product,"rev-parse","HEAD"),candidate_sha)
        self.assertEqual(host.git(product,"rev-parse","HEAD^{tree}"),candidate_tree)
        self.assertNotEqual(candidate_sha,base_sha)
        self.assertEqual(host.git(self.source,"rev-parse","HEAD"),self.original)
        self.assertEqual((self.source/"readme.md").read_text(),"original\n")
        self.assertEqual(host.git(self.source,"status","--porcelain"),"")

    def test_freeze_suppresses_automatic_packing_of_protected_git_metadata(self):
        product = self.root / 'candidate'
        snapshot.capture_base(self.source, product)
        host.git(product, 'config', 'gc.auto', '1')
        host.git(product, 'config', 'gc.autoDetach', 'false')
        host.git(product, 'config', 'maintenance.auto', 'true')
        # Git's loose-object heuristic samples bucket 17; force that bucket over its threshold.
        loose = []
        for value in range(10000):
            data = str(value).encode()
            oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if oid.startswith('17'):
                loose.append(oid)
                (product / ('new-file-' + str(len(loose)))).write_bytes(data)
                if len(loose) == 2:
                    break
        else:
            self.fail('No loose-object fixture found')
        snapshot.freeze(product)
        for oid in loose:
            self.assertTrue((product / '.git/objects/17' / oid[2:]).is_file())
        self.assertEqual(list((product / '.git/objects/pack').iterdir()), [])

    def test_dirty_and_untracked_source_are_never_discarded(self):
        (self.source/"readme.md").write_text("dirty user work\n")
        with self.assertRaisesRegex(snapshot.InputGap,"local changes"):
            snapshot.capture_base(self.source,self.root/"candidate1")
        self.assertEqual((self.source/"readme.md").read_text(),"dirty user work\n")
        (self.source/"readme.md").write_text("original\n")
        (self.source/"new.txt").write_text("untracked user work\n")
        with self.assertRaisesRegex(snapshot.InputGap,"local changes"):
            snapshot.capture_base(self.source,self.root/"candidate2")
        self.assertEqual((self.source/"new.txt").read_text(),"untracked user work\n")
        self.assertFalse((self.root/"candidate2").exists())

    def test_source_symlink_outside_snapshot_is_rejected(self):
        outside=self.root/"secret.txt"
        outside.write_text("outside\n")
        (self.source/"alias").symlink_to(outside)
        host.git(self.source,"add","--all")
        host.git(self.source,"commit","--quiet","-m","Add unsafe symlink")
        with self.assertRaisesRegex(snapshot.InputGap,"Symlink escapes"):
            snapshot.capture_base(self.source,self.root/"candidate")
        self.assertEqual(outside.read_text(),"outside\n")

    def skill_layout(self):
        checkout = Path(__file__).resolve().parents[1]
        canonical = Path('skills/proofline-check/SKILL.md')
        (self.source / canonical).parent.mkdir(parents=True)
        (self.source / canonical).write_bytes((checkout / canonical).read_bytes())
        aliases = [Path(agent) / 'skills/proofline-check' for agent in ('.agents', '.claude')]
        for alias in aliases:
            (self.source / alias).parent.mkdir(parents=True)
            (self.source / alias).symlink_to(os.readlink(checkout / alias))
        return aliases

    def test_clean_git_snapshot_retains_real_skill_directory_and_file_aliases(self):
        aliases = self.skill_layout() + [Path('file-alias')]
        (self.source / 'file-alias').symlink_to('readme.md')
        host.git(self.source, 'add', '--all')
        host.git(self.source, 'commit', '--quiet', '-m', 'Skill discovery layout')
        before = host.snapshot(self.source)
        product = self.root / 'candidate'
        snapshot.capture_base(self.source, product)
        self.assertEqual(host.git(product, 'rev-parse', 'HEAD^{tree}'),
                         host.git(self.source, 'rev-parse', 'HEAD^{tree}'))
        for alias in aliases:
            self.assertEqual(os.readlink(product / alias), os.readlink(self.source / alias))
            self.assertEqual((product / alias).lstat().st_mode, (self.source / alias).lstat().st_mode)
            self.assertTrue(host.git(product, 'ls-tree', 'HEAD', str(alias)).startswith('120000 blob '))
        self.assertEqual(host.snapshot(self.source), before)

    def test_working_snapshot_retains_tracked_dirty_and_untracked_directory_aliases(self):
        aliases = self.skill_layout()
        if hasattr(os, 'lchmod'):
            os.lchmod(self.source / aliases[0], 0o700)
        host.git(self.source, 'add', '--all')
        host.git(self.source, 'commit', '--quiet', '-m', 'Skill discovery layout')
        trees = []
        for state in ('tracked', 'dirty', 'untracked'):
            with self.subTest(state=state):
                if state == 'dirty':
                    (self.source / aliases[0]).unlink()
                    (self.source / aliases[0]).symlink_to('../../skills/./proofline-check/')
                    (self.source / 'skills/proofline-check/SKILL.md').write_text('dirty canonical skill')
                elif state == 'untracked':
                    host.git(self.source, 'rm', '--cached', str(aliases[1]))
                before = host.snapshot(self.source)
                product = self.root / state
                selection = snapshot.capture_worktree(self.source, product)
                trees.append(selection['candidate_tree'])
                entries = {entry['path']: entry for entry in selection['entries']}
                for alias in aliases:
                    self.assertEqual(entries[str(alias)], {
                        'path': str(alias), 'mode': stat.S_IMODE((self.source / alias).lstat().st_mode),
                        'kind': 'symlink', 'target': os.readlink(self.source / alias)})
                    self.assertEqual(os.readlink(product / alias), os.readlink(self.source / alias))
                    self.assertEqual(stat.S_IMODE((product / alias).lstat().st_mode), entries[str(alias)]['mode'])
                    self.assertEqual((product / alias / 'SKILL.md').read_bytes(),
                                     (self.source / 'skills/proofline-check/SKILL.md').read_bytes())
                    self.assertFalse(any(name.startswith(str(alias) + '/') for name in entries))
                    self.assertTrue(host.git(product, 'ls-tree', 'HEAD', str(alias)).startswith('120000 blob '))
                self.assertEqual(host.snapshot(self.source), before)
        self.assertNotEqual(trees[0], trees[1])
        self.assertEqual(trees[1], trees[2])

    def test_links_reject_unsafe_literal_targets_without_resolving_them(self):
        (self.source / 'directory').mkdir()
        (self.source / 'directory/file').write_text('safe')
        real_resolve = Path.resolve
        targets = [str(self.source / 'readme.md'), str(self.source / 'directory'),
                   '../secret', '../source/readme.md', '.git/HEAD', '.GiT/HEAD',
                   '.gIt/../readme.md', 'missing', 'missing/../readme.md',
                   'hop/file', 'hop/../readme.md', 'hop', 'cycle-a', '.',
                   'readme.md/..', 'readme.md/.', 'readme.md/']
        for target in targets:
            with self.subTest(target=target):
                alias = self.source / 'alias'
                alias.symlink_to(target)
                if target.startswith('hop'):
                    (self.source / 'hop').symlink_to('directory')
                elif target == 'cycle-a':
                    (self.source / 'cycle-a').symlink_to('cycle-b')
                    (self.source / 'cycle-b').symlink_to('cycle-a')
                with patch.object(Path, 'resolve', autospec=True, side_effect=real_resolve) as resolve:
                    with self.assertRaises(snapshot.InputGap):
                        snapshot.validate_links(self.source)
                    self.assertEqual([call.args[0] for call in resolve.call_args_list], [self.source])
                alias.unlink()
                for helper in ('hop', 'cycle-a', 'cycle-b'):
                    (self.source / helper).unlink(missing_ok=True)

    def test_directory_targets_reject_nested_aliases_metadata_and_special_files(self):
        aliases = self.skill_layout()
        canonical = self.source / 'skills/proofline-check'
        for target in ('../../readme.md', '.', 'missing'):
            with self.subTest(nested=target):
                nested = canonical / 'nested'
                nested.symlink_to(target)
                with self.assertRaises(snapshot.InputGap):
                    snapshot.capture_worktree(self.source, self.root / ('nested-' + str(len(target))))
                nested.unlink()
        (canonical / '.GiT').mkdir()
        (canonical / '.GiT/config').write_text('metadata')
        with self.assertRaises(snapshot.InputGap):
            snapshot.capture_worktree(self.source, self.root / 'metadata')
        (canonical / '.GiT/config').unlink()
        (canonical / '.GiT').rmdir()
        os.mkfifo(canonical / 'pipe')
        with self.assertRaises(snapshot.InputGap):
            snapshot.capture_worktree(self.source, self.root / 'special')
        (canonical / 'pipe').unlink()
        (self.source / aliases[0]).unlink()
        (self.source / aliases[0]).symlink_to('..')
        with self.assertRaises(snapshot.InputGap):
            snapshot.capture_worktree(self.source, self.root / 'ancestor')

    def test_directory_alias_edits_during_capture_refuse_the_snapshot(self):
        alias = self.skill_layout()[0]
        original = snapshot._working_files
        def changing(repo, product=None):
            if product is None:
                (repo / alias).unlink()
                (repo / alias).symlink_to('../../skills/./proofline-check')
            return original(repo, product)
        with patch.object(snapshot, '_working_files', side_effect=changing):
            with self.assertRaisesRegex(snapshot.InputGap, 'changed during snapshot'):
                snapshot.capture_worktree(self.source, self.root / 'candidate')

    def test_external_symlink_chain_is_not_followed_during_discovery_or_validation(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'secret').write_text('must not be copied')
        os.mkfifo(outside / 'pipe')
        (outside / 'return').symlink_to(self.source, target_is_directory=True)
        (self.source / 'hop').symlink_to('../outside', target_is_directory=True)
        (self.source / 'alias').symlink_to('hop/return/readme.md')
        before = host.snapshot(self.source)
        product = self.root / 'candidate'
        real_open = os.open
        def no_external_open(path, *args, **kwargs):
            self.assertNotIn(str(outside), os.fspath(path))
            self.assertNotIn(os.fspath(path), ('secret', 'pipe', 'return'))
            return real_open(path, *args, **kwargs)
        with patch.object(snapshot.os, 'open', side_effect=no_external_open):
            with self.assertRaises(snapshot.InputGap):
                snapshot.capture_worktree(self.source, product)
        self.assertFalse(any(entry['path'].startswith('hop/') for entry in host.snapshot(product)['entries']))
        self.assertEqual(host.snapshot(self.source), before)

    def test_special_alias_targets_are_rejected_without_opening_them(self):
        os.mkfifo(self.source / 'pipe')
        alias = self.source / 'alias'
        alias.symlink_to('pipe')
        real_stat = os.stat
        for mode in (stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK):
            with self.subTest(mode=mode):
                def special(path, *args, **kwargs):
                    if path == 'pipe':
                        return os.stat_result((mode | 0o600,) + (0,) * 9)
                    return real_stat(path, *args, **kwargs)
                with patch.object(snapshot.os, 'stat', side_effect=special):
                    with self.assertRaises(snapshot.InputGap):
                        snapshot.validate_links(self.source)

    def test_candidate_nested_git_metadata_cannot_be_frozen(self):
        product=self.root/"candidate"
        snapshot.capture_base(self.source,product)
        (product/"nested"/".git").mkdir(parents=True)
        (product/"nested"/".git"/"config").write_text("unsafe\n")
        with self.assertRaisesRegex(snapshot.InputGap,"Nested Git"):
            snapshot.freeze(product)

    def test_worktree_rejects_special_files_without_opening_them(self):
        os.mkfifo(self.source / 'pipe')
        before = host.snapshot(self.source / '.git')
        with self.assertRaisesRegex(snapshot.InputGap, 'regular files'):
            snapshot.capture_worktree(self.source, self.root / 'candidate')
        self.assertTrue(stat.S_ISFIFO((self.source / 'pipe').lstat().st_mode))
        self.assertEqual(host.snapshot(self.source / '.git'), before)

    def test_worktree_rejects_escape_links_and_symlinked_parents(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'secret').write_text('outside data')
        (self.source / 'alias').symlink_to('../outside/secret')
        with self.assertRaises(snapshot.InputGap):
            snapshot.capture_worktree(self.source, self.root / 'bad-link')
        (self.source / 'alias').unlink()
        directory = self.source / 'directory'
        directory.mkdir()
        (directory / 'secret').write_text('tracked')
        host.git(self.source, 'add', '--all')
        (directory / 'secret').unlink()
        directory.rmdir()
        directory.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            snapshot.capture_worktree(self.source, self.root / 'bad-parent')
        self.assertEqual((outside / 'secret').read_text(), 'outside data')

    def test_worktree_rejects_submodules_and_nested_repositories(self):
        host.git(self.source, 'update-index', '--add', '--cacheinfo', '160000,' + self.original + ',module')
        with self.assertRaisesRegex(snapshot.InputGap, 'Submodules'):
            snapshot.capture_worktree(self.source, self.root / 'module-candidate')
        host.git(self.source, 'update-index', '--force-remove', 'module')
        nested = self.source / 'nested'
        nested.mkdir()
        host.git(nested, 'init', '--quiet', '--template=')
        (nested / 'file').write_text('nested')
        snapshot.freeze(nested)
        with self.assertRaises(snapshot.InputGap):
            snapshot.capture_worktree(self.source, self.root / 'nested-candidate')

    def test_concurrent_worktree_edits_refuse_a_mixed_snapshot(self):
        original = snapshot._working_files
        def changing(repo, product=None):
            if product is None:
                (repo / 'readme.md').write_text('concurrent edit')
            return original(repo, product)
        with patch.object(snapshot, '_working_files', side_effect=changing):
            with self.assertRaisesRegex(snapshot.InputGap, 'changed during snapshot'):
                snapshot.capture_worktree(self.source, self.root / 'candidate')
        self.assertEqual((self.source / 'readme.md').read_text(), 'concurrent edit')


if __name__=="__main__":
    unittest.main()
