"""Mechanical S1 checks; live model acceptance is recorded separately."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as delivery

host = delivery.host


class DeliveryTests(unittest.TestCase):
    def test_verifiers_challenge_source_domains_without_benchmark_answers(self):
        inputs = Path('/disposable/inputs')
        for role in ('reviewer', 'prover'):
            text = delivery.prompt(role, inputs, {}, ids=('R1',), execution_map='Public interface')
            self.assertIn('every clause within each criterion', text)
            self.assertIn('inherited runtime limits', text)
            self.assertIn('which plausible defect the evidence discriminates', text)
            self.assertIn('A coverage qualifier cannot excuse a knowingly narrower domain', text)
            self.assertIn('candidate\'s algorithm, operator, or library', text)
            self.assertNotIn('2024-061', text)
        text = delivery.prompt('implementer', inputs, {}, ids=('R1',), execution_map='Public interface')
        self.assertNotIn('which plausible defect the evidence discriminates', text)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.repo = self.work / "source"
        self.repo.mkdir()
        (self.repo / "entry.py").write_bytes(b"print('original')\n")
        (self.repo / "entry.py").chmod(0o755)
        (self.repo / ".gitattributes").write_text("entry.py export-ignore\n")
        (self.repo / ".gitignore").write_text("ignored\n")
        host.git(self.repo, "init", "--quiet", "--template=")
        host.git(self.repo, "add", "--all")
        host.git(self.repo, "commit", "--quiet", "-m", "Source")

    def test_capture_preserves_exact_bytes_modes_and_export_ignored_files(self):
        (self.repo / "ignored").write_text("local cache or secret")
        before = host.snapshot(self.repo)
        product = self.work / "product"
        source, base = delivery.capture_base(self.repo, product)
        self.assertEqual((product / "entry.py").read_bytes(), b"print('original')\n")
        self.assertEqual((product / "entry.py").stat().st_mode & 0o777, 0o755)
        self.assertFalse((product / "ignored").exists())
        self.assertEqual(host.git(product, "rev-parse", base + "^{tree}"),
                         host.git(self.repo, "rev-parse", source + "^{tree}"))
        self.assertEqual(host.snapshot(self.repo), before)

    def test_dirty_source_and_links_are_not_silently_dropped(self):
        (self.repo / "entry.py").write_text("user change")
        with self.assertRaisesRegex(delivery.InputGap, "local changes"):
            delivery.capture_base(self.repo, self.work / "dirty-copy")
        host.git(self.repo, "add", "--all")
        host.git(self.repo, "commit", "--quiet", "-m", "Preserve user work")
        (self.repo / "link").symlink_to("../outside")
        host.git(self.repo, "add", "--all")
        host.git(self.repo, "commit", "--quiet", "-m", "Link")
        with self.assertRaisesRegex(delivery.InputGap, "Symlink"):
            delivery.capture_base(self.repo, self.work / "link-copy")

    def test_relative_internal_aliases_preserve_tree_and_reject_git_or_directory_links(self):
        (self.repo / "alias.py").symlink_to("entry.py")
        host.git(self.repo, "add", "--all")
        host.git(self.repo, "commit", "--quiet", "-m", "Internal alias")
        product = self.work / "product"
        _, base = delivery.capture_base(self.repo, product)
        self.assertTrue((product / "alias.py").is_symlink())
        self.assertEqual((product / "alias.py").read_bytes(), b"print('original')\n")
        _, tree = delivery.freeze(product)
        self.assertEqual(tree, host.git(product, "rev-parse", base + "^{tree}"))
        outside = self.work / "outside-alias"
        outside.symlink_to(product / "entry.py")
        for name, target in (("git-link", ".git/config"), ("dir-link", "."), ("cycle", "cycle"),
                             ("external-hop", "../outside-alias")):
            path = product / name
            path.symlink_to(target)
            with self.assertRaises(delivery.InputGap):
                delivery.freeze(product)
            path.unlink()

    def test_candidate_freeze_includes_new_ignored_files_and_rejects_external_links(self):
        product = self.work / "product"
        _, base = delivery.capture_base(self.repo, product)
        (product / "ignored").write_text("new executable input")
        candidate, tree = delivery.freeze(product)
        self.assertNotEqual(base, candidate)
        self.assertEqual(delivery.git_bytes(product, "show", candidate + ":ignored"), b"new executable input")
        (product / "outside").symlink_to(self.repo / "entry.py")
        with self.assertRaisesRegex(delivery.InputGap, "link"):
            delivery.freeze(product)

    def test_complete_diff_is_not_truncated_or_redacted(self):
        product = self.work / "product"
        _, base = delivery.capture_base(self.repo, product)
        text = "user@example.invalid\n" + "long line\n" * 4000
        (product / "entry.py").write_text(text)
        delivery.freeze(product)
        path = self.work / "diff"
        host.write_diff(product, base, path)
        self.assertGreater(path.stat().st_size, host.MAX_LOG_BYTES)
        self.assertIn("+user@example.invalid", path.read_text())
        self.assertEqual(path.read_text().count("+long line"), 4000)

    def test_nested_repository_cannot_hide_product_bytes_behind_a_gitlink(self):
        product = self.work / "product"
        delivery.capture_base(self.repo, product)
        (product / "nested" / ".git").mkdir(parents=True)
        (product / "nested" / "code.py").write_text("print('not a submodule')")
        with self.assertRaisesRegex(delivery.InputGap, "Nested Git"):
            delivery.freeze(product)

    def test_brief_requires_unique_material_ids_without_renumbering(self):
        self.assertEqual(delivery.criterion_ids("| ID | Outcome |\n| AC-9 | Required |\n| D2 | Other |"), ["AC-9", "D2"])
        for text in ("No criteria", "| D1 | A |\n| D1 | B |"):
            with self.assertRaises(delivery.InputGap):
                delivery.criterion_ids(text)

    def test_stale_candidate_and_missing_receipts_never_return_saved_acceptance(self):
        inputs = self.work / "inputs"
        inputs.mkdir()
        (inputs / "source.md").write_text("source")
        (inputs / "accepted-input.md").write_text("| D1 | Outcome |")
        _, base = delivery.capture_base(self.repo, inputs / "product")
        delivery.freeze(inputs / "product")
        record = {"schema_version": 1, "kind": "direct_local_delivery", "status": "LOCAL ACCEPTED",
                  "candidate_path": str(inputs / "product"), "snapshot": host.snapshot(inputs)["sha256"],
                  "identities": delivery.identities(inputs, base), "stages": [], "model_dispatches": 0}
        path = self.work / "report.json"
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "Missing independent"):
            delivery.inspect_record(path)
        (inputs / "product" / "entry.py").write_text("post-check change")
        self.assertEqual(delivery.inspect_record(path)["status"], "NOT VERIFIED")

    def test_missing_host_stops_before_any_model_dispatch_and_preserves_record(self):
        output = self.work / "delivery"
        with patch.object(delivery.platform, "system", return_value="Darwin"), patch.object(host, "find_codex", return_value=None), patch.object(delivery.live, "launch") as launch:
            result = delivery.deliver(self.repo, "source", "| D1 | Outcome |", output)
        launch.assert_not_called()
        self.assertEqual(result["status"], "INPUT NOT READY")
        self.assertEqual(result["model_dispatches"], 0)
        before = host.snapshot(output)
        with self.assertRaises(FileExistsError):
            delivery.deliver(self.repo, "source", "| D1 | Outcome |", output)
        self.assertEqual(host.snapshot(output), before)

    def test_material_review_failure_and_input_gap_skip_proof_and_retain_candidate(self):
        calls = []
        def stage(codex, directory, inputs, identity, role, preferences, allowance, **kwargs):
            calls.append(role)
            return {"role": role, "status": "OBSERVED", "thread_id": role, "report": {
                "verdict": "READY" if role == "implementer" else verdict,
                "findings": [] if role == "implementer" else findings, "summary": "Material gap found"}}
        def boundary(codex, directory, inputs, *args):
            for name in ("canary.py", "canary.json"):
                (inputs / name).write_text("native test double")
            return {"assessment": {"status": "OBSERVED"}}
        original_command = host.run_command
        def command(argv, *args, **kwargs):
            if argv == [sys.executable, "--version"]:
                return {"exit_code": 0, "timed_out": False, "stdout": "codex-cli 0.162.1"}
            return original_command(argv, *args, **kwargs)
        for verdict, findings, expected in (("FAIL", ["Material regression"], "BUDGET EXHAUSTED"),
                ("NOT VERIFIED", ["INPUT NOT READY: Original source promise omitted"], "INPUT NOT READY")):
            with self.subTest(expected=expected):
                calls.clear()
                with patch.object(delivery.platform, "system", return_value="Darwin"), patch.object(host, "find_codex", return_value=sys.executable), patch.object(host, "run_command", side_effect=command), patch.object(host, "probe_boundary", side_effect=boundary), patch.object(delivery.live, "preferences", return_value={}), patch.object(delivery.live, "run_stage", side_effect=stage):
                    result = delivery.deliver(self.repo, "source", "| D1 | Outcome |", self.work / expected, dispatches=3)
                self.assertEqual(calls, ["implementer", "reviewer"])
                self.assertEqual(result["status"], expected)
                self.assertTrue(Path(result["candidate_path"]).exists())
                self.assertFalse(result["published"])
                self.assertFalse(result["merged"])
