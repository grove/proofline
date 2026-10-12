---
name: proofline
description: Implement a repository request with fresh independent review and behavioral proof on one frozen local candidate. Use when the user asks for Proofline delivery or invokes /proofline. Direct delivery, bounded recovery/resume and narrow approved-contract inputs are supported. Optional scoped GitHub PR/merge delivery is qualified within the recorded S5 host and disposable-repository boundary.
---

Use the installed repository's [proofline.py](proofline.py) entry point. Python
3.11+, macOS and the qualified Codex CLI 0.162.1 are required. The runner consumes
real model usage and keeps local evidence. It publishes or merges only under an
explicit initial repository/action grant; local delivery is the default.

For a direct request, preserve the user's original text and any delegated source
bytes/revisions in a source file outside product changes. In the initiating
context, make a small source-grounded Markdown brief with stable criterion IDs
in a table (`| D1 | Required observable outcome |`). Include all material
positive, negative, boundary and regression obligations, constraints, exclusions,
and unresolved material decisions. The brief indexes the source; it cannot
narrow or replace it. Do not invoke an extra planning agent or ask for routine
approval. Resolve an essential source/authority ambiguity with the user.

Inspect the task-relevant repository README/conventions and entry points. Supply
a short inline execution map with known commands, public interfaces, fixtures,
and environment gaps. Use exact interpreter paths where needed. A clean Git
source repository is required; preserve unrelated local work rather than
resetting or discarding it. This boundary supports regular tracked files and
relative aliases to regular files inside the product, preserving exact Git modes
and link targets. External, directory, missing, cyclic and Git-metadata aliases,
submodules, ignored local dependencies, and source-mutating test
harnesses need a separately qualified observation path.

Run one delivery episode:

```sh
python3 /absolute/path/to/proofline/proofline.py deliver \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --brief /absolute/path/to/brief.md \
  --map 'Task-specific commands and relevant entry points' \
  --seconds 900 --stage-seconds 240 --verification-reserve 120 --dispatches 12
```

The runner owns the isolated implementation, candidate freeze, fresh review,
and fresh proof. Do not replace a failed receipt with an invented report, reuse
another candidate's verdict, or start a second episode silently to reset its
budget. On a failed review it skips proof. The runner classifies failure before recovery: product defects return a concise
reproduction and affected obligations to the same implementer session; weak
evidence gets a focused independent recheck without product edits. Environment
failures remain environment/evidence gaps; source and authority gaps block
explicitly. A changed candidate receives fresh review and proof. A still-valid
review may be retained only for the exact unchanged candidate and inputs.
Two consecutive correction rounds without independent criterion improvement
stop early; a productive third round can use remaining authorized capacity.
All stages share cumulative time/dispatch limits and a verification reserve.

Use `proofline.py resume <report.json>` after interruption. Resume reconciles
workers, confirms binding inputs and current candidate, and rejects stale
judgments before redispatch. Never duplicate a running/uncertain worker. Downtime
and interrupted dispatches consume the original budget; resume does not reset
or extend limits. The episode lock prevents concurrent controllers. Historical
S1/S3 records are inspectable, not resumable. Preserve terminal gaps and exhausted
work with the recorded next action. See [S4 evidence](docs/S4-RECOVERY.md).

Before reporting success, run `proofline.py status <report.json>`. Report the
confirmed outcome, remaining failed/unknown criteria, exact candidate path and
commit, and one next action. Local acceptance alone establishes **no publication or merge**.
A stale candidate requires fresh judgments. An unsupported host or an unqualified
remote path is an explicit capability gap, never a completed remote target.

For an explicitly authorized initial PR/merge request, record the actual grant
with `--target pr-created|pr-merged --github-repo OWNER/REPO --base <branch>
--branch <publication-branch> --authorize push --authorize create-pr
--effect-reference '<actual user grant reference>'`. A merge target additionally
requires `--authorize merge`; `--merge-method merge|squash|rebase` selects its
strategy. Never infer a grant from implementation permission, contract adoption,
independent acceptance, a tracker label, or publication preview. No deployment,
comment, force-push, protection bypass, or unrelated write is authorized.
Do not ask again when the exact initial grant still covers the action.

The runner uses host Git/GitHub CLI after local acceptance, verifies the original
source ancestry and exact accepted tree, then reads back the current remote
head/base and merged tree. Local and remote facts are separate; report the
requested target and actual partial outcome. Moved bases, changed heads,
protection failures and unavailable readback cannot inherit local verdicts.
Use the same `resume` command to reconcile uncertain effects before continuing;
it cannot enlarge the original grant or reset the budget. `status` reads current
remote state without remote mutations. S5's real authorized PR/merge and separate-process
recovery gate passed. Its live case had no required CI or branch protections;
protection failures and transformed-merge equivalence have deterministic coverage.
Honor [S5 qualification and limits](docs/S5-PUBLICATION.md); the narrow fixture is
not a guarantee for every repository or remote policy.

For a contract, first use `proofline.py inspect-contract <contract.md>` and read
the exact contract and complete linked original source chain. The narrow adapter
supports the current P2P eight-column Markdown matrix, transitive local sources,
and exact parent/contribution snapshots with qualified criterion mapping. There
must be no unresolved gaps, open decisions, or unavailable prerequisites. Runtime
prerequisite imports remain unsupported. It does not require P2P installed.
Inspection and an `approved` label grant no authority. Do not rewrite, renumber,
replan or convert an unsupported contract into a direct brief to bypass its gate.

Only if the user has explicitly adopted these exact displayed contract/source
bytes, or an actual P2P approval reference's authority and binding have been
inspected, substitute `--contract <path> --adopt-contract-sha256 <hash>
--adopt-source-sha256 <hash> --approval-reference '<actual approval reference>'`
for `--source` and `--brief`. Never supply these flags based on a generic task
mandate, an agent-authored fixture, or an inferred approval. Saved P2P approval
formats are not automatically trusted; obtain exact adoption if their authority
cannot be established. For an inspected existing P2P reference also supply
`--approval-file <original reference> --approval-sha256 <inspected hash>`.
Preserve the actual reference in the record. Read
[the support boundary and live gate](docs/S2-CONTRACT-INPUT.md).
Child acceptance never establishes parent completion. Combined-parent acceptance
needs the complete original promise on one assembled candidate. A stale parent or
plan and a closed prerequisite ticket cannot establish readiness. The narrow S2
live gate passed; see its actual agreements, failures and limits in
[S2 evidence](docs/S2-LIVE-EVIDENCE.md). Runtime prerequisite imports remain unsupported.
