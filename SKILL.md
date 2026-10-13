---
name: proofline
description: Run one bounded coding attempt on an isolated local candidate, followed by explicit executable checks. Reports check outcomes without certifying the complete source promise.
---

## Product direction: agent-first, not new runtime behavior

This skill **currently supports only** the managed `run` workflow below:
one Codex coding attempt and selected native checks on its frozen candidate.
The [vNext contract](DESIGN.md#proofline-vnext--agent-first-product-contract-proposed-13-october-2026)
also proposes a [check-only mode (#11)](https://github.com/grove/proofline/issues/11)
for existing coding agents, with **zero additional model dispatches**.
**Do not invoke `proofline check` yet; it is not implemented.**

The coding agent owns strategy, implementation, self-testing and corrections.
Proofline owns bounded execution, exact source/candidate/check identity,
native receipts and concise observed outcomes. Preserve the *full* source,
including source-grounded authorized contracts where supplied; direct tasks
need neither P2P nor Intentline. Report checks passed/failed/unavailable and
stale candidate evidence truthfully; requirement coverage mapping is future
work, and passing commands cannot certify all promises. No local check
authorizes push, PR, merge or deployment. No mandatory reviewer, prover,
planner, slicer, extra approval ceremony, config or publication stage is
introduced by this documentation change. Extra mandatory steps require
independently measured correctness gains worth their overhead.

Use [proofline.py](proofline.py) `run`. The supported native host is macOS,
Python 3.11+ and Codex CLI 0.162.1 with existing authentication. Select an exact
supported interpreter. See the [S6 decision](docs/S6-DECISION.md).

Preserve the user's complete original request in a source file outside product
changes. Select task-relevant executable checks and store their exact argument
lists in a JSON file outside product changes. A clean Git source repository is
required; preserve unrelated work rather than discarding it. The runner creates
an isolated candidate and leaves the source repository untouched.

```sh
/opt/homebrew/bin/python3.14 -B /absolute/path/to/proofline/proofline.py run \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --seconds 900 --stage-seconds 600 --check-seconds 120
```

Own implementation strategy. The runner dispatches one coding attempt, freezes
its candidate and runs the caller-selected commands under the native read-only
boundary. No automatic model reviewer, prover, repair loop or publication runs.
All preparation, implementation and checks consume the same episode budget.
Use explicit executable paths. Checks can write temporary scratch artifacts but
cannot change the frozen product or access the network. Preserve failures,
unavailable observations and unfinished handoffs; never invent receipts or
silently restart a run to reset the budget.

Read back `proofline.py status <report.json>` before reporting check success.
Report the candidate and actual checked commands, failed/unavailable observations
and remaining source gaps. **CHECKS PASSED means the listed commands exited
successfully; full source correctness is not certified.** The caller decides
whether the implementation fulfills the request. A stale snapshot cannot inherit
old checks. No push, PR, merge or deployment is part of this workflow.

Historical `deliver` and `resume` require explicit `--experimental` selection.
Their model acceptance verdicts remain untrusted for complete-source coverage.
The original input/source/effect authority boundaries still apply; experimental
selection grants no contract adoption or remote mutation authority. Do not
invoke those paths as the current production workflow or reuse a stopped study.
