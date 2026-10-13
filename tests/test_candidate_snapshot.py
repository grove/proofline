"""Exact Git snapshot and frozen-candidate regressions; no model dispatches."""
import os
from pathlib import Path
import stat
import tempfile
import unittest

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

    def test_candidate_nested_git_metadata_cannot_be_frozen(self):
        product=self.root/"candidate"
        snapshot.capture_base(self.source,product)
        (product/"nested"/".git").mkdir(parents=True)
        (product/"nested"/".git"/"config").write_text("unsafe\n")
        with self.assertRaisesRegex(snapshot.InputGap,"Nested Git"):
            snapshot.freeze(product)


if __name__=="__main__":
    unittest.main()
