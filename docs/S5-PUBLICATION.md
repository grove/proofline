# S5 — Authorized publication

S5 adds optional `pr-created` and `pr-merged` delivery targets after independently
accepted local work. The implementation and deterministic controls are present.
**The real authorized remote gate passed on 12 October 2026** in
[grove/proofline-disposable-1](https://github.com/grove/proofline-disposable-1).
[Qualification PR #1](https://github.com/grove/proofline-disposable-1/pull/1) was
created and merged after real independent local acceptance and separate-process
recovery. The live case used a normal merge, an unprotected base and no required
CI. Other safety cases retain the deterministic coverage stated below. This is
one narrow end-to-end observation, not a general correctness or performance
claim. Publication or merge of Proofline's own implementation is not claimed.

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

## Recorded real gate

The user supplied the repository and explicitly approved completing the S5
push/PR/merge test: “Use it to finish S5's real remote gate. I approve.” The
repository was empty. Host setup initialized `main` with a single README and
pushed comparison commit `db263580765dd1d347842a14f005a5c557254c1b` before starting
the bounded episode. That separate bootstrap push took 2.176 seconds; its receipt
is retained. Repository policy readback showed `protected: false`, no rulesets,
and all three merge strategies allowed. No settings, workflows or protections
were changed.

The exact executed command was:

```sh
/opt/homebrew/bin/python3.14 -B checks/s5_live.py \
  --repo /Users/grove/projects/proofline/.proofline/s5-live/disposable-1-20261012/source \
  --github-repo grove/proofline-disposable-1 --base main \
  --branch proofline/s5-gate-20261012 \
  --authorize push --authorize create-pr --authorize merge \
  --effect-reference 'User approval on 2026-10-12: Use https://github.com/grove/proofline-disposable-1 to finish S5 real remote gate; push, PR creation and merge approved.' \
  --output /Users/grove/projects/proofline/.proofline/s5-live/disposable-1-20261012/qualification
```

The host was Darwin 25.6.0, Python 3.14.8, Codex CLI 0.162.1,
Git 2.54.0 (Apple Git-157) and GitHub CLI 2.102.0. Model preferences were the
existing `gpt-6.1-sol` / `high`; worker isolation was unchanged. No model or host
boundary change was needed. The episode began at 07:20:08 UTC and the real merge
completed at 07:26:03 UTC, within the unchanged 900-second/12-dispatch budget.

| Stage | Native outcome | Elapsed | Input tokens | Cached input tokens | Output tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| Implementer | READY | 128.082 s | 115,511 | 97,792 | 2,377 |
| Fresh reviewer | PASS | 76.306 s | 55,441 | 39,808 | 1,291 |
| Fresh prover | PROVEN | 128.761 s | 74,828 | 57,216 | 2,926 |

All three native thread identities were distinct. Both verifier boundary
canaries were OBSERVED. The prover independently observed exact 35-byte file
contents including the final newline and preserved original Git blobs/modes,
with only the requested addition and a matching captured diff. Both material
criteria, D1 and D2, were SATISFIED. No corrections or evidence rechecks were
needed.

Local acceptance took 334.446 seconds; delivery through the confirmed remote
target took **359.537 seconds and three model stage dispatches**. Reported usage
was 245,780 input tokens (194,816 cached), 6,594 output tokens and 851 reasoning
output tokens. Cached input and reasoning output are reported subcategories,
not extra tokens to add to their totals. Monetary cost is unknown. Bootstrap,
policy inspection and subsequent operator status inspection are outside the
bounded episode; they are not presented as zero-cost work.

The controller exited with the qualification's required code 75 immediately
after real PR creation returned, before remote readback. A separate process
resumed the same record and cumulative budget, reconciled the existing PR,
merged it and read back the resulting Git objects. The episode has exactly one
push, one create-PR and one merge intent/receipt, each exit 0, and no pending
effect. Those counts exclude the explicitly documented bootstrap push. No model
worker was redispatched during remote recovery.

Before merge, remote metadata was `MERGEABLE` / `CLEAN` with the exact original
base and intended head. `gh pr checks --required` returned its explicit
no-checks response (exit 1); the runner's narrow empty-check handling was exercised
on the actual CLI, and GitHub permitted the normal merge without a bypass.

| Binding | Exact identity |
| --- | --- |
| Original remote comparison base | `db263580765dd1d347842a14f005a5c557254c1b` |
| Frozen local comparison base | `4e87e8193d25ebefc047bd9eb7e8315c874c7311` |
| Accepted local candidate | `09efb1eb8fd1dbcfb9a99b1a45c686e249ab7221` |
| Accepted/published/merged tree | `07b34343178c43f12b7b9680ad94093b76d5e723` |
| Published PR head | `a63283101d6da4126444c664b18b31a5c8e826fd` |
| Merge commit and current remote main | `bb7c6e43b14b0a2696499eccaa4d3707b1bcb184` |

The published head has the original comparison commit as its sole parent. The
merged tree and current `main` tree equal the accepted tree; the merge commit is
an ancestor of current `main`. The private operator oracle confirmed only
`A\tproofline-s5-qualification.txt`, exact promised bytes, and an unchanged
original local repository snapshot. The qualification report is **OBSERVED**.
Independent `gh pr view` and `git ls-remote` agreed on the merged PR/head/main.
The final public `proofline.py status` exited 0 with
`LOCAL ACCEPTED. Remote target: pr-merged; PR MERGED.`

Raw local evidence is ignored under
`.proofline/s5-live/disposable-1-20261012/`: `authorization.json`,
`bootstrap-receipt.json`, policy snapshots, `evidence-summary.json`,
`qualification/report.json`, `qualification/run/report.json`, native role
transcripts/receipts, remote command receipts and `final-status.txt`. No raw
transcripts, credentials, private oracle or temporary product files enter the
tracked product change.

**S5's dependency gate is satisfied within this recorded host and repository
boundary.** Actual push/PR/merge, separate-process recovery and current remote
readback are demonstrated. Live required-CI/protected-branch behavior, live
squash/rebase and concurrent base races were not tested; their mechanical
controls and the post-merge race limit above remain explicit. S6 is the next
slice, not evidence already obtained by this run.

## Repeat the real gate (requires explicit authorization)

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
