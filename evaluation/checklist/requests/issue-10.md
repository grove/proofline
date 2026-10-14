[vNext 3/9] Extract a minimal supported runner core from S6 experiments

## Goal
Reduce supported-runtime complexity **without losing the proven mechanical safeguards**. In particular, the current `checks/local_run.py` uses `checks/s6_baseline.py`; avoid depending on research/benchmark modules for normal product execution.

## Scope
- Identify the smallest reusable implementation boundary for snapshot preparation, optional Codex dispatch, explicit check execution, and report/status readback.
- Move or factor shared runtime helpers into clearly named production modules, rather than importing an S6 baseline from the supported path.
- Keep historical `deliver`/`resume` experiments and their original evidence preserved; do not silently restore experimental certification or publication.
- Retain host isolation, source/candidate/check identity, stale-snapshot detection, bounded cumulative budgets, actual process receipts and distinctions between check failure and unavailable execution.
- Keep the existing qualified macOS/Codex path working; portability is a separate hypothesis, not permission to remove safeguards.

## Acceptance criteria
- [ ] `proofline.py run` and `proofline.py status` operate with the same visible semantics and successful, failed, unavailable and stale outcomes.
- [ ] The supported run/check path no longer needs to import `checks/s6_baseline.py` or a historical study coordinator.
- [ ] Native-security and deterministic regressions cover candidate immutability, exact command matching, protected material, timeouts and resource accounting.
- [ ] Normal CI passes on its supported test matrix; native qualification remains explicit rather than mocked into a success claim.
- [ ] README/SKILL explain the small supported entry point and keep historical research clearly separated.
- [ ] No new compulsory model role, planning format, framework abstraction, or ceremony is added.

## Dependencies / out of scope
Follows the product direction in #1. May be implemented with offline tests initially; native-host validation still required for assurance claims.