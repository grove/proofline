# Proofline vNext — lean implementation plan

The supported `check`/`run`/`status` workflow is the product baseline.
The [design](DESIGN.md) is agent-first; S0–S6's previous mandatory
review/proof/certification architecture was abandoned. Historical source
and reports are [pinned in Git](docs/RESEARCH-ARCHIVE.md), not imported
by the current CLI.

## Minimal active architecture

- `proofline.py`: small public `check`/`run`/`status` CLI. It keeps minimal
  compatibility exports for already recorded native study tools.
- `skills/proofline-check/SKILL.md`: sole canonical optional coding-agent
  instruction set; both Codex and Claude Code repo-local discovery locations
  link to it, with the old root `SKILL.md` retained as a migration pointer.
  The Python CLI and check-only zero-model behavior do not require skills.
- `checks/candidate_snapshot.py`: exact clean-source Git snapshot or current tracked/non-ignored
  working-file snapshot, path validation and frozen candidate identity, without agent/review policy.
- `checks/local_run.py`: bounded episode orchestration and exact status
  revalidation, retaining distinct check failure/unavailability/staleness.
- `checks/coding_attempt.py`: one autonomous Codex implementation dispatch per turn,
  optionally persisting/resuming the same implementer for one correction,
  without an independent reviewer/prover or a second acceptance verdict.
- `checks/native_checks.py`: trusted host command receipts and protected
  check execution.
- `checks/feedback.py`: deterministic, optional caller-grounded failure
  annotations and concise check-scoped reports, with separately hash-bound
  bounded process receipts. No model inference or semantic certification.
- `checks/promise_evidence.py`: optional exact-source S1/R-id mapping and
  deterministic link-to-receipt reporting, including self-reported gaps and
  explicit coverage UNKNOWN. No additional model, source rewriting or peer.
- `checks/intentline_advisory.py`: optional **data-only** reader for completed
  single-S1 initial Intentline JSON exports, with exact source, file, contract
  and revision digests, preserved advisory constraints/gaps, explicit argv links
  and frozen local readback. No producer import, lineage flattening or approval.
- `checks/host_probe.py` and `checks/codex_live.py`: existing qualified
  sandbox, process lifecycle and model transport protections. S0 diagnostic
  helpers remain available for offline regressions, but are not called as
  extra acceptance stages by the supported runner.
- `tests/test_check_only.py`, `tests/test_local_run.py`, `tests/test_supported_cli.py`,
  `tests/test_host_probe.py`, `tests/test_codex_live.py`, and retained
  native S0 fixture controls: the supported runner and its boundary
  regressions.

No old delivery/recovery/publisher runtime, source-contract certifier,
historical native Intentline `deliver` controller, S3–S6 corpus generator,
or benchmark coordinator is imported by the supported runner. The optional
JSON advisory adapter does not execute peers or grant authority.

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
   reduce setup and show concise, actionable native observations while keeping
   raw bounded host receipts and optional expected/observed annotations separate.
   Source-linked R IDs are advisory even when optional #13 command links exist.
5. [#13 — Promise/evidence](https://github.com/grove/proofline/issues/13):
   implemented as optional check-only source-linked rows, receipt-bound status,
   untested clauses and unverified gap proposals, never certification.
   [#23](https://github.com/grove/proofline/issues/23) adds a separate
   **opt-in** reader of completed initial Intentline JSON exports and their
   unverified promises/gaps; no mandatory installation or adoption.
6. [#15 — Correction](https://github.com/grove/proofline/issues/15), implemented:
   opt-in `run --correct-once` resumes the bound implementer after an intact
   Python assertion failure. Both candidates and their receipts remain bound;
   all selected checks rerun under one cumulative budget. No extra dispatch
   on success, no retry after interruption, no inference from advisory gaps.
7. [#16 — Compare](https://github.com/grove/proofline/issues/16), implemented:
   the [observed matched study](evaluation/results/matched-v5-20261013/README.md)
   retains all sixteen assigned native attempts, exact candidates, independent
   finite grading and twelve pre-dispatch controls. Each arm delivered 4/4.
   The report separates false acceptance, blocked handoffs, omissions, bad/unknown
   evidence, time/tokens, paired descriptive effects and unmeasured costs.
   Planning added overhead without an observed delivery benefit; keep additional
   stages optional. Four tasks cannot establish general superiority. Earlier
   stopped declarations retain their separate missing slots and source archives.

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
