"""Synthetic parser controls are not approval evidence or live S2 qualification."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline
from contract_input import adopted_contract, inspect_contract


CONTRACT = """# Acceptance contract: Greeting version

Contract revision: v2
Source: [Original request](source.md)
Parent: None
Prerequisites: None
Intended outcome: Show the version without a name, preserving greetings.

## Acceptance matrix

| ID | Source | Requirement | Boundaries / counterexamples | Seam | Oracle | Planned evidence | Plan state |
|---|---|---|---|---|---|---|---|
| R7 | Source | Version without name | Missing name | CLI | greet 1.0 | CLI probe | planned |
| R9 | Source | Preserve greetings | Spaces and Unicode | CLI | Exact supplied name | CLI probe | planned |

## Unresolved gaps

- None

## Open questions

- None

## Out of scope

- Dependencies and publication

## Change notes

- v2: retained stable R7 and R9; synthetic parser test, not approved.
"""


class ContractInputTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.path = self.work / "contract.md"
        self.path.write_bytes(CONTRACT.replace("\n", "\r\n").encode())
        (self.work / "source.md").write_bytes(b"Add --version; preserve greetings.\r\n")

    def test_exact_bytes_revision_ids_and_exclusions_survive(self):
        before = proofline.host.snapshot(self.work)
        metadata, source, contract = inspect_contract(self.path)
        self.assertEqual(metadata["revision"], "v2")
        self.assertEqual(metadata["criterion_ids"], ["R7", "R9"])
        self.assertEqual(contract.encode(), self.path.read_bytes())
        self.assertEqual(source.encode(), (self.work / "source.md").read_bytes())
        self.assertIn("Dependencies and publication", contract)
        self.assertNotIn("approval", metadata)
        self.assertFalse(metadata["parent_completion"])
        self.assertEqual(proofline.host.snapshot(self.work), before)

    def test_missing_and_stale_adoption_never_grants_authority(self):
        metadata, _, _ = inspect_contract(self.path)
        for contract_hash, source_hash, reference in (
            (None, None, None), (metadata["contract_sha256"], metadata["source_sha256"], ""),
            ("0" * 64, metadata["source_sha256"], "synthetic test only"),
            (metadata["contract_sha256"], "0" * 64, "synthetic test only"),
        ):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                adopted_contract(self.path, contract_hash, source_hash, reference)
        # Mechanics only: this synthetic reference is never sent to a worker.
        result, _, _ = adopted_contract(self.path, metadata["contract_sha256"],
                                       metadata["source_sha256"], "synthetic parser assertion")
        self.assertEqual(result["approval"]["kind"], "explicit-user-adoption")
        (self.work / "source.md").write_text("Changed original promise")
        with self.assertRaisesRegex(ValueError, "changed since adoption"):
            adopted_contract(self.path, metadata["contract_sha256"], metadata["source_sha256"], "synthetic")

    def test_unsupported_incomplete_and_ambiguous_inputs_are_actionable(self):
        changes = (
            ("Parent: None", "Parent: [Parent](parent.md)"),
            ("Prerequisites: None", "Prerequisites: Issue 7 is closed"),
            ("Parent: None", "Parent: None\nContribution: R1"),
            ("Contract revision: v2", "Contract revision: v2\nContract revision: v3"),
            ("[Original request](source.md)", "[Original request](https://example.com/source.md)"),
            ("[Original request](source.md)", "[Original request](missing.md)"),
            ("| planned |", "| proven |"),
            ("| R9 |", "| R7 |"),
            ("- None", "- Unresolved decision"),
            ("## Open questions", "## Unresolved gaps"),
            ("| Exact supplied name |", "| |"),
        )
        for old, new in changes:
            with self.subTest(new=new):
                self.path.write_text(CONTRACT.replace(old, new))
                with self.assertRaises((ValueError, OSError)):
                    inspect_contract(self.path)

    def test_unapproved_contract_records_input_gap_before_host_or_model(self):
        with patch.object(proofline.host, "find_codex") as host, patch.object(proofline.live, "launch") as launch:
            record = proofline.deliver(self.work, "", "", self.work / "run", contract_request={
                "path": self.path, "contract_sha256": None, "source_sha256": None, "approval_reference": None})
        self.assertEqual(record["status"], "INPUT NOT READY")
        self.assertEqual(record["model_dispatches"], 0)
        self.assertTrue((self.work / "run" / "report.json").exists())
        host.assert_not_called()
        launch.assert_not_called()
