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
    def test_worker_authority_binding_does_not_inherit_old_peer_verdicts(self):
        metadata = {"scope": "standalone", "approval": {"kind": "inspected-p2p-approval",
            "reference": "Actual original approval", "sha256": "a" * 64, "content": "Old review/proof reports"}}
        context = proofline.worker_context(metadata)
        self.assertNotIn("content", context["approval"])
        self.assertEqual(context["approval"]["sha256"], "a" * 64)
        self.assertEqual(metadata["approval"]["content"], "Old review/proof reports")

    def test_preservation_constraint_requires_source_bound_predecessor_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / ".p2p/work/previous"
            previous.mkdir(parents=True)
            candidate = "a" * 64
            documents = [previous / name for name in ("contract.md", "review.md", "proof.md")]
            for document in documents:
                document.write_text("Synthetic preserved predecessor " + candidate)
            hashes = [proofline.host.sha256(p.read_bytes()) for p in documents]
            work = root / ".p2p/work/correction"
            work.mkdir()
            (work / "source.md").write_text(f"reviewed recovery candidate: `snapshot:sha256:{candidate}`; prior P2P contract is `.p2p/work/previous/contract.md` v1, SHA-256 `{hashes[0]}`; its saved review and proof reports are identified by SHA-256 `{hashes[1]}` and `{hashes[2]}`.\n\n## Exact reviewed predecessor patch\nSynthetic offline patch")
            contract = work / "contract.md"
            contract.write_text(CONTRACT.replace("Prerequisites: None", "Prerequisites: Preserve the exact reviewed predecessor candidate and the issue #72 approval/transition records. Do not run the live-evaluation script or install this candidate before matching fresh review and proof."))
            metadata, _, _ = inspect_contract(contract)
            self.assertEqual(len(metadata["context_files"]), 3)
            self.assertEqual(metadata["scope"], "standalone")
            for document in documents:
                raw = document.read_bytes()
                document.write_bytes(raw + b"changed")
                with self.assertRaisesRegex(ValueError, "Predecessor"):
                    inspect_contract(contract)
                document.write_bytes(raw)

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

    def test_inspected_approval_is_bound_and_preserved_not_inferred(self):
        metadata, _, _ = inspect_contract(self.path)
        approval = self.work / "approval.md"
        approval.write_text("User approved exact v2 " + metadata["contract_sha256"])
        args = (self.path, metadata["contract_sha256"], metadata["source_sha256"], "inspected conversation reference")
        result, _, _ = adopted_contract(*args, approval, proofline.host.sha256(approval.read_bytes()))
        self.assertEqual(result["approval"]["kind"], "inspected-p2p-approval")
        self.assertEqual(result["approval"]["content"].encode(), approval.read_bytes())
        approval.write_text("approved")
        with self.assertRaisesRegex(ValueError, "approval reference changed"):
            adopted_contract(*args, approval, result["approval"]["sha256"])

    def test_child_preserves_source_chain_and_rejects_changed_parent_or_plan(self):
        parent = self.work / "parent.md"
        parent.write_text(CONTRACT)
        plan = self.work / "slicing.md"
        section = "## Approved delivery plan\nChild contribution R7; parent completion requires full proof.\n\n"
        plan.write_text(section + "## Notes\nNo extra effects.\n")
        child = CONTRACT.replace("Parent: None", f"Parent: [Parent](parent.md)\nParent snapshot: SHA-256 {proofline.host.sha256(parent.read_bytes())}\nContribution: [Plan](slicing.md), section SHA-256 {proofline.host.sha256(section.encode())}").replace("[Original request](source.md)", "[Parent](parent.md)").replace("| R7 | Source |", "| R7 | Parent v2:R7 |").replace("| R9 | Source |", "| R9 | Parent v2:R9 |")
        self.path.write_text(child)
        metadata, source, accepted = inspect_contract(self.path)
        self.assertEqual(metadata["scope"], "child")
        self.assertFalse(metadata["parent_completion"])
        self.assertIn("Add --version; preserve greetings.", source)
        self.assertEqual(accepted, child)
        self.assertEqual(len(metadata["source_files"]), 2)
        self.assertEqual(len(metadata["context_files"]), 2)
        self.path.write_text(child.replace("Parent v2:R9", "Parent v2:R999"))
        with self.assertRaisesRegex(ValueError, "source-qualified mapping"):
            inspect_contract(self.path)
        self.path.write_text(child)
        plan.write_text(section.replace("R7", "R9") + "## Notes\n")
        with self.assertRaisesRegex(ValueError, "Contribution plan changed"):
            inspect_contract(self.path)
        plan.write_text(section)
        parent.write_text(CONTRACT + "\nNew parent promise\n")
        with self.assertRaisesRegex(ValueError, "Parent snapshot changed"):
            inspect_contract(self.path)

    def test_source_cycles_and_unrecoverable_transitive_promises_are_rejected(self):
        parent = self.work / "parent.md"
        parent.write_text(CONTRACT.replace("source.md", "contract.md"))
        self.path.write_text(CONTRACT.replace("source.md", "parent.md"))
        with self.assertRaisesRegex(ValueError, "Cyclic source chain"):
            inspect_contract(self.path)
        parent.write_text(CONTRACT.replace("source.md", "missing.md"))
        with self.assertRaises(OSError):
            inspect_contract(self.path)

    def test_combined_parent_keeps_all_criteria_and_needs_its_own_acceptance(self):
        self.path.write_text(CONTRACT + "\n## Children\n\n| R1 | Historical child success |\n")
        metadata, _, _ = inspect_contract(self.path)
        self.assertEqual(metadata["scope"], "combined-parent")
        self.assertEqual(metadata["criterion_ids"], ["R7", "R9"])
        self.assertFalse(metadata["parent_completion"])

    def test_stale_and_incomplete_inputs_stop_before_dispatch(self):
        metadata, _, _ = inspect_contract(self.path)
        changes = (("stale-contract", {"contract_sha256": "0" * 64}),
                   ("stale-source", {"source_sha256": "0" * 64}),
                   ("unapproved", {"approval_reference": None}),
                   ("prerequisite", {}), ("incomplete", {}))
        for name, changes in changes:
            self.path.write_text(CONTRACT.replace("Prerequisites: None", "Prerequisites: Issue 7 closed") if name == "prerequisite" else
                                 CONTRACT.replace("| CLI probe |", "| |") if name == "incomplete" else CONTRACT)
            current, _, _ = inspect_contract(self.path) if name not in {"prerequisite", "incomplete"} else (metadata, None, None)
            request = {"path": self.path, "contract_sha256": current["contract_sha256"],
                       "source_sha256": current["source_sha256"], "approval_reference": "synthetic offline test only", **changes}
            with patch.object(proofline.host, "find_codex") as host:
                result = proofline.deliver(self.work, "", "", self.work / name, contract_request=request)
            self.assertEqual(result["status"], "INPUT NOT READY")
            self.assertEqual(result["model_dispatches"], 0)
            host.assert_not_called()
