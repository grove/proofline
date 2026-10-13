# Proofline vNext — lean implementation plan

The supported `check`/`run`/`status` workflow is the product baseline.
The [design](DESIGN.md) is agent-first; S0–S6's previous mandatory
review/proof/certification architecture was abandoned. Historical source
and reports are [pinned in Git](docs/RESEARCH-ARCHIVE.md), not imported
by the current CLI.

## Minimal active architecture

- `proofline.py`: small public `check`/`run`/`status` CLI. It keeps minimal
  compatibility exports for already recorded native study tools.
- `checks/candidate_snapshot.py`: exact clean-source Git snapshot or current tracked/non-ignored
  working-file snapshot, path validation and frozen candidate identity, without agent/review policy.
- `checks/local_run.py`: bounded episode orchestration and exact status
  revalidation, retaining distinct check failure/unavailability/staleness.
- `checks/coding_attempt.py`: one autonomous Codex implementation dispatch,
  without an independent reviewer/prover or a second acceptance verdict.
- `checks/native_checks.py`: trusted host command receipts and protected
  check execution.
- `checks/host_probe.py` and `checks/codex_live.py`: existing qualified
  sandbox, process lifecycle and model transport protections. S0 diagnostic
  helpers remain available for offline regressions, but are not called as
  extra acceptance stages by the supported runner.
- `tests/test_check_only.py`, `tests/test_local_run.py`, `tests/test_supported_cli.py`,
  `tests/test_host_probe.py`, `tests/test_codex_live.py`, and retained
  native S0 fixture controls: the supported runner and its boundary
  regressions.

No old delivery/recovery/publisher runtime, source-contract evaluator,
Intentline bundle consumer, S3–S6 corpus generator or benchmark controller
belongs on the supported runtime import path. Any future upstream
contract use must be a new narrow, approved adapter, not an automatic
reinstatement of retired certification.

## Small issue-ordered next steps

1. [#9 — Baseline](https://github.com/grove/proofline/issues/9):
   define a fixed, independently evaluated comparison, including genuine
   alternatives, defects, failure/no-handoff denominators and resource use.
   Keep the original S6 benchmark only as historical reference.
2. [#10 — Core extraction](https://github.com/grove/proofline/issues/10):
   finish simplifying native helper boundaries without breaking validated
   sandbox and receipt controls. This cleanup is significant groundwork.
3. [#11 — Check-only](https://github.com/grove/proofline/issues/11), implemented:
   existing coding agents obtain frozen checks with zero new model calls,
   safely handling dirty/untracked work without mutation. Original request,
   selected manifest, exact argv and host evidence are bound to each record.
4. [#12 — Invocation](https://github.com/grove/proofline/issues/12),
   [#14 — Feedback](https://github.com/grove/proofline/issues/14):
   reduce setup and show concise, actionable native observations.
5. [#13 — Promise/evidence](https://github.com/grove/proofline/issues/13):
   optional source-linked rows with explicit evidence gaps, not certification.
6. [#15 — Correction](https://github.com/grove/proofline/issues/15):
   an optional single same-agent repair after observed failures; one
   cumulative budget and no extra model dispatch on success.
7. [#16 — Compare](https://github.com/grove/proofline/issues/16):
   report independently correct deliveries against the ordinary-agent
   baseline, latency, cost, false acceptances and needless blocking. Retain
   only features that measurably earn their overhead.

## Stop rules

Never claim a command pass proves the complete original promise. Do not
silently import historical experiments as approved behavior. No new mandatory
reviewer, planner, approval ceremony or automatic GitHub publication. Any
new mandatory stage needs measured improvement in independent correctness
worth its cost. Native isolation, source/candidate identity, evidence integrity
and remote-effect authorization remain essential.

A previously published live baseline pins runtime hashes at commit
`9c3684d`. Deterministic CI verifies those historical bytes from Git
history, not from the intentionally evolving active runner; no historical
manifest or scores are rewritten. Native macOS/Codex qualification is
still distinct from Linux CI.

The S6 abandon/simplify decision and incomplete comparisons are preserved
in [S6-DECISION.md](docs/S6-DECISION.md). The later six-task study found no
added correctness benefit from routine review; see
[BOUNDED-COMPARISON.md](docs/BOUNDED-COMPARISON.md).
