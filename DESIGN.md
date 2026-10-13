# Proofline vNext — minimal agent-first design

**Status:** Direction agreed in [issue #8](https://github.com/grove/proofline/issues/8);
cleanup proposed before new functionality. Today's working commands remain
`run` and `status`; check-only is **not yet implemented**.

## Purpose

**Help capable coding agents deliver better work by exposing meaningful
mistakes, without managing their thinking.** Preserve the entire original
promise, provide useful executable checks and fast feedback, and get out of
the way when evidence is sufficient for the caller's decision.

- **User/product owner:** supplies or approves the actual promise, any
  contractual amendment and specific remote effect permissions.
- **Coding agent:** owns exploration, plans, implementation, testing, and
  corrections. No required internal ceremony, reviewer or supervisor.
- **Proofline:** owns check execution against the exact frozen candidate,
  source and command identity, bounded native receipts, and honest check
  outcomes. This is *not* universal proof of source correctness.
- **Optional upstream planning:** Existing authorized P2P/Intentline contracts
  can inform later work without replanning, approving or narrowing the
  original request. Direct requests require neither integration.

## Workflows

| Path | Actual state | Boundaries |
| --- | --- | --- |
| Ordinary agent → check existing candidate → handoff | **Planned (#11)**; zero Proofline model dispatches; accepts unchanged/dirty work safely when implemented. | Existing agent owns all coding and fixes. Proofline checks frozen candidate. |
| Optional managed coding → explicit checks → handoff | **Supported** `proofline.py run`; one Codex coding dispatch and selected check commands. | Clean Git input, qualified macOS host, no correction/reviewer/prover/PR/merge. |

**Current example:** User requests a CLI version option. Caller provides the
complete request and relevant CLI/compatibility commands. The managed runner
codes once, executes those named commands, and reports "Selected commands
passed on candidate X, no full-source certification and no remote publication."
A failed or unavailable check is reported, not turned into acceptance.

**Future example (not runnable):** An existing agent implements Unicode-aware
username validation, invokes check-only without launching a second model,
receives "selected validation checks passed; Unicode compatibility not
demonstrated," and chooses whether to add coverage or fix a defect.

## Evidence is deliberately narrower than the promise

- **Checks passed:** only the named commands returned successful receipts
  for the exact candidate. Never "all requirements proven."
- **Checks failed:** at least one observed failing command; don't invent a
  diagnosis beyond the observations.
- **Checks unavailable:** a command could not produce trusted evidence
  (timeout, missing tool, sandbox or environment failure).
- **Stale checks:** candidate/source/command identity changed; previous
  evidence cannot be reused.
- **Requirements with or without demonstrated evidence:** planned optional
  mapping in [#13](https://github.com/grove/proofline/issues/13); not a
  current `run` verdict and not an exhaustive promise inventory.

Local coding/check permission does **not** authorize push, PR creation, merge,
deployment or other external mutation. A separate exact user grant would be
required for any future publishing tool. The supported product provides none.

## Explicitly excluded

Do **not** bring back mandatory AI reviewer/prover stages, automatic contract
planning/slicing, universal certification, multi-agent correction supervisors,
new mandatory configuration or approval ceremonies, or automatic publication.
Existing legacy `deliver`/`resume` mechanisms and their experiments are
retired from the supported product; see [archive](docs/RESEARCH-ARCHIVE.md).

**Feature admission:** Before adding any new mandatory step beyond essential
integrity/security/authorization controls, show a worthwhile gain in
**independently correct deliveries** versus a matched ordinary-agent baseline.
Account for extra latency, model/tool usage, false acceptance, needless
blocking and unavailable runs. If value is unproven, leave it optional or
remove it. Do not weaken mechanical safeguards to save a few seconds.

## vNext direction

[#9](https://github.com/grove/proofline/issues/9) freeze a small baseline;
[#10](https://github.com/grove/proofline/issues/10) keep a lean supported core;
[#11](https://github.com/grove/proofline/issues/11) add model-free check-only;
[#12](https://github.com/grove/proofline/issues/12) simplify invocation;
[#13](https://github.com/grove/proofline/issues/13) optional evidence mapping;
[#14](https://github.com/grove/proofline/issues/14) actionable feedback;
[#15](https://github.com/grove/proofline/issues/15) optional one correction;
[#16](https://github.com/grove/proofline/issues/16) compare and keep only earned
features. Scope remains small and gated by measurements.

Original S0–S6 designs, protocols and results survive unchanged at the pinned
commit linked from [RESEARCH-ARCHIVE.md](docs/RESEARCH-ARCHIVE.md). The
[S6 decision](docs/S6-DECISION.md) and [bounded comparison](docs/BOUNDED-COMPARISON.md)
remain accessible on the current branch.
