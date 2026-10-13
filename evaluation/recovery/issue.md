## Why

The merged [#32 / PR #33](https://github.com/grove/proofline/pull/33) study delivered **20/20 independently correct implementations**, including **4/4 with Luna:high alone**. Sol planning/verification added large time overhead without observed quality improvement. The real same-thread correction mechanism was qualified on a **staged defect**, but **zero naturally occurring implementation errors required it**. [#16](https://github.com/grove/proofline/issues/16) had a similar correctness ceiling.

We now need evidence from **realistic tasks where an agent may actually miss part of the original promise**, not another general-purpose orchestration framework. The question is: **When Luna makes mistakes, do selected executable checks, Proofline's trustworthy feedback and one Luna correction improve independently correct deliveries enough to justify their end-to-end cost? Does rare, check-triggered Sol diagnosis add anything?**

## Bounded design — new corpus, no inherited success claims

- Freeze **six new, representative coding tasks** (prefer real-world Python repository changes, at least several genuinely multi-file) before live dispatch. Include a straightforward control; emphasize API compatibility, changed behavior across modules, negative cases, failure handling, and requirements that ordinary repository tests can miss. Avoid reusing #16/#32 private grading vectors or their task/solution pairs. No live credentials or uncontrolled external services.
- Derive and independently validate a **finite hidden behavioral oracle** from each *original request*, before seeing any agent implementation. Include correct/alternative/green-public-tests-but-defective controls. Keep oracle values and control implementations unavailable to all workers and Sol.
- Freeze each initial repository, complete source request, visible existing tests, **additional source-grounded public executable probes** (their expected outcomes independently validated), exact models/reasoning/host, prompts, randomized or balanced order, per-episode limits, all assigned slots and stop rules. Checks may be revealed to intervention arms only **after their initial candidate is frozen**; never feed the hidden grader as feedback.
- Reuse existing Proofline check, bounded correction, native isolation and evaluation/accounting infrastructure. Prefer a small adapter/fixture change over a new runner framework. First exercise `proofline-check` on one real agent-built change; record only concrete usability blockers, and fix the smallest reproducible defect if necessary.

## Compare four approaches on the same six frozen tasks

| Arm | Workflow |
| --- | --- |
| **A — Luna ordinary** | GPT-6 Luna:high implements and self-tests normally within its total budget; no imposed planner, Proofline, or reviewer |
| **B — Checks + Luna** | Luna:high implements; the same predeclared public executable probes run through ordinary protected commands **without Proofline**; on a genuine check failure, allow **one** Luna correction using the check evidence |
| **C — Proofline + Luna** | As B, but use Proofline's model-free `check`/receipt-bound feedback and the supported one-correction path; same probes, Luna configuration and opportunity to repair |
| **D — Selective Sol + Proofline + Luna** | As C, but invoke **Sol:high only for a qualified, observed check-grounded defect** to provide a source-grounded *advisory* diagnosis before the **same single** Luna correction; no routine Sol planning/review or speculative extra triggers |

A vs B measures the **probe/feedback/repair package**; B vs C isolates Proofline's delivery mechanism given the same probes; C vs D estimates the additional effect/cost of **conditionally invoked Sol**. Do not credit Proofline for better tests that B also received, or credit Sol for additional repair attempts. All methods get the **same original request and starting product bytes**, same supported isolation boundary and matched **total** per-assignment budget, including checks, review, corrections and grader runtime. A may use its normal self-testing/revisions within that budget.

**Predeclared spending gate:** Run and independently grade the **six A-arm baseline implementations first**. If **fewer than two** are demonstrably defective under the hidden oracle, stop the study as a **correctness ceiling/insufficient-error pilot**; mark the remaining 18 assigned cells `NOT_EXECUTED`. Do **not** cherry-pick only the failed tasks, expand the corpus based on observed outcomes, or claim recovery effectiveness. Otherwise run **all 18 remaining assignments**, not just the initially failed tasks; maximum **24 primary assignments (6 × 4)**. The gate and any resulting conditional inference must be explicit in the report.

## Trust, attribution and costs

- One additional correction attempt maximum in B/C/D, using the original Luna implementer where supported. Trigger solely on an **independently validated public executable assertion** failing on the exact frozen candidate—not an advisory Sol claim, a private grade, an agent-authored test expectation, an unavailable tool or a speculative coverage gap. Freeze/recheck the corrected candidate; keep initial and final grades distinct. If B cannot match the correction opportunity without changing the host, record the deviation rather than claiming clean isolation.
- In D, Sol sees the complete original request, actual frozen candidate and **only public trusted check receipts**; it never sees its own prior plan (none is required), hidden expected outputs or independent grading results. Sol's diagnosis cannot alone authorize repair; it gets **zero dispatches on green checks**. An omitted promise that is not covered by a prevalidated public probe remains an honest coverage gap.
- Distinguish **normal first-pass failures** from seeded/staged correction qualification. Use seeded defects to qualify machinery, but **never count them as evidence of natural improvement**.
- Track all-assigned independently correct deliveries, initial/final correctness, recovered defects, persistent failures, false accept/false block, missed promises despite green public tests, check unavailability, and unexecuted/failed slots. Compare paired differences honestly, report small-sample uncertainty and limitations.
- Record full elapsed seconds, Luna/Sol model identifiers and reported uncached/cached/output tokens, tool/turn counts, probe setup/execution, correction and Sol time, failed attempts, human intervention and **total cost per independently correct delivery**. Observed billing remains **unknown** unless actual reliable billing is available; hypothetical price sensitivity must be labeled as such. No cached-input double counting. Include the extra cost of developing/qualifying public probes rather than calling checks free.
- If B and C are equivalent, or errors do not materialize, say so. Recommend **keep / simplify / remove / inconclusive** based on independent results, not passing tests or plans.

## Boundaries and authorization

- **Evaluation only**, no new adaptive Sol router, mandatory planner, multi-model supervisor, Proofline/P2P integration requirement, or widened production correction policy.
- Keep `proofline.py check` zero-model, agent-owned and optional; don't change normal coding workflows to satisfy the benchmark.
- Declare a **fresh frozen, bounded native study** and obtain explicit authorization for live model/compute expenditure **before dispatch**. Existing #32 approval cannot be reused. Never silently change model, reasoning setting, expected result, isolation profile or task difficulty after inspecting candidate outcomes. If live access cannot be qualified, stop with an auditable incomplete result.
- Prefer compact reproducible evidence and hashes to large repetitive archives. Preserve #16/#32 historical cohorts byte-for-byte.
- Relevant separate research: [P2P #52](https://github.com/grove/promise-to-proof/issues/52) and [P2P #116](https://github.com/grove/promise-to-proof/issues/116). Reuse their *methods* if helpful, not hidden outcomes or already-exposed test cases.

## Definition of done

A small, independently graded **live recovery comparison** on all predeclared assignments **or** a fully reported predeclared early-stop ceiling, with results and end-to-end resource costs sufficient to decide whether Proofline check/feedback should remain a lightweight option and whether check-triggered Sol help merits any further engineering. Do not assert measured recovery benefits if no actual initial defects occur. Create a focused PR; **do not merge without explicit user approval**.
