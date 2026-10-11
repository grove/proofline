"""Control construction checks; these synthetic inputs never authorize model runs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checks"))
import s2_live


class S2ControlTests(unittest.TestCase):
    def test_environment_gap_cannot_qualify_detection_of_a_regression(self):
        gap = {"status": "OBSERVED", "report": {"verdict": "NOT VERIFIED",
            "findings": ["Diagnosis test could not run"], "criteria": [{"id": "R1", "status": "NOT VERIFIED"}]}}
        self.assertFalse(s2_live.challenge_matches("diagnosis-regression", "standalone", [gap, gap]))
        defect = {"status": "OBSERVED", "report": {"verdict": "FAIL",
            "findings": ["Wrong invalid_diagnosis_response marker"], "criteria": [{"id": "R1", "status": "VIOLATED"}]}}
        self.assertTrue(s2_live.challenge_matches("diagnosis-regression", "standalone", [defect, defect]))
        defect["report"]["criteria"][0]["id"] = "R2"
        self.assertFalse(s2_live.challenge_matches("diagnosis-regression", "standalone", [defect, defect]))

    def test_parent_interaction_defect_is_a_complete_parent_blocker(self):
        defect = {"status": "OBSERVED", "report": {"verdict": "FAIL",
            "findings": ["R16: active descendants allow competing parent implementation"],
            "criteria": [{"id": "R16", "status": "VIOLATED"}]}}
        self.assertTrue(s2_live.challenge_matches("incomplete-combined-parent", "standalone", [defect, defect]))

    def test_equivalent_recovery_wording_keeps_the_source_gap_requirement(self):
        gap = {"status": "OBSERVED", "report": {"verdict": "NOT VERIFIED",
            "findings": ["INPUT NOT READY: source-required supported recovery action is omitted"], "criteria": []}}
        self.assertTrue(s2_live.challenge_matches("omitted-source-promise", "standalone", [gap, gap]))
        gap["report"]["findings"] = ["Supported recovery action could not be tested"]
        self.assertFalse(s2_live.challenge_matches("omitted-source-promise", "standalone", [gap, gap]))

    def test_audit_cannot_upgrade_a_missing_or_running_native_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "record.json"
            path.write_text(json.dumps({"kind": "s2_live_qualification", "active_stage": "prover"}))
            with patch.object(s2_live.delivery, "inspect_record") as inspect:
                result = s2_live.audit(path, root / "audit")
            self.assertEqual(result["status"], "NOT VERIFIED")
            inspect.assert_not_called()

    def test_diagnosis_controls_keep_source_and_expose_the_exact_marker_regression(self):
        d = s2_live.delivery
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            controller = original / "product/skills/productivity/deliver-issue/scripts/p2p_delivery.py"
            controller.parent.mkdir(parents=True)
            controller.write_text("failure_kind = 'invalid_diagnosis_response'\n")
            (original / "source.md").write_text("Require the invalid diagnosis marker and a later explicit resume.")
            (original / "accepted-input.md").write_text("# Invalid diagnosis\n| R1 | Honest terminal failure |\n| R2 | Later explicit resume |\n")
            (original / "contract-context.json").write_text(json.dumps({"criterion_ids": ["R1", "R2"], "scope": "standalone"}))
            d.host.git(original / "product", "init", "--quiet", "--template=")
            d.freeze(original / "product")
            before = d.host.snapshot(original)
            self.assertEqual(s2_live.prepare_case(original, root / "omitted", "omitted-source-promise"), ["R1"])
            s2_live.prepare_case(original, root / "regression", "diagnosis-regression")
            changed = root / "regression/product/skills/productivity/deliver-issue/scripts/p2p_delivery.py"
            self.assertIn("failed_launch", changed.read_text())
            self.assertNotIn("invalid_diagnosis_response", changed.read_text())
            self.assertEqual((root / "omitted/source.md").read_bytes(), (original / "source.md").read_bytes())
            control = json.loads((root / "omitted/contract-context.json").read_text())
            self.assertEqual(control["approval"]["kind"], "read-only-judgment-control")
            self.assertNotIn("content", control["approval"])
            self.assertEqual(d.host.snapshot(original), before)

    def test_all_readiness_controls_reject_without_host_or_model_dispatch(self):
        from test_contract_input import CONTRACT
        d = s2_live.delivery
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("Original source")
            parent = root / "parent.md"
            parent.write_text(CONTRACT)
            section = "## Approved delivery plan\nBoth children require full parent verification.\n\n"
            (root / "plan.md").write_text(section)
            contract = root / "contract.md"
            contract.write_text(CONTRACT.replace("| R7 | Source |", "| R7 | Parent v2:R7 |").replace("| R9 | Source |", "| R9 | Parent v2:R9 |").replace("[Original request](source.md)", "[Parent](parent.md)").replace(
                "Parent: None", f"Parent: [Parent](parent.md)\nParent snapshot: SHA-256 {d.host.sha256(parent.read_bytes())}\nContribution: [Plan](plan.md), section SHA-256 {d.host.sha256(section.encode())}"))
            metadata, _, _ = d.contract_input.inspect_contract(contract)
            approval = root / "approval.md"
            approval.write_text("Synthetic offline parser control " + metadata["contract_sha256"])
            metadata, _, _ = d.contract_input.adopted_contract(contract, metadata["contract_sha256"],
                metadata["source_sha256"], "Synthetic offline control", approval, d.host.sha256(approval.read_bytes()))
            positive = {"status": "NOT VERIFIED", "model_dispatches": 0, "elapsed_seconds": 0,
                        "accepted_contract": metadata, "source_repository": {"path": str(root)}}
            with patch.object(d, "inspect_record", return_value=positive), patch.object(d.host, "find_codex") as host:
                result = s2_live.qualify(root / "synthetic.json", root / "controls")
            self.assertEqual(len(result["input_controls"]), 9)
            self.assertTrue(all(c["status"] == "INPUT NOT READY" and c["dispatches"] == 0 for c in result["input_controls"]))
            self.assertEqual(result["model_dispatches"], 0)
            self.assertEqual(result["status"], "NOT VERIFIED")
            host.assert_not_called()

    def test_omission_and_parent_controls_keep_original_promise_and_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original"
            (original / "product").mkdir(parents=True)
            (original / "product/entry").write_text("unchanged product")
            (original / "product/alias").symlink_to("entry")
            (original / "source.md").write_text("The original parent requires admission and adaptive resizing.")
            (original / "accepted-input.md").write_text("| R9 | Parent v1:R22; S1 contribution | Admission |\n| R10 | Parent v1:R23 | Origin |\n")
            parent = "## Acceptance matrix\n| P1 | Admission |\n| P2 | Adaptive resizing |\n\n## Children\nChild is incomplete.\n"
            (original / "contract-context.json").write_text(json.dumps({"criterion_ids": ["R9", "R10"],
                "scope": "child", "context_files": [{"content": parent}]}))
            before = s2_live.delivery.host.snapshot(original)
            for case, expected in (("omitted-source-promise", ["R10"]), ("incomplete-combined-parent", ["P1", "P2"])):
                inputs = root / case
                ids = s2_live.prepare_case(original, inputs, case)
                self.assertEqual(ids, expected)
                self.assertEqual((inputs / "source.md").read_bytes(), (original / "source.md").read_bytes())
                self.assertEqual(s2_live.delivery.host.snapshot(inputs / "product"), s2_live.delivery.host.snapshot(original / "product"))
                self.assertTrue((inputs / "product/alias").is_symlink())
                context = json.loads((inputs / "contract-context.json").read_text())
                self.assertEqual(context["control"]["kind"], "deliberate-unapproved-fault-injection")
            self.assertEqual(s2_live.delivery.host.snapshot(original), before)
