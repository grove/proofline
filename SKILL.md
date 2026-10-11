---
name: proofline
description: Implement a repository request with fresh independent review and behavioral proof on one frozen local candidate. Use when the user asks for Proofline delivery or invokes /proofline. Direct delivery is qualified; the narrow contract adapter is experimental. Publication is not supported.
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
resetting or discarding it. This initial boundary supports regular tracked files;
symlinks, submodules, ignored local dependencies, and source-mutating test
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
the exact contract and linked original source. This experimental adapter supports
the current standalone P2P eight-column Markdown matrix with no unresolved gaps,
open questions, parent or prerequisites. It does not require P2P installed.
Inspection and an `approved` label grant no authority. Do not rewrite, renumber,
replan or convert an unsupported contract into a direct brief to bypass its gate.

Only if the user has explicitly adopted these exact displayed contract/source
bytes, substitute `--contract <path> --adopt-contract-sha256 <hash>
--adopt-source-sha256 <hash> --approval-reference '<actual approval reference>'`
for `--source` and `--brief`. Never supply these flags based on a generic task
mandate, an agent-authored fixture, or an inferred approval. Saved P2P approval
formats are not automatically trusted; obtain exact adoption if their authority
cannot be established. Preserve the actual reference in the record. The adapter's
full S2 live gate remains pending an actual approved contract; do not claim that
parser tests establish S2 or parent completion.
