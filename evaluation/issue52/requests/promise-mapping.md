# [vNext 6/9] Link source-grounded promises to checks and expose evidence gaps

## Why
A successful test suite can omit a material user promise. Proofline's value over `pytest`/CI should be an **honest, optional promise-to-evidence view**, not another AI verifier. Intentline already provides useful source-grounded `R1`–`Rn` rows; do not reinvent its planning schema inside Proofline.

## Core scope (works without Intentline)
Extend the supported, model-free `proofline.py check` / `status` record to accept **optional**, small caller-provided source-linked outcome rows, each with a stable ID, exact original-source citation and selected check IDs/argv associations. Preserve and display the full original request regardless of whether any rows were supplied.

## Acceptance criteria
- [ ] A direct check needs **no** acceptance plan, Intentline/P2P installation, second model call, additional mandatory file or approval ceremony. Existing run/check/status semantics and native sandbox/receipt integrity remain intact.
- [ ] Optional rows identify source-linked obligations and outcomes, including positive and negative behaviors, compatibility constraints and exceptions. Validate IDs, source identity/quoted lines, exact selected-command references and candidate binding; reject missing/stale/contradictory claims. Source text always outranks an incomplete mapping.
- [ ] Report, **per supplied obligation**, actual linked-check outcomes: `LINKED CHECKS PASSED (limited evidence)`, `CHECK FAILED`, `CHECK UNAVAILABLE`, or `NOT DEMONSTRATED`. Never call a green command proof of the full obligation or all obligations. A requirement with *no selected check* is not demonstrated, not failed.
- [ ] Support an **optional step by the same existing coding agent**: reread the complete original source, compare it with the recorded rows/selected checks, and propose any apparent omitted material promise or high-value negative/compatibility case with a verbatim source citation and test suggestion. Record such findings as **proposals/gaps**, not authenticated or complete review. Proofline itself dispatches zero extra models. If no gap analysis was performed, make coverage completeness **unknown**, not silently complete.
- [ ] Any listed expected behavior, `oracle`, or proposed check derived from an agent is explicitly a *proposed expectation*, not an independently established answer. Actual success requires executable receipts.
- [ ] Negative tests: valid green existing suite but source's Unicode promise left uncovered; missing/duplicate IDs, omitted material source quote, changed source, wrong candidate, forged command link, failed check, unavailable sandbox, stale receipt, and an advisory plan that omits a user constraint.
- [ ] Output stays concise; detailed source/check/receipt identities are available for inspection but do not clutter ordinary successful handoffs.

## Intentline integration boundary
This issue defines the **generic evidence mapping**, not a bundled Intentline parser. Follow-on **[Proofline #23](https://github.com/grove/proofline/issues/23)** may consume existing Intentline schema-1 `R` rows, boundaries, proposed oracles, evidence gaps and exact export identities as **optional untrusted guidance**, with no automatic adoption or peer execution. Keep source quotation and IDs compatible where straightforward; a caller-authored direct mapping remains equally supported.

## Non-goals
No automatic semantic completeness certificate, universal requirement extraction, automatic test generator, independent AI reviewer/prover, workflow planner, or PR/merge controller.

## Dependencies
After [#11](https://github.com/grove/proofline/issues/11) (implemented). Can proceed alongside [#14](https://github.com/grove/proofline/issues/14). [#16](https://github.com/grove/proofline/issues/16) must measure whether it actually catches missed outcomes at reasonable cost.
