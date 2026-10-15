# Make uncovered requirements actionable with optional next-check guidance

## Problem

Proofline already implements honest source-linked coverage reporting in [#13](https://github.com/grove/proofline/issues/13), actionable *failed-check* feedback in [#14](https://github.com/grove/proofline/issues/14), and optional Intentline import in [#23](https://github.com/grove/proofline/issues/23). `check` / `status` show each supplied requirement as linked checks passed (limited evidence), failed, unavailable, or NOT DEMONSTRATED. Overall coverage is correctly UNKNOWN.

**Remaining usability gap:** when a coding agent sees `R3 NOT DEMONSTRATED: No selected executable check linked`, it has to dig through `report.json` to find Intentline's already-imported `planned_evidence`, `boundaries`, `seam`, and gap reasons, then work out what check to add. Existing CLI summaries say *what is missing*, but offer little concrete *next step*. Preserve the distinction between a **missing check** and an **observed failing check**.

## Goal

Make uncovered obligations **actionable to the already-running coding agent**, using existing, explicitly unverified data; do **not** create a new verification engine. A concise report might say:

```
Promise evidence: 2/3 mapped rows have linked passing checks (limited); overall coverage UNKNOWN
  R3 NOT DEMONSTRATED — no selected executable check linked
     Next: examine the source-cited account-lockout obligation.
     Proposed check focus (unverified Intentline plan): five failures, sixth attempt,
     and reset boundary. Select/author an executable assertion, link its exact argv
     to R3, and rerun proofline check; passing remains limited evidence.
```

This is **guidance**, not an automatically established test oracle or a request to run any command.

## Small implementation slice

1. Enhance the existing `promise_evidence.format_lines()` / optional evidence report to surface **bounded, per-R next-check hints** for NOT DEMONSTRATED requirements. Derive hints **only from fields already validated and retained** by the direct promise mapping (if present) and optional Intentline import (`planned_evidence`, `boundaries`, `seam`, `evidence_gap_reasons`, source citations). Do **not** infer tests from arbitrary source prose or invent executable commands.
2. Distinguish: **no linked check**, **failed linked check**, **unavailable/stale evidence**, and **caller/Intentline-proposed check**. Recommend an additional selected check for an *unlinked* requirement, diagnosing actual failure evidence for a *failed* check, or restoring re-runnable evidence for *unavailable/stale* checks. Never describe absent evidence as an implementation defect.
3. Keep the normal successful/mapping-free path unchanged and concise (e.g. top 3 gaps, with full detail in existing `report.json`); preserve truthful `coverage_completeness: UNKNOWN`. If no source-grounded planned evidence is available, report this explicitly instead of generating a confident suggestion.
4. Document **one optional existing-agent workflow**: inspect imported R rows → select/author behavior-focused checks (including negative/compatibility boundaries where proposed) → supply explicitly selected exact argv and optional R links → `check` → inspect `status` → revise/check again if needed. The agent must validate proposed expectations against the full original request; Intentline planning remains advisory.

## Acceptance criteria

- [ ] Existing `check`, `status`, `--promises`, `--intentline-export`, `--intentline-links` work without breaking flags, record readback, hashes, candidate identity, or sandbox/receipt integrity.
- [ ] For an imported R without a linked selected check, short actionable guidance identifies R ID + reason, cites **existing** source/plan data when available, labels suggestions **unverified**, and names the human/agent action (select/author assertion, link exact selected check, rerun).
- [ ] Hints never assert that a passed check semantically proves a requirement, or that all source requirements have been captured. All completion/coverage claims remain UNKNOWN beyond bounded receipts.
- [ ] No fabricated check argv, claims of tests executed, inherited approval, source rewriting, automatic link guessing, or execution of exported planning artifacts. Missing fields are handled without invented expectations.
- [ ] Failing, unavailable and stale receipts keep their distinct meanings and do not become `NOT DEMONSTRATED because no test was written` or `implementation bug` without evidence. `status` re-read reproduces the same evidence-grounded guidance for intact records.
- [ ] Offline tests cover: deliberately uncovered material requirement with all selected checks green; advisory boundary/oracle hint; missing planned evidence; existing linked-check pass/fail; unavailable/stale receipts; tampered mapping readback; no-Intentline/no-mapping behavior; bounded output.
- [ ] One short documented before/after example (e.g. valid login, invalid password, 5-failure lockout) demonstrates the *agent's next step*, not a claimed correctness improvement. No new study harness.

## Explicit non-goals / safeguards

- No universal semantic prover, LLM reviewer, automatic test generator, second-model call, contract schema redesign, compulsory planning step, mandatory CI gate, autonomous repair or PR/merge action.
- **Do not reopen or replace #13/#14/#23.** Reuse their trusted boundaries and fields; prefer a small code/docs/tests change over new commands or infrastructure.
- No release-blocking mandate until real-world benefit is observed. Compare usability and overhead through ordinary dogfooding rather than reviving the blocked [#46](https://github.com/grove/proofline/issues/46) benchmark machinery.

## Dependencies

All necessary source/evidence plumbing is already merged: [#13](https://github.com/grove/proofline/issues/13), [#14](https://github.com/grove/proofline/issues/14), [#23](https://github.com/grove/proofline/issues/23). The existing source/Intentline output examples in [README](https://github.com/grove/proofline/blob/main/README.md#optional-connect-requirements-to-check-evidence) are a suitable fixture starting point.
