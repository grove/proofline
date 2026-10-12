# S5 — Authorized publication

S5 adds optional `pr-created` and `pr-merged` delivery targets after independently
accepted local work. The implementation and deterministic controls are present.
**The real authorized remote gate is pending.** No real GitHub test, end-to-end
qualification, publication of this change, or merge of this change is claimed.

## Authority and candidate binding

The initiating caller must have an actual explicit user grant for the repository,
base, publication branch, target and actions. `--authorize push`,
`--authorize create-pr`, and (only for a merge target) `--authorize merge` record
that grant with an actual `--effect-reference`. The grant is frozen before model
work, outside worker inputs, with a digest in the run record. `resume` cannot
adopt a new grant. Contract adoption and independent checking grant no effects.
Local requests do not instantiate the remote boundary or require GitHub.

Workers retain their network/credential isolation. Host-native Git and `gh` run
only after the public local-acceptance boundary validates current receipts and
candidate inputs. The runner has no comment, deployment, force-push, branch
cleanup or administrative bypass operation. No unrelated tracker writes occur.

The synthetic local base/candidate commits remain untouched. In separate host
scratch the runner imports the accepted Git objects, checks that the original
source tree equals the frozen comparison base, and creates one commit with the
accepted tree and original source commit as its sole parent. Full tree equality
covers regular bytes, paths, executable modes and symlink targets. The remote
base must still equal the original source commit. Another publication branch
candidate is never intentionally overwritten.

Publication requires current Git refs, scoped PR metadata and fetched head-tree
readback. Merge requires current matching head/base, required CI results and
GitHub's clean mergeable state; `gh pr merge` uses `--match-head-commit` and never
`--admin`. Server protections still apply. Merge, squash and rebase results are
accepted only when the remote merge tree and current base tree exactly equal the
independently accepted tree and the merge is an ancestor of that base. A changed
base, head, CI-produced commit, conflict resolution or different merged tree
returns a specific partial outcome requiring fresh acceptance.

GitHub cannot atomically bind its merge operation to both the inspected base SHA
and head SHA through this CLI. A concurrent base update may cause the server to
merge another tree; post-merge readback rejects that result rather than inheriting
local verdicts. The recorded external effect may already have happened. The
conservative path also reports later unrelated base changes as unverified; it
does not try to re-prove changed code or automatically rebase.

## Recovery, budget and status

Each effect has a persisted intent and native process identity/receipt before
completion is claimed. Resume first reads current remote refs and PR state and
reconciles the recorded worker. Observed pushes, PR creation and merges are not
repeated. A running worker, uncertain launch, or absent result after a lost or
successful response blocks retry. Confirmed failed processes can retry within
the original grant. A queued merge remains uncertain until readback confirms it;
the controller does not submit it twice.

Implementation, checking, CI waiting and remote commands share the original
elapsed budget. Every remote subprocess gets the remaining time (capped at 30
seconds) and its descendants are terminated on timeout. Local acceptance time is
preserved separately, so exhausted remote work does not erase previously valid
local proof. Read-only status inspection can reconcile current remote facts after
the execution budget has expired. Dispatch/usage accounting remains model-only;
native remote commands have their own elapsed receipts, and unavailable model
usage stays unknown.

The report keeps `status: LOCAL ACCEPTED` separately from `delivery.status` and
current `published`/`merged` facts. CLI exit 0 requires the requested target to be
confirmed; exit 2 includes a locally accepted but incomplete remote target.
`status` reads remote state without mutations and fails closed on inaccessible
or changed state. `resume` can finish publication without redispatching models or
repeating authorization when the original scope and acceptance still apply.

## Deterministic gate

[Publication tests](../tests/test_publication.py) use real disposable bare Git
repositories and explicitly fake GitHub responses. They exercise:

- Exact tree publication with original ancestry, and merge/squash/rebase readback.
- Create-only, local-only, rejected-candidate and invalid-authorization paths.
- Lost push/create/merge responses followed by resume without duplicate effects.
- An absent uncertain effect, authority tampering and exhausted remote budget.
- CI waiting and required-check/protection failures, base movement and branch collisions.
- Changed remote heads, stale local candidates and non-equivalent merged trees.
- Running/timeout worker reconciliation, unavailable readback and partial-target CLI exits.

Recorded local validation on 12 October 2026:

- Python 3.14: full 114-test suite passed, with six platform/opt-in skips.
- Native Codex transport/permission module: 17 tests passed on the host, including
  the three native checks that failed to initialize inside the nested sandbox.
- Fixed behavioral oracle: three controls passed.
- Python 3.12: the first 16 publication controls passed; the final two wrapper/CLI
  controls were additionally included in the full Python 3.14 run.
- The local Python 3.11 installation lacks its standard library, so that version
  was not exercised here; the repository CI matrix still includes it.

These are transport/safety controls, **not live GitHub or model judgments**.
The existing S0–S4 judgment evidence remains unchanged.

## Real gate (requires explicit authorization)

Use a clean local checkout of a safe disposable GitHub repository, with its base
still at that checkout's commit, existing host SSH/GitHub authentication, and an
unused authorized publication branch. The repository's existing workflows and
permissions must be appropriate for the authorized test. No repository creation
or deletion is performed by this runner.

```sh
python3 -B checks/s5_live.py \
  --repo /path/to/disposable-checkout --github-repo OWNER/REPO \
  --base main --branch proofline/s5-test \
  --authorize push --authorize create-pr --authorize merge \
  --effect-reference 'Actual initiating user grant reference' \
  --output .proofline/s5-live/new-qualification
```

The fixture adds only `proofline-s5-qualification.txt`, obtains real fresh local
judgments, publishes, and exits the controller immediately after PR creation.
Another process resumes the exact record, reconciles the uncertain creation,
merges, and reads back the remote result. A private operator check requires only
the expected addition and bytes, preserved original repository, confirmed remote
merge and exactly one push/create/merge dispatch. Raw evidence stays local and
ignored. Only an `OBSERVED` result supports claiming the full S5 gate passed.
