# Issue #34 — observed baseline stop

The explicitly authorized [frozen six-task study](../evaluation/recovery/README.md)
executed **all six Luna:high baselines** on 2026-10-14 and stopped under its
predeclared spending gate. Five passed every frozen behavioral case. Cache expiry
received a **disputed oracle failure**, because the grader requires an exception
class absent from the original request. **All 18 B/C/D assignments remain
unexecuted / unobserved**, with no observed success rate. No Sol, correction or
additional intervention assignment ran.

The [live report](../evaluation/results/issue34-live-baselines/README.md) includes
all 24 initial/final observations, candidate identities, native receipts,
model-separated usage, diagnostics and explicitly hypothetical price sensitivity.
The [original preparation evidence](../evaluation/results/issue34-preparation/README.md)
and historical #16/#32 cohorts remain unchanged.

Freeze: `e6cd153ae5582fcbba5c7639b0f8e67fdb6ab09037376f19e67b44e6def5f2b9`.
[Recorded authorization](../evaluation/results/issue34-live-baselines/approval.json)
covers the exact declaration: 24 assignments, 48 native turns and 28,800 seconds.
The actual campaign used **six turns and 483.68 seconds**. All source, seed,
runtime, prompt, model, ordering, budget and gate hashes still match. No frozen
component or production correction rule was modified.

## Outcomes and validity

| Baseline | Initial independent observation | Final independent observation |
| --- | --- | --- |
| report-columns | Correct | Correct |
| config-overlay | Correct | Correct |
| retry-policy | Correct | Correct |
| cache-expiry | Disputed oracle expectation | Disputed oracle expectation |
| atomic-export | Correct | Correct |
| safe-zip | Correct | Correct |

The frozen controller counted one defective baseline and stopped because
**one is fewer than two**. This gate decision is robust to the disputed cache
classification: at most one candidate could be defective. No task was cherry-picked,
retried, corrected, regraded under new expectations or made harder after exposure.
The five passing grades establish finite correctness; the sixth does not establish
either a genuine implementation defect or complete correctness.

The hidden cache assertion expects `ValueError` for invalid TTL types. Luna
validates and rejects a Boolean TTL with `TypeError`; the original request
specifies numeric validation but no exception class. The grouped hidden assertion
then aborts before checking its remaining cases. The raw `FALSE_ACCEPTANCE` and
5/6 oracle score are preserved, but neither is presented as an established genuine
false acceptance or observed 83.3% genuine-correctness rate. **Confirmed genuine
defects: zero; disputed grades: one; observed recoveries: zero.** Recovery
effectiveness remains unmeasured. The initial readiness review missed this oracle
fidelity defect; it was discovered after the live failure.

The ancillary hidden-grader repository-test flags are also unreliable: child
discovery runs from scratch without the product import path. This also affects
all prevalidated controls. A separate model-free reference diagnostic reproduced
the import error, and all six delivered candidates passed their original tests
under protected, candidate-bound post-campaign execution. Those diagnostics do
not alter independent behavioral grades, feed a worker, or change the gate.
No source-grounded omission despite green repository tests was confirmed.

There were no unavailable behavioral grades, assignment execution failures or
timeouts. Workers encountered 22 nonzero shell-command exits, including macOS
Python launcher and test-discovery problems, and continued within their ordinary
attempts. Tool failures and self-authored smoke checks are not counted as
Proofline recovery. Intervention false acceptances, unnecessary blocking,
coverage gaps and recovery are unmeasured because those arms did not execute.

## Resources and recommendation

Luna reported **1,074,085 input tokens**, comprising **191,909 uncached** and
**882,176 cached**, plus **43,398 output tokens**, six native turns and 109 tool
executions. Cached input is not counted again; reasoning output is part of output.
Native-turn time was 473.40 seconds; it is included in campaign wall time.
Hidden grading took 3.99 seconds inside the campaign. Sol usage and bounded
correction overhead were zero; their delivery latency and benefit are unobserved.

Preparation took 14.95 seconds and native qualification 98.18 seconds. Post-study
diagnostics took 3.37 seconds with zero models. Total measured campaign/setup/
diagnostic time was 600.18 seconds, before incompletely observed authoring,
usability, reporting and human work. Actual billing and total economic cost per
independently correct delivery remain unknown. The report's token-price scenarios
are labeled hypothetical and exclude those costs.

**Proofline feedback: INCONCLUSIVE. Selective Sol diagnosis: INCONCLUSIVE.**
There is no measured B–C or C–D effect. Keep Proofline model-free and optional,
and keep Sol optional with no routine planning or successful-implementation review.
This pilot gives no evidence for adding mandatory stages or further recovery
infrastructure. Staged qualification (24/24 controls, 12/12 B/C comparisons and
the reused #32 handoff) demonstrates machinery, not natural recovery.

Validation ran 241 repository tests with eight native opt-in skips; three fixed
oracle-control tests passed separately. Source/archive hashes, raw native receipts
and candidate trees were revalidated. The live archive adds about 348 KB of
compressed evidence without duplicating the original frozen source or qualification.

The v1 campaign is terminal. Any future executable revision requires a separately
frozen declaration and fresh explicit authorization, with outcome exposure
disclosed; this cohort cannot silently be relabeled as fresh. Six fixed synthetic
repositories, one repetition, a finite single-author oracle and a conditional
spending gate cannot establish population reliability or production value.
Issue #34 stays open for review of the recorded stop and oracle limitation.
PR #35 must not merge without explicit user approval.
