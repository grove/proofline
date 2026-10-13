# Completed native Sol/Luna pilot: no observed assistance gain

All **20/20 live assignments delivered independently graded correct candidates**:
4/4 in every arm, initially and finally. No managed correction was needed.
Sol planning and verification added time without an observed correctness gain.
Luna:high alone is the practical choice for these four tasks. This does not
establish its reliability on other work or monetary savings.

The user explicitly authorized fresh declaration `issue32-sol-luna-high-lenient`,
freeze SHA-256 `c8ea1f9b55ce5f8319e3c77090caf6c8038c597c0bc610348751382dc011da4e`.
The serial campaign ran **2026-10-13 19:15:47–20:38:58 UTC**, 83.19 minutes,
using **36 native turns: 16 Luna and 20 Sol**, always `high`. No assignment retry,
substitution, grader repair, operator candidate edit or extra worker message
occurred. The stopped cohorts remain separate.

## Deliveries and end-to-end time

Times include native startup/shutdown, model tools, setup/freezing, selected
checks, verification and independent grading. Each arm has four assignments.

| Arm | Initially / finally correct | Mean seconds per correct delivery | Native turns | Tool executions | Nonzero command exits |
| --- | --- | ---: | ---: | ---: | ---: |
| Luna alone | 4/4 / 4/4 | 102.60 | 4 | 82 | 9 |
| Sol plan → Luna | 4/4 / 4/4 | 322.37 | 8 | 135 | 12 |
| Luna → Sol verification | 4/4 / 4/4 | 207.40 | 8 | 105 | 4 |
| Sol plan → Luna → Sol verification | 4/4 / 4/4 | 463.45 | 12 | 150 | 9 |
| Sol alone | 4/4 / 4/4 | 151.83 | 4 | 41 | 0 |

**False acceptances: 0; correct-but-blocked: 0; unavailable assignments: 0;
green repository test omissions detected by the finite grader: 0.** All eight
plans were valid advisory exports; all eight reviews were valid and reported no
findings. All eight selected Proofline check sets passed. Managed corrections,
correction improvements and regressions were all zero. Initial means the frozen
candidate after the implementer's normal self-checks, before managed correction.

There were **zero failed native invocations**. The 34 nonzero command exits
include intended CLI rejection probes, shell/Python quoting errors, a system
Python launcher error and failed self-check assertions. They are not 34 product
defects. The controller recorded 2,179 process launches, including coding, checks,
freezing and grading; this is distinct from model tool counts. Provider-internal
model calls/retries are unexposed. Tool counts include
native command execution and file changes, deduplicated by item identity.

The hybrid took **4.52× Luna-only time and 3.05× Sol-only time** per correct
delivery. Planning added 219.77 seconds without verification and 256.05 seconds
with verification, per task. The verification package added 104.81 seconds
without planning and 141.08 seconds with planning. All paired correctness effects
were zero. Four fixed tasks, one repetition and imperfect position balance give
descriptive observations, not population estimates; a zero bootstrap interval
at this ceiling cannot rule out unseen-task effects.

| Arm | Planning | Implementation | Proofline checks | Sol verification | Correction | Grading | Other setup/freezing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | 0 | 370.28 | 0 | 0 | 0 | 35.72 | 4.40 |
| Plan | 900.63 | 345.54 | 0 | 0 | 0 | 37.04 | 6.28 |
| Verify | 0 | 294.91 | 4.62 | 487.19 | 0 | 35.69 | 7.20 |
| Hybrid | 816.45 | 493.73 | 3.55 | 492.96 | 0 | 39.14 | 7.96 |
| Sol | 0 | 566.52 | 0 | 0 | 0 | 36.36 | 4.46 |

These are **total seconds across four assignments**, not means. Model self-checks
and model-run probes are included in their native stage; per-tool duration is
unavailable. The final candidate was unchanged, so its bound initial grade was
reused. Current model-free preparation took 201.51 seconds separately. The
previously completed four-turn handoff qualification took 343.35 seconds and
was reused with zero new inference; its cost is not counted twice. Failed earlier
attempts and their unknown consumption remain in the historical reports, not
pooled into this cohort. Authoring, active human attention and total project
spending are unmeasured.

## Actual tokens and unknown billing

| Arm | Model | Input tokens | Cached input subset | Output tokens |
| --- | --- | ---: | ---: | ---: |
| Luna | Luna | 728,284 | 627,712 | 27,685 |
| Plan | Luna | 707,292 | 584,704 | 22,685 |
| Plan | Sol | 1,292,048 | 1,146,368 | 25,312 |
| Verify | Luna | 514,649 | 392,448 | 20,683 |
| Verify | Sol | 471,783 | 321,408 | 15,073 |
| Hybrid | Luna | 780,775 | 653,312 | 21,439 |
| Hybrid | Sol | 1,459,722 | 1,161,728 | 40,220 |
| Sol | Sol | 462,928 | 359,424 | 19,619 |

