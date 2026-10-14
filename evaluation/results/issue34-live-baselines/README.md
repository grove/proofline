# Issue #34: authorized baseline stop

On 2026-10-14 the unchanged frozen v1 controller executed all six ordinary
**GPT-6 Luna:high** baselines and stopped at its spending gate. Five candidates
passed every frozen behavioral case. Cache expiry failed an **unsupported
exception-class expectation**, so its correctness is disputed, not an established
implementation defect. All 18 B/C/D assignments are **unexecuted / unobserved**.
Recovery effectiveness and comparative overhead remain **unmeasured**.

The raw gate counted one failure, below its threshold of two. The stop remains
valid even if that disputed candidate is defective: at most one baseline could
be defective. No failed task was selected for an intervention, no candidate was
edited by the operator, and no correction, Sol diagnosis, retry or extra worker
message occurred. This is an insufficient-error pilot with an oracle-validity
limitation, not a successful recovery comparison or proof that all six are correct.

- [All 24 assignment records and model accounting](results-summary.json)
- [Exact user spending authorization](approval.json)
- [Post-study diagnostic observations](diagnostics.json)
- [Native receipts, original/final candidates and bookkeeping](raw-evidence.zip)
- [Original frozen source](../issue34-preparation/frozen-source.zip),
  [qualification](../issue34-preparation/README.md), and [declaration](../../recovery/README.md)
- [Issue assessment](../../../docs/ISSUE34.md) and [artifact hashes](hashes.json)

Freeze: `e6cd153ae5582fcbba5c7639b0f8e67fdb6ab09037376f19e67b44e6def5f2b9`.
Explicit approval covered 24 assignments, 48 native turns and 28,800 seconds.
The actual campaign used **six turns and 483.68 seconds**. The frozen source,
grader, prompts, models, ordering, limits and gate remain byte-for-byte unchanged.

## Initial and final observations

Each intervention cell below includes its initial and final status. **U/U** means
neither was observed; it never means independently incorrect or 0% success.
There were no corrections, so every A final candidate equals its initial tree.

| Task | A initial / final | B initial / final | C initial / final | D initial / final |
| --- | --- | --- | --- | --- |
| report-columns | Correct / Correct | U/U | U/U | U/U |
| config-overlay | Correct / Correct | U/U | U/U | U/U |
| retry-policy | Correct / Correct | U/U | U/U | U/U |
| cache-expiry | Disputed / Disputed | U/U | U/U | U/U |
| atomic-export | Correct / Correct | U/U | U/U | U/U |
| safe-zip | Correct / Correct | U/U | U/U | U/U |

The frozen oracle recorded 38 passed case groups and one failed group. Its literal
A score is 5/6; **this is not a validated 83.3% genuine-correctness estimate**.
The report keeps the original grade and `FALSE_ACCEPTANCE` label in raw evidence,
but classifies cache separately as `DISPUTED_ORACLE_EXPECTATION`. It does not
regrade it as correct. Aggregate success rates are null for the disputed A result
and unobserved B/C/D arms. Preparation's historical 0/6 placeholders are allocation
counts, not observed failure rates.

**Confirmed genuine defects: zero. Disputed failures: one. Defects corrected:
zero. Persistent genuine omissions: none established.** The failure occurs when
the cache oracle expects `ValueError` for a Boolean TTL, while the implementation
rejects it with `TypeError`. The original request requires validation of finite,
nonnegative numeric TTLs excluding Boolean values, but specifies no exception
class. The failing group stops there; its remaining checks, including loader
failure handling, do not establish a complete cache grade. No hidden result was
sent to a worker or used as correction feedback.

All six original repository suites passed in **post-campaign**, protected,
candidate-bound checks. No source-grounded behavior omission despite green
repository tests was confirmed. The raw cache false-acceptance label is not a
confirmed genuine false acceptance. There was no observed A blocking, assignment
execution failure, timeout or unavailable behavioral grade. False acceptance,
unnecessary blocking, green-probe omissions and recovery in B/C/D are unmeasured.

## Validity and environment limitations

The initial readiness review missed the cache oracle's overspecified exception
class; it was identified after the live failure. No revised oracle was substituted,
no outcomes were rewritten, and no frozen component was changed after exposure.
The v1 campaign is terminal. Any future executable revision needs a separate
freeze and explicit spending authorization; these exposed results cannot become
a fresh predeclared cohort by relabeling or rerunning them.

