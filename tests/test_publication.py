"""S5 fault injection: real disposable Git remotes, fake GitHub responses."""
import copy
import json
import io
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_recovery as recovery
import proofline as p


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = recovery.RecoveryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.work = self.fixture.work
        self.bare = self.work / "remote.git"
        p.host.git(self.work, "init", "--bare", "--quiet", str(self.bare))
        self.source = p.host.git(self.fixture.repo, "rev-parse", "HEAD")
        p.host.git(self.fixture.repo, "push", str(self.bare), "HEAD:refs/heads/main")
        self.pr = None
        self.effects = []
        self.failure = None
        self.checks = []
        self.pending_once = False
        self.merge_state = "CLEAN"
        self.merged_tree = None
        self.grant = {"target": "pr-merged", "repository": "owner/product", "base": "main",
                      "branch": "proofline/s5", "actions": ["push", "create-pr", "merge"],
                      "reference": "Explicit user request in test", "merge_method": "merge"}
        test = self
        native = p.publication.Remote
        self.native_remote = native
        class FakeRemote(native):
            def __init__(self, *args):
                super().__init__(*args)
                self.url = str(test.bare)

            def command(self, argv, *, action=None, **kwargs):
                result = super().command(argv, action=action, **kwargs)
                if action:
                    test.effects.append(action)
                    if test.failure == action:
                        test.failure = None
                        active = self.record["delivery"]["active_effect"]
                        worker_path = Path(active["directory"]) / "worker.json"
                        worker = json.loads(worker_path.read_text())
                        worker["receipt"]["timed_out"] = True
                        worker_path.write_text(json.dumps(worker))
                        raise ValueError("Simulated lost response")
                return result

            def gh(self, *args, action=None):
                if args[0] == "list":
                    return json.dumps([test.pr] if test.pr else [])
                if args[0] == "checks":
                    if test.pending_once:
                        test.pending_once = False
                        test.pr["mergeStateStatus"] = "CLEAN"
                        return json.dumps([{"name": "required", "bucket": "pending"}])
                    return json.dumps(test.checks)
                if args[0] == "create":
                    test.pr = {"number": 1, "url": "https://github.com/owner/product/pull/1", "state": "OPEN",
                        "headRefName": test.grant["branch"], "headRefOid": self.record["delivery"]["publication_commit"],
                        "baseRefName": "main", "baseRefOid": test.source, "isCrossRepository": False,
                        "mergeCommit": None, "mergeable": "MERGEABLE", "mergeStateStatus": test.merge_state}
                elif args[0] == "merge":
                    test.assertIn("--match-head-commit", args)
                    test.assertNotIn("--admin", args)
                    head = self.record["delivery"]["publication_commit"]
                    tree = test.merged_tree or self.record["identities"]["candidate_tree"]
                    parents = ["-p", test.source] + (["-p", head] if "--merge" in args else [])
                    merge = p.host.git(self.repo, "commit-tree", tree, *parents, "-m", "Fake GitHub merge")
                    p.host.git(self.repo, "push", str(test.bare), merge + ":refs/heads/main")
                    test.pr.update(state="MERGED", mergeCommit={"oid": merge})
                else:
                    raise AssertionError(args)
                return self.command([sys.executable, "-c", "print('fake GitHub response')"], action=action)
        self.remote_patch = patch.object(p.publication, "Remote", FakeRemote)
        self.remote_patch.start()
        self.addCleanup(self.remote_patch.stop)

    def deliver(self, **kwargs):
        with self.fixture.patches(self.fixture.stage):
            return self.fixture.deliver(effect_grant=copy.deepcopy(self.grant), **kwargs)

    def inspect(self):
        return p.inspect_record(self.fixture.output / "report.json")

    def test_remote_targets_and_exact_tree_for_all_merge_methods(self):
        for method in ("merge", "squash", "rebase"):
            with self.subTest(method=method):
                self.grant["merge_method"] = method
                self.fixture.output = self.work / method
                self.pr = None
                self.effects.clear()
                p.host.git(self.bare, "update-ref", "refs/heads/main", self.source)
                p.host.git(self.bare, "update-ref", "-d", "refs/heads/" + self.grant["branch"])
                result = self.deliver()
                self.assertEqual(result["status"], "LOCAL ACCEPTED")
                self.assertEqual(result["delivery"]["status"], "PR MERGED")
                self.assertEqual(self.effects, ["push", "create-pr", "merge"])
                self.assertTrue(self.inspect()["merged"])
                publication_commit = result["delivery"]["publication_commit"]
                remote_repo = self.fixture.output / "publication" / "git"
                self.assertEqual(p.host.git(remote_repo, "rev-parse", publication_commit + "^"), self.source)
                self.assertEqual(p.host.git(remote_repo, "rev-parse", publication_commit + "^{tree}"), result["identities"]["candidate_tree"])
                p.resume(self.fixture.output / "report.json")
                self.assertEqual(self.effects, ["push", "create-pr", "merge"])

    def test_create_target_never_merges(self):
        self.grant.update(target="pr-created", actions=["push", "create-pr"])
        result = self.deliver()
        self.assertTrue(result["published"])
        self.assertFalse(result["merged"])
        self.assertEqual(result["delivery"]["status"], "PR CREATED")
        self.assertEqual(self.effects, ["push", "create-pr"])

    def test_invalid_grant_fails_before_model_or_remote_effect(self):
        for key, bad in (("reference", ""), ("actions", ["merge"]), ("repository", None),
                         ("branch", "../main"), ("base", "proofline/s5")):
            with self.subTest(key=key), patch.object(p.live, "run_stage") as stage:
                grant = {**self.grant, key: bad}
                result = p.deliver(self.fixture.repo, "source", "| D1 | Required |", self.work / ("bad-" + key), effect_grant=grant)
                self.assertEqual(result["status"], "INPUT NOT READY")
                stage.assert_not_called()
                self.assertEqual(self.effects, [])

    def test_local_and_rejected_candidates_never_publish(self):
        with self.fixture.patches(self.fixture.stage), patch.object(p.publication, "Remote") as remote:
            local = self.fixture.deliver()
            remote.assert_not_called()
        self.assertFalse(local["published"])
        self.fixture.output = self.work / "rejected"
        self.fixture.outcome = lambda role, v, s, f: ("NOT VERIFIED", 0, ["INPUT NOT READY: missing source promise"]) if role == "reviewer" else (v, s, f)
        result = self.deliver()
        self.assertEqual(result["status"], "INPUT NOT READY")
        self.assertEqual(self.effects, [])

    def test_lost_responses_reconcile_without_duplicate_effects(self):
        for action in ("push", "create-pr", "merge"):
            with self.subTest(action=action):
                self.fixture.output = self.work / ("lost-" + action)
                p.host.git(self.bare, "update-ref", "refs/heads/main", self.source)
                p.host.git(self.bare, "update-ref", "-d", "refs/heads/" + self.grant["branch"])
                self.pr = None
                self.effects.clear()
                self.failure = action
                result = self.deliver()
                self.assertIn("active_effect", result["delivery"])
                recovered = p.resume(self.fixture.output / "report.json")
                self.assertEqual(recovered["delivery"]["status"], "PR MERGED")
                self.assertEqual(self.effects, ["push", "create-pr", "merge"])
                self.assertNotIn("active_effect", recovered["delivery"])

    def test_uncertain_absent_effect_is_not_retried(self):
        self.failure = "create-pr"
        result = self.deliver()
        self.pr = None
        result = p.resume(self.fixture.output / "report.json")
        self.assertIn("uncertain", result["next_action"])
        self.assertEqual(self.effects, ["push", "create-pr"])

    def test_failed_pending_and_protected_checks_do_not_merge(self):
        for state, checks in (("BLOCKED", []), ("CLEAN", [{"name": "required", "bucket": "fail"}]),
                              ("DIRTY", [])):
            with self.subTest(state=state, checks=checks):
                self.fixture.output = self.work / ("checks-" + state + str(len(checks)))
                self.pr = None
                self.effects.clear()
                p.host.git(self.bare, "update-ref", "-d", "refs/heads/" + self.grant["branch"])
                self.merge_state, self.checks = state, checks
                result = self.deliver()
                self.assertEqual(result["delivery"]["status"], "PR CREATED")
                self.assertFalse(result["merged"])
                self.assertEqual(self.effects, ["push", "create-pr"])

    def test_pending_ci_is_waited_for_without_repeating_effects(self):
        self.merge_state = "BLOCKED"
        self.pending_once = True
        with patch.object(p.publication.time, "sleep"):
            result = self.deliver()
        self.assertTrue(result["merged"])
        self.assertEqual(self.effects, ["push", "create-pr", "merge"])

    def test_running_effect_blocks_resume_before_any_new_mutation(self):
        self.failure = "create-pr"
        result = self.deliver()
        with patch.object(p.live, "reconcile_worker", side_effect=ValueError("Recorded worker is still running")):
            resumed = p.resume(self.fixture.output / "report.json")
        self.assertIn("still running", resumed["next_action"])
        self.assertEqual(self.effects, ["push", "create-pr"])

    def test_status_network_failure_does_not_trust_saved_remote_success(self):
        self.deliver()
        with patch.object(p.publication.Remote, "refs", side_effect=ValueError("readback unavailable")):
            result = self.inspect()
        self.assertEqual(result["status"], "LOCAL ACCEPTED")
        self.assertEqual(result["delivery"]["status"], "NOT VERIFIED")
        self.assertFalse(result["merged"])
        self.assertFalse(result["published"])
        self.assertEqual(self.effects, ["push", "create-pr", "merge"])

    def test_effect_wrappers_reject_unscoped_writes_and_cli_reports_partial_target(self):
        self.merge_state = "BLOCKED"
        result = self.deliver()
        remote = self.native_remote(result, self.fixture.output, lambda: None, lambda: 30)
        with patch.object(remote, "command") as command:
            for call in (lambda: remote.git("push", "other"), lambda: remote.gh("create"),
                         lambda: remote.gh("merge", "1"), lambda: remote.gh("comment", "1"),
                         lambda: remote.git("push", "other", action="merge")):
                with self.assertRaisesRegex(ValueError, "outside"):
                    call()
            command.assert_not_called()
        with patch.object(sys, "argv", ["proofline.py", "status", str(self.fixture.output / "report.json")]), \
                patch.object(p, "inspect_record", return_value=result), patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(p.main(), 2)
            self.assertIn("LOCAL ACCEPTED. Remote target: pr-merged; PR CREATED", stdout.getvalue())
            result["delivery"]["status"], result["merged"] = "PR MERGED", True
            self.assertEqual(p.main(), 0)

    def test_empty_required_checks_only_accepts_the_explicit_no_checks_response(self):
        self.merge_state = "BLOCKED"
        result = self.deliver()
        remote = self.native_remote(result, self.fixture.output, lambda: None, lambda: 30)
        directory = self.work / "empty-checks"
        directory.mkdir()
        result["delivery"]["commands"].append({"directory": str(directory), "receipt": {"exit_code": 1}})
        for message, allowed in (("no required checks reported on the 'proofline/s5' branch", True),
                                 ("HTTP 403 Forbidden", False), ("no checks reported on the 'other' branch", False)):
            (directory / "stderr").write_text(message)
            with patch.object(remote, "command", return_value=""):
                if allowed:
                    self.assertEqual(remote.gh("checks", "1", "--required"), "[]")
                else:
                    with self.assertRaisesRegex(ValueError, "unavailable"):
                        remote.gh("checks", "1", "--required")

    def test_native_remote_timeout_retains_worker_for_reconciliation(self):
        self.grant.update(target="pr-created", actions=["push", "create-pr"])
        with self.fixture.patches(self.fixture.stage), patch.object(p, "complete_target"):
            record = self.fixture.deliver(effect_grant=copy.deepcopy(self.grant))
        remote = p.publication.Remote(record, self.fixture.output, lambda: None, lambda: 0.05)
        with self.assertRaisesRegex(ValueError, "timed out"):
            remote.command([sys.executable, "-c", "import time; time.sleep(10)"], action="create-pr")
        effect = record["delivery"]["active_effect"]
        worker = p.live.reconcile_worker(Path(effect["directory"]))
        self.assertTrue(worker["receipt"]["timed_out"])
        with self.assertRaisesRegex(ValueError, "uncertain"):
            remote.reconcile(False)

    def test_live_qualification_requires_authority_and_validates_resumed_remote(self):
        import s5_live
        with self.assertRaisesRegex(ValueError, "explicit push/create-pr/merge"):
            s5_live.qualify(self.fixture.repo, self.work / "ungranted", {**self.grant, "target": "pr-created", "actions": ["push", "create-pr"]})
        self.assertFalse((self.work / "ungranted").exists())
        original_stage = self.fixture.stage
        def stage(*args, **kwargs):
            result = original_stage(*args, **kwargs)
            if result["role"] == "implementer":
                product = Path(result["identities"]["candidate_path"])
                (product / "value.py").write_bytes((self.fixture.repo / "value.py").read_bytes())
                (product / s5_live.MARKER).write_text(s5_live.CONTENT)
            return result
        with self.fixture.patches(stage):
            result = self.fixture.deliver(effect_grant=copy.deepcopy(self.grant))
        qualified = self.work / "qualified"
        with patch.object(s5_live.subprocess, "run", return_value=SimpleNamespace(returncode=75)), \
                patch.object(p, "resume", return_value=result), \
                patch.object(p, "inspect_record", return_value=result), \
                patch.object(p.host, "git", return_value="A\t" + s5_live.MARKER):
            audit = s5_live.qualify(self.fixture.repo, qualified, copy.deepcopy(self.grant))
        self.assertEqual(audit["status"], "OBSERVED")
        self.assertTrue(all(audit["private_oracle"].values()))

    def test_base_movement_and_branch_collision_prevent_effects(self):
        for collision in (False, True):
            with self.subTest(collision=collision):
                self.fixture.output = self.work / ("collision-" + str(collision))
                if collision:
                    p.host.git(self.bare, "update-ref", "refs/heads/main", self.source)
                    p.host.git(self.bare, "update-ref", "refs/heads/" + self.grant["branch"], self.source)
                else:
                    tree = p.host.git(self.bare, "rev-parse", self.source + "^{tree}")
                    other = p.host.git(self.bare, "commit-tree", tree, "-p", self.source, "-m", "Remote changed")
                    p.host.git(self.bare, "update-ref", "refs/heads/main", other)
                result = self.deliver()
                self.assertEqual(result["delivery"]["status"], "NOT VERIFIED")
                self.assertEqual(self.effects, [])

    def test_changed_merged_tree_never_inherits_acceptance(self):
        self.merged_tree = p.host.git(self.fixture.repo, "rev-parse", "HEAD^{tree}")
        result = self.deliver()
        self.assertEqual(result["status"], "LOCAL ACCEPTED")
        self.assertFalse(result["merged"])
        self.assertIn("Merged tree differs", result["next_action"])
        self.assertFalse(self.inspect()["merged"])

    def test_status_rejects_changed_remote_head_and_stale_local_candidate(self):
        self.grant.update(target="pr-created", actions=["push", "create-pr"])
        result = self.deliver()
        self.pr["headRefOid"] = self.source
        self.assertFalse(self.inspect()["published"])
        self.pr["headRefOid"] = result["delivery"]["publication_commit"]
        (Path(result["candidate_path"]) / "value.py").write_text("stale")
        inspected = self.inspect()
        self.assertEqual(inspected["status"], "NOT VERIFIED")
        self.assertFalse(inspected["published"])
        self.assertEqual(self.effects, ["push", "create-pr"])

    def test_grant_edit_and_exhausted_budget_cannot_authorize_more_work(self):
        self.grant.update(target="pr-created", actions=["push", "create-pr"])
        result = self.deliver()
        grant_file = self.fixture.output / "effect-grant.json"
        grant_file.write_text("{}")
        with self.assertRaisesRegex(ValueError, "authority changed"):
            p.resume(self.fixture.output / "report.json")
        self.assertEqual(self.effects, ["push", "create-pr"])
        self.fixture.output = self.work / "exhausted"
        with self.fixture.patches(self.fixture.stage), patch.object(p, "complete_target"):
            result = self.fixture.deliver(effect_grant=copy.deepcopy(self.grant))
        p.publication.publish(result, self.fixture.output, lambda: None, lambda: 0)
        self.assertEqual(result["delivery"]["status"], "NOT VERIFIED")
        self.assertIn("budget exhausted", result["next_action"])
        self.assertEqual(self.effects, ["push", "create-pr"])


if __name__ == "__main__":
    unittest.main()
