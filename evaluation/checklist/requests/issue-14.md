[vNext 7/9] Return concise, actionable failure feedback to the coding agent

## Why
A real failing check is valuable only if the agent can readily act on it. Avoid long generic reviews: deliver reproducible evidence and sharply distinguish product defects from broken verification.

## Scope
Enhance the local `check` report and supported managed `run` output with a short failure summary and structured details. Preserve full raw receipts separately. Never invent expected results where the check did not specify them.

## Acceptance criteria
- [ ] For each check, report exact argv, exit status, elapsed time, bounded stdout/stderr references, and frozen candidate/source identity.
- [ ] A failed behavior assertion may show supplied expected and observed values and linked outcome IDs; otherwise report the actual command failure without fabricated expectations.
- [ ] Distinguish observed check failures, missing/insufficient evidence, environment/boundary unavailability, timeouts, and stale receipts.
- [ ] Produce concise plain-language guidance an existing coding agent can act upon; preserve logs for audit without dumping them into the primary answer.
- [ ] Successful commands produce a short result and do not trigger another reviewer or unnecessary model invocation.
- [ ] Tests cover failing and passing commands, truncated or missing output, timeouts, unauthorized mutation attempts, malformed expected/actual metadata, and correct status re-read.

## Out of scope
Another AI reviewer, mandatory static analysis bundle, automatic diagnosis disguised as ground truth, or auto-correction.

## Dependencies / order
After #11; integrate with optional mapping from #13, but do not block this issue on full contract integration.

---

## Source-grounded evidence feedback (13 October 2026)

When optional [#13](https://github.com/grove/proofline/issues/13) requirement IDs/source citations are present, report the affected `R` IDs alongside actual command receipts, and distinguish **a demonstrated failing test** from **an untested promise / an unavailable check / a proposed expected behavior**. Do not invent a test expectation from a planner's wording or call a missing check a candidate defect. Without any requirements mapping or Intentline, the ordinary concise check feedback must remain fully usable. No model dispatch or peer integration belongs in the mandatory feedback path.