The grader's ancillary `repository_tests_passed: false` flags are also unreliable.
Its child unittest process runs from scratch without the product import path.
This flag was false for all 24 prevalidated controls despite their separate
protected repository suites passing. A post-study reference diagnostic reproduced
`ModuleNotFoundError: No module named 'app'`. The six candidate-bound repository
checks above diagnose that metadata problem; they do not replace frozen behavioral
grades or affect the gate. Diagnostic time was **3.37 seconds**, with zero models.

Workers recorded **22 nonzero shell-command exits**, including macOS `python3`
developer-tool launcher failures, wrong test-discovery locations, shell/syntax
errors and self-authored smoke-check failures. Luna continued within each ordinary
attempt. These are retained tool observations, not 22 failed assignments or 22
Proofline recoveries. No operator intervention repaired an implementation. The
post-study bookkeeping script's first launch also failed on its repository import
path before any check; running it with the repository on the path succeeded.

## Latency, tokens and cost

All episode times include isolation, native coding, snapshot capture and hidden
grading. Native-turn time is a subset, not another additive cost.

| A baseline, in executed order | Episode seconds | Luna native seconds | Uncached input | Cached input | Output | Native turns | Tools |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| safe-zip | 98.15 | 96.36 | 32,019 | 189,696 | 11,239 | 1 | 10 |
| report-columns | 62.27 | 60.54 | 27,932 | 182,272 | 6,258 | 1 | 21 |
| retry-policy | 56.21 | 54.53 | 25,604 | 116,736 | 5,534 | 1 | 17 |
| atomic-export | 78.03 | 76.40 | 17,622 | 143,872 | 7,392 | 1 | 25 |
| cache-expiry | 116.91 | 115.24 | 49,190 | 139,008 | 7,912 | 1 | 17 |
| config-overlay | 72.10 | 70.34 | 39,542 | 110,592 | 5,063 | 1 | 19 |
| Total A | 483.67 | 473.40 | 191,909 | 882,176 | 43,398 | 6 | 109 |

Input totals are **1,074,085**, including **882,176 cached input**; uncached is
input minus cached. Reasoning output is already part of output and is not added
again. Raw session observations and normalized stage usage are retained. Sol used
**zero tokens, turns and tools**. B/C/D episode latency, correction latency and
cost per delivery are **not measured**, rather than zero-cost successful deliveries.

Campaign wall time was **483.68 seconds**, including controller overhead. Hidden
grading used **3.99 seconds** inside that time. Primary public probes, diagnosis
and bounded correction used zero time because none executed. Preparation and
native qualification separately cost **14.95 + 98.18 seconds**. Including these
and the diagnostics gives **600.18 measured seconds**; development/usability,
reporting, authoring and human work are additional and incompletely observed.
Checks are not free. Implementation validation separately ran 241 tests with eight
native opt-in skips in 178.02 seconds, plus three fixed oracle-control tests.

**Actual billing and total economic cost per independently correct delivery are
unknown.** A's campaign time divided by its five confirmed correct deliveries is
96.74 seconds; this is a conservative resource ratio that also charges the
disputed slot. Including the measured setup/diagnostics gives 120.04 seconds per
confirmed delivery, excluding unobserved authoring/human cost. These are not
monetary savings or B/C/D estimates.

**Hypothetical token-price sensitivity only:** with Luna prices `u`, `c`, `o`
in dollars per million uncached-input, cached-input and output tokens, respectively,
the token-only campaign estimate is `0.191909*u + 0.882176*c + 0.043398*o`.
At illustrative prices `(1, 0.1, 5)` it is **$0.4971**, or **$0.0994** per
confirmed delivery; at `(3, 0.3, 15)` it is **$1.4913**, or **$0.2983** per
confirmed delivery. These arbitrary sensitivity inputs are not provider prices,
observed charges or a quote, and omit compute, setup, authoring and human cost.

## Decision

**Proofline feedback: INCONCLUSIVE. Selective Sol diagnosis: INCONCLUSIVE.**
No B–C or C–D comparison executed, so there is no measured gain or added overhead
for either intervention. Keep both optional; this pilot provides no reason to add
mandatory checks, orchestration or Sol reasoning. It also provides no recovery
evidence supporting removal of the existing lightweight, model-free check option.

Staged machinery qualification remains 24/24 offline/native controls and 12/12 B/C
eligibility comparisons, plus the reused #32 seeded thread handoff. None counts
as observed natural recovery. Five finite-correct baselines and one disputed
oracle grade across six fixed synthetic repositories, one repetition and a
conditional gate cannot establish population reliability or production value.
The finite oracle has one author and partially shared alternative validation.
Issue #34 remains open for review; PR #35 must not merge without explicit approval.
