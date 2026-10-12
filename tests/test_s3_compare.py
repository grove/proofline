import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "checks"))
import s3_compare as s3


class ComparisonTests(unittest.TestCase):
    def test_single_sandbox_transport_preserves_non_permission_arguments(self):
        t = s3.s3_p2p_transport
        args = ["exec", "--ignore-user-config", "--sandbox", "workspace-write", "-C", "/scratch",
                "-c", 'model="configured"', "-c", "sandbox_workspace_write.network_access=false",
                "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
                "-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true",
                "--output-schema", "/schema", "-"]
        argv = t.command("/codex", args, ["/private"])
        self.assertNotIn("--sandbox", argv)
        self.assertIn('model="configured"', argv)
        self.assertEqual(argv[-1], "-")
        config = tomllib.loads("profile=" + argv[-2].split("=", 1)[1])["profile"]
        self.assertEqual(config["filesystem"]["/private"], "deny")
        self.assertEqual(config["filesystem"]["/scratch"], "write")
        self.assertEqual(config["filesystem"]["/scratch/.git"], "read")
        self.assertFalse(config["network"]["enabled"])
        executions = (Path.home() / ".p2p/executions").resolve()
        self.assertEqual(config["filesystem"][str(executions)], "deny")
        self.assertEqual(config["filesystem"][str(s3.p.host.ROOT)], "deny")
        self.assertEqual(config["filesystem"][str(Path(os.environ.get("CODEX_HOME", Path.home()/".codex")).resolve())], "deny")
        self.assertEqual(config["filesystem"][str(Path.home()/".codex/RTK.md")], "read")
        scoped = t.profile(executions / "own/username/runtime/scratch/context", [])
        self.assertEqual(scoped["filesystem"][str(executions)], "deny")
        self.assertEqual(scoped["filesystem"][str(executions / "own")], "read")
        with self.assertRaisesRegex(ValueError, "Unexpected permission"):
            t.command("/codex", [x.replace("network_access=false", "network_access=true") for x in args], [])
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            t.command("/codex", [x for x in args if x != "sandbox_workspace_write.exclude_slash_tmp=true"], [])

    def test_transport_git_paths_preserve_environment_and_bind_actual_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory).resolve() / "runtime"
            workspace = runtime / "workspace"
            workspace.mkdir(parents=True)
            (workspace / ".git").write_text("gitdir: " + str(runtime / "repository.git"))
            (runtime / "repository.git").mkdir()
            readonly = runtime / "scratch/review"
            readonly.mkdir(parents=True)
            for scratch in (workspace, readonly):
                args = ["exec", "--sandbox", "workspace-write", "-C", str(scratch),
                        "-c", 'shell_environment_policy.set={PATH="original",HOME="unchanged"}',
                        "-c", "sandbox_workspace_write.network_access=false",
                        "-c", "sandbox_workspace_write.exclude_slash_tmp=true",
                        "-c", "sandbox_workspace_write.exclude_tmpdir_env_var=true", "-"]
                argv = s3.s3_p2p_transport.command("/codex", args, [])
                value = next(x for x in argv if x.startswith("shell_environment_policy.set="))
                env = tomllib.loads(value)["shell_environment_policy"]["set"]
                self.assertEqual(env["PATH"], "original")
                self.assertEqual(env["HOME"], "unchanged")
                self.assertFalse(Path(env["GIT_DIR"]).is_absolute())
                self.assertEqual((scratch / env["GIT_DIR"]).resolve(), runtime / "repository.git")
                self.assertEqual((scratch / env["GIT_WORK_TREE"]).resolve(), workspace)
                self.assertTrue(any(x.startswith("developer_instructions=") for x in argv))

    def test_transport_followup_refuses_changed_private_oracle_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.json"
            previous.write_text(json.dumps({"status": "OBSERVED", "p2p_commit": "fixed",
                "oracle_sha256": "changed", "assignments": [{"cohort": "p2p",
                    "delivery": {"model_dispatches": 0, "controller_receipt": {
                        "stdout": "generated artifacts cannot be binding inputs"}}} for _ in range(5)]}))
            with patch.object(s3.p, "git_bytes", return_value=b"fixed"), \
                 patch.object(s3.p.host, "run_command") as launch:
                with self.assertRaisesRegex(ValueError, "oracle changed"):
                    s3.p2p_followup(previous, root / "p2p", root / "output")
            launch.assert_not_called()
            self.assertFalse((root / "output").exists())

    def test_p2p_collects_actual_external_runtime_and_supported_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, local, runtime = (root / name for name in ("repo", "local", "external"))
            repo.mkdir(); local.mkdir()
            (root / ".proofline").mkdir()
            (runtime / "workspace").mkdir(parents=True)
            attempt = runtime / "attempts/a"
            attempt.mkdir(parents=True)
            (attempt / "launch.json").write_text("{}")
            (attempt / "exit.json").write_text('{"elapsed_seconds": 3, "exit_code": 0}')
            (local / "delivery.json").write_text('{"status":"REVIEWED_AND_PROVEN", "attempts":[{"id":"a","stage":"proof","status":"complete","usage":{"input_tokens":7}}]}')
            module = SimpleNamespace(local_directory=lambda *_: local,
                execution_runtime=lambda *_: runtime, autonomy=SimpleNamespace(local=lambda _: {
                    'policy': {'decisions': ['implementation', 'evidence', 'repair', 'planning'],
                               'constraints': [], 'effects': [], 'approval_source': 'fixture'}}))
            receipt = {"exit_code": 0, "timed_out": False}
            with patch.dict(sys.modules, {"p2p_delivery": module}), \
                 patch.object(s3.p.host, "ROOT", root), \
                 patch.object(s3.p.host, "git", return_value="base"), \
                 patch.object(s3.p.host, "run_command", return_value=receipt) as run_command:
                result = s3.p2p_run(repo, s3.contract(), "original", root / "run",
                    root / "skills/productivity/deliver-issue/scripts/p2p_delivery.py",
                    root / "operator", "/real/codex")
            self.assertTrue(result["accepted"])
            self.assertEqual(result["candidate"], str(runtime / "workspace"))
            self.assertEqual(result["model_dispatches"], 1)
            self.assertEqual(result["stages"][0]["path"], str(attempt))
            controller_argv = run_command.call_args_list[-1].args[0]
            self.assertEqual(controller_argv[controller_argv.index('--max-stage-seconds') + 1], '240')
            mandate = json.loads(Path(controller_argv[controller_argv.index('--mandate') + 1]).read_text())
            self.assertNotIn('planning', mandate['decisions'])
            self.assertEqual(mandate['effects'], [])
            self.assertTrue({'implementation', 'evidence', 'repair'} <= set(mandate['decisions']))
            self.assertEqual((repo / ".p2p/work/username/source-issue.md").read_text(), "original")
            self.assertIn("(source-issue.md)", (repo / ".p2p/work/username/contract.md").read_text())

    def test_all_assignments_and_source_coverage_are_fixed(self):
        self.assertEqual(len(s3.CASES) * len(s3.COHORTS), 20)
        self.assertEqual(s3.p.criterion_ids(s3.contract()), ["R1", "R2", "R3", "R4"])
        self.assertEqual(s3.p.criterion_ids(s3.contract(True)), ["R1", "R3", "R4"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "contract.md"
            path.write_text(s3.contract())
            (root / "source.md").write_bytes((s3.p.host.FIXTURES / "source.md").read_bytes())
            metadata, _, _ = s3.p.contract_input.inspect_contract(path)
            self.assertEqual(metadata["criterion_ids"], ["R1", "R2", "R3", "R4"])

    def test_incomplete_agreement_cannot_be_scored_as_a_delivery(self):
        self.assertEqual(s3.outcome(True, True, True), "FALSE ACCEPTED")
        self.assertEqual(s3.outcome(True, False, False), "FALSE ACCEPTED")
        self.assertEqual(s3.outcome(False, True, False, observed=True), "FALSE BLOCKED")
        self.assertEqual(s3.outcome(False, True, False, timed_out=True), "BUDGET EXHAUSTED")
        self.assertEqual(s3.outcome(False, True, True, observed=True), "FAILED")
        self.assertFalse(s3.source_gap_rejected({"accepted": False,
            "next_action": "Native invocation timed out", "stages": []}))
        self.assertTrue(s3.source_gap_rejected({"accepted": False,
            "stages": [{"report": {"findings": ["INPUT NOT READY: original source whitespace promise R2 omitted from contract"]}}]}))
        self.assertFalse(s3.judgment_observed([{"role": "preflight-1", "status": "complete"}]))
        self.assertFalse(s3.judgment_observed([{"role": "review", "status": "complete", "report_validation": "rejected"}]))
        self.assertFalse(s3.judgment_observed([{"role": "review", "status": "complete"}]))
        self.assertTrue(s3.judgment_observed([{"role": "review", "status": "complete", "report_validation": "accepted"}]))
        self.assertTrue(s3.judgment_observed([{"role": "reviewer", "status": "OBSERVED"}]))
        diagnosis = {'role': 'diagnosis', 'status': 'complete', 'report_validation': 'accepted',
                     'report': {'status': 'BLOCKED', 'action': 'plan-acceptance'}}
        self.assertTrue(s3.judgment_observed([diagnosis]))
        self.assertTrue(s3.judgment_observed([diagnosis | {
            'report': {'status': 'ACTIONABLE', 'action': 'plan-acceptance'}}]))
        self.assertFalse(s3.judgment_observed([diagnosis | {'status': 'failed'}]))
        self.assertFalse(s3.judgment_observed([diagnosis | {'report_validation': 'rejected'}]))
        self.assertFalse(s3.judgment_observed([diagnosis | {'report': None}]))
        self.assertFalse(s3.judgment_observed([diagnosis | {
            'report': {'status': 'BLOCKED', 'action': 'none'}}]))

    def test_scope_change_is_a_real_public_behavior_counterexample(self):
        spec = importlib.util.spec_from_file_location("s3_test_oracle", s3.p.host.FIXTURES / "oracle.py")
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "product"
            s3.seed(root, "correct", trim=True)
            report = oracle.inspect_candidate(root)
            self.assertFalse(report["matches_expected"])
            bad = [row for row in report["observations"] if row["status"] == "MISMATCH"]
            self.assertTrue(any(row["criterion"] == "U2" for row in bad))

    def test_failed_and_unknown_costs_are_not_zero_or_discarded(self):
        records = [{"elapsed_seconds": 12, "assignments": [
            {"cohort": "proofline", "outcome": "ACCEPTED CORRECTLY", "delivery": {
                "elapsed_seconds": 10, "model_dispatches": 2, "stages": [
                    {"role": "prover", "receipt": {"elapsed_seconds": 4},
                     "usage": {"input_tokens": 7, "output_tokens": 2}}]}}]},
            {"elapsed_seconds": None, "quality_eligible": False, "assignments": [
                {"cohort": "proofline", "outcome": "FAILED", "delivery": {
                    "model_dispatches": 1, "elapsed_seconds": None, "stages": []}},
                {"cohort": "p2p", "outcome": "FAILED", "delivery": {
                    "model_dispatches": 0, "elapsed_seconds": 2}}]}]
        result = s3.summarize(records)
        self.assertIsNone(result["campaign_seconds"])
        self.assertEqual(result["known_campaign_seconds"], 12)
        row = result["cohorts"]["proofline"]
        self.assertEqual((row["dispatches"], row["usage_unknown_stages"]), (3, 2))
        self.assertEqual(row["qualified_satisfactory_deliveries"], 1)
        self.assertEqual(row["known_seconds_per_qualified_satisfactory_delivery"], 10)
        self.assertIsNone(row["seconds_per_qualified_satisfactory_delivery"])
        self.assertIsNone(result["cohorts"]["p2p"]["seconds_per_qualified_satisfactory_delivery"])
        successful_setup = {"elapsed_seconds": 5, "quality_eligible": False, "assignments": [
            {"cohort": "proofline", "outcome": "ACCEPTED CORRECTLY", "delivery": {
                "elapsed_seconds": 5, "model_dispatches": 0}}]}
        row = s3.summarize([records[0], successful_setup])["cohorts"]["proofline"]
        self.assertEqual(row["qualified_satisfactory_deliveries"], 1)
        self.assertEqual(row["independently_satisfactory_deliveries"], 2)
        self.assertEqual(row["seconds_per_satisfactory_delivery"], 7.5)
        successful_setup["quality_eligible"] = True
        successful_setup["assignments"][0]["quality_eligible"] = False
        self.assertEqual(s3.summarize([successful_setup])["cohorts"]["proofline"]["qualified_satisfactory_deliveries"], 0)
        row = s3.summarize([{"assignments": [{"cohort": "p2p", "outcome": "FAILED"}]}])["cohorts"]["p2p"]
        self.assertIsNone(row["total_dispatches"])
        self.assertEqual(row["unknown_dispatch_counts"], 1)
