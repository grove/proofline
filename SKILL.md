---
name: proofline
description: Implement a repository request with fresh independent review and behavioral proof on one frozen local candidate. Use when the user asks for Proofline delivery or invokes /proofline. Direct delivery and narrow approved-contract inputs are qualified. Publication is not supported.
---

Use the installed repository's [proofline.py](proofline.py) entry point. Python
3.11+, macOS and the qualified Codex CLI 0.162.1 are required. The runner consumes
real model usage and keeps local evidence; it does not publish or merge.

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
  --seconds 900 --stage-seconds 240 --verification-reserve 120
```

The runner owns the isolated implementation, candidate freeze, fresh review,
and fresh proof. Do not replace a failed receipt with an invented report, reuse
another candidate's verdict, or start a second episode silently to reset its
budget. On a failed review it skips proof. Product correction and evidence-only
recovery are later slices; report the current actionable gap and preserved
candidate rather than claiming acceptance.

Before reporting success, run `proofline.py status <report.json>`. Report the
confirmed outcome, remaining failed/unknown criteria, exact candidate path and
commit, and one next action. Local acceptance is **not published or merged**.
A stale candidate requires fresh judgments. Requested publication, merge,
or an unsupported host is an explicit capability/input gap,
not authority to approximate that target or silently convert it to local success.

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
