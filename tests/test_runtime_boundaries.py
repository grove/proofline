"""Dependency boundaries remain thin and exclude retired S6 orchestrators."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SUPPORTED=("proofline.py","checks/candidate_snapshot.py","checks/coding_attempt.py",
           "checks/local_run.py","checks/native_checks.py")


class RunnerImportBoundaries(unittest.TestCase):
    def test_supported_code_has_no_retired_study_or_cli_circular_import(self):
        for path in SUPPORTED:
            with self.subTest(path=path):
                tree=ast.parse((ROOT/path).read_text())
                modules=[]
                for node in ast.walk(tree):
                    if isinstance(node,ast.Import):
                        modules.extend(alias.name for alias in node.names)
                    elif isinstance(node,ast.ImportFrom):
                        modules.append(node.module or "")
                        modules.extend((node.module or "")+"."+alias.name for alias in node.names)
                self.assertFalse(any("s6_baseline" in item or "s6_compare" in item
                                    or "s0_live" in item or "source_challenges" in item
                                    or "publication" in item for item in modules))
                if path!="proofline.py":
                    self.assertNotIn("proofline",modules)

    def test_public_cli_keeps_historical_snapshot_api_for_existing_evidence(self):
        import proofline
        from checks import candidate_snapshot
        self.assertIs(proofline.capture_base,candidate_snapshot.capture_base)
        self.assertIs(proofline.freeze,candidate_snapshot.freeze)
        self.assertIs(proofline.InputGap,candidate_snapshot.InputGap)


if __name__=="__main__":
    unittest.main()