Totals: Luna **2,731,000 input / 2,258,176 cached / 92,492 output**;
Sol **3,686,481 input / 2,988,928 cached / 100,224 output**. Every primary stage
reported usage. Cached input and reasoning output are subsets, not extra tokens
to add. Native CLI session-cumulative usage is normalized before aggregation;
no primary thread was resumed. The historical correction's real cumulative
counter delta is retained in its separate normalized report.

**Observed dollars and credit debits remain unknown.** A read-only
`account/usage/read` probe returned `threadUsage: null` for all 36 actual primary
threads, with no RPC error and zero model turns. Only thread-specific results
were retained; no credentials were retrieved and no account-wide activity
was published. The installed schema can expose model/effort/speed token groups and
estimated credit/USD consumption when a billing route supports them. Even those
fields would be estimates, not invoice charges.

### Pricing sensitivity, not observed spending

Assume the published **standard** token-credit rates on
[Codex pricing](https://learn.chatgpt.com/docs/pricing), accessed 2026-10-13:
Luna 2.5 / 0.25 / 12.5 and Sol 50 / 2.5 / 250 credits per million uncached
input / cached input / output tokens. Actual speed, billing-route adjustments,
subscription allocation and charges are not established by this assumption.

| Arm | Hypothetical credits per independently correct delivery |
| --- | ---: |
| Luna | 0.1886 |
| Plan | 4.3035 |
| Verify | 3.1882 |
| Hybrid | 7.1522 |
| Sol | 2.7446 |

Calculate `(input-cached)*input_rate + cached*cache_rate + output*output_rate`.
This projection excludes check compute, preparation/qualification, authoring,
human attention and unexposed charges. **It is not a monetary savings claim.**

For a broader sensitivity family, hold each model's output/input ratio at 5,
Luna cache/input at .1 and Sol cache/input at .05. Let `r` be Sol's uncached unit
price divided by Luna's. Hybrid costs `0.0749973 + 0.1392951*r` per correct
delivery in normalized model-price units; Luna costs `0.07544205`, and Sol costs
`0.05489255*r`. Hybrid beats Luna only for **0 < r < 0.003193**, versus the
published standard-credit ratio of **20**. It has **no positive break-even r
against Sol** in this family. These conditional model-price results do not
establish actual total dollar cost.

## What to keep

- **Luna:high alone:** 4/4 deliveries with the least observed episode time.
- **Sol planning:** working advisory exports, substantial overhead, no observed
  gain here; keep optional.
- **Sol verification:** complete original-source reads and real receipt/candidate
  inspection worked; no defect found or gain observed here; keep optional.
- **Proofline checks:** eight model-free, candidate-bound check sets cost 8.17
  seconds total. Keep existing optional checks. Their separate correctness benefit
  is not identified by the verification package or this ceiling.
- **Bounded correction:** the original-thread repair/freeze/recheck worked in the
  staged native control. Efficacy on naturally occurring coding errors was not
  measured in this primary cohort.

A source-cited Sol omission with green checks still cannot authorize correction.
The [separate assessment](../../../docs/ISSUE32_CORRECTIONS.md) proposes selection
from predeclared, source-grounded, independently validated public probes, with a
checks-only comparison. It remains unimplemented and unauthorized; no speculative
finding, self-authored oracle or private grade changed this study.

## Evidence and reproduction

[Results summary](results-summary.json) contains all 20 outcomes, initial/final
grades, candidate trees, stage times, native identities, model-separated usage,
paired comparisons and the conditional pricing calculation.
[Raw evidence](raw-evidence.zip) retains full receipts, candidates, seeds,
private native grades, controls, manifest, prompts and process records.
[Frozen sources](frozen-source.zip) retains this exact declaration, every pinned
source and its historical archives, plus the pinned Intentline producer.
The models' sandbox permissions excluded the private grader and its outputs.

The final audit revalidated all 36 native lifecycle/event hashes and exact model
and effort arguments; all eight Proofline receipt/candidate bindings; all
original-source copies; independent thread identities; unchanged final trees;
1200/900-second budgets; zero operator edits; and unchanged frozen inputs.
Native command output contains the complete source for every Sol review.

Run `python3.14 -B evaluation/results/issue32-lenient-results/analysis.py` to
reproduce the compact summary and pricing projection from the raw archive,
without models or checks. Its decimal arithmetic has executable self-checks.
[Consumption probe](billing-probe.py), [installed response schema](billing-schema.json)
and [filtered response](thread-consumption.json) record the billing investigation.
[Hashes](hashes.json) bind the published files. The archive regression test reads
actual native receipts through the existing parser and checks original-source
and freeze fidelity. All earlier frozen evidence is retained separately.
