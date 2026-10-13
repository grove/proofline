# Issue #16: observed matched delivery outcomes

13 October 2026. **Sixteen assigned attempts, sixteen observed; four tasks per arm.**
This is a bounded comparison at independently frozen finite behavioral seams.
It does not establish general superiority or semantic completeness.

**No added arm improved observed delivery correctness: every arm delivered 4/4.**
Planning-only added 98.478 seconds per delivery (+72.9% episode time) and used
2.67× reported input + output tokens versus ordinary; combined added 120.394
seconds (+89.1%) and used 2.85× tokens. **Keep the additional stages optional.**

| Assigned arm | Correct deliveries / assigned | False acceptance | Correct but blocked | Incorrect without handoff | Unavailable / missing |
| --- | --- | --- | --- | --- | --- |
| Ordinary | 4/4 | 0 | 0 | 0 | 0 / 0 |
| Proofline-only | 4/4 | 0 | 0 | 0 | 0 / 0 |
| Intentline-only | 4/4 | 0 | 0 | 0 | 0 / 0 |
| Combined | 4/4 | 0 | 0 | 0 | 0 / 0 |

All assigned attempts remain in the denominator. Independently correct code
and an accepted delivery are distinct: Proofline arms also require current
selected-check success; rejected combined imports do not fall back to unmapped
checks. Planning-only advice cannot block an independently correct product.
Worker-generated artifact failures are observations, not infrastructure stops.

| Matched task | Ordinary | Proofline-only | Intentline-only | Combined |
| --- | --- | --- | --- | --- |
| atomic-transfers | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY |
| locale-fallback | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY |
| dependency-order | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY |
| fifo-upserts | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY | CORRECT_DELIVERY |

The private oracle includes ordered/intermediate/self-overdraft validation,
boolean rejection, exact locale fallback and empty-but-found translations,
source-ordered readiness and disconnected cycles, FIFO updates/zero capacity,
untested batch behavior, immutability, extra keys and unchanged CLI compatibility.
The source-conflicting alphabetical test and tempting locale grammar/default
assumptions are independently specified, not adopted from candidate tests.
Before dispatch, native grading accepted eight correct/algorithmically different
controls and rejected all four missing-batch defects despite green repository
tests. Both worker and grader isolation and the real producer/adapter/check
roundtrip were observed before coding. Qualification dispatched no models.

| Arm | Episode seconds total / per correct delivery | Input | Cached input subset | Output | Native coding invocations | Agent tool executions |
| --- | --- | --- | --- | --- | --- | --- |
| Ordinary | 540.523 / 135.131 | 360,013 | 266,112 | 17,409 | 4 | 27 |
| Proofline-only | 580.862 / 145.215 | 376,654 | 295,936 | 16,603 | 4 | 27 |
| Intentline-only | 934.437 / 233.609 | 977,596 | 798,336 | 30,695 | 4 | 83 |
| Combined | 1022.097 / 255.524 | 1,043,502 | 877,952 | 31,175 | 4 | 78 |

| Arm versus ordinary | Mean paired episode seconds added | Total known input + output tokens added |
| --- | --- | --- |
| Proofline-only | +10.085 | +15,835 |
| Intentline-only | +98.478 | +630,869 |
| Combined | +120.394 | +697,255 |

Cost differences describe this fixed task/order sample; they are not causal
latency estimates. Cached input is already included in input and is not added twice.

Native qualification, including controls: 62.970 seconds.
Independent grading: 86.362 seconds.
Campaign wall time, including grading: 3170.521 seconds.
These measurements overlap and are not added. Study authoring remains unmeasured.

Episode time includes plan creation/export, coding/self-checks, candidate freezing,
check setup/execution and feedback/status readback. Each arm had the same
600-second agent allocation inside a 900-second episode; planning consumed that
allocation. No extra planner/reviewer/prover, correction turn, adoption, manual
candidate edit or additional worker message was used. There is no enforceable
token cap in this transport. Cached input and reasoning output are subsets.
Dollar prices, initiating-agent usage, active human time, backend weight revision
and provider-internal calls are unknown. Native invocation counts are not a claim
that the provider made only one inference per turn.

| Matched delivery contrast | Percentage points | Task-bootstrap 95% descriptive interval |
| --- | --- | --- |
| Proofline − ordinary | +0.0 | [0.0, 0.0] |
| Intentline − ordinary | +0.0 | [0.0, 0.0] |
| Combined − ordinary | +0.0 | [0.0, 0.0] |
| Combined − Intentline | +0.0 | [0.0, 0.0] |
| Combined − Proofline | +0.0 | [0.0, 0.0] |
| Interaction: combined − Intentline − Proofline + ordinary | +0.0 | [0.0, 0.0] |

These intervals enumerate resampling of the four observed matched tasks; they
are descriptive, not population confidence intervals. A [0,0] interval merely
reflects no variation in those four contrasts and cannot rule out differences
on unseen requests, another model or another run. Assignment order was frozen
and serial; there was one repetition. No synergy claim follows from R labels.

| Secondary observation | Count |
| --- | --- |
| Green-test candidates with finite behavioral omissions | 0 |
| Retained original stale alphabetical expectations | 0 |
| Missing/invalid advisory artifacts | 0 |
| Unknown native token usage attempts | 0 |
| Unknown repository-test observations | 0 |
| Selected checks with invalid/unknown evidence | 0 |
| Repository-test failures | 0 |
| Selected check invocations | 16 |
| Independent finite probe invocations | 580 |
| NOT DEMONSTRATED combined advisory rows | 0 |

Bad-test detection covers the frozen stale expectation, not a semantic audit of
every newly authored test. Passing test observations remain limited evidence;
every combined package reports source-coverage completeness UNKNOWN.

| Additional mandatory action | Decision |
| --- | --- |
| Selected Proofline checks/feedback | KEEP optional; do not add a mandatory stage on this sample |
| Intentline planning/export | KEEP optional; added time/tokens require demonstrated benefit |
| Intentline → Proofline mapping | KEEP explicit opt-in; reject invalid artifacts without claiming complete coverage |
| Separate planner/reviewer/prover, repeated audits, adoption or mandatory correction | REMOVE mandatory proposal; not tested in this experiment |

Independent outcome differences and observed costs above determine these decisions.
No new product policy or installation requirement is introduced. Optional #15
correction remains outside the measured arms.

Reproduction and evidence: [protocol](../../matched_v5/protocol.json),
[original frozen source](frozen-source.zip), [manifest](manifest.json),
[native controls](controls.json), [qualification](qualification.json),
[approval](approval.json), [results](results.json), [resources](resources.json)
and [private raw evidence hashes](raw-evidence-hashes.json). Exact candidate
bytes/modes, source/prompt hashes, exported plans and bounded native observations
are retained per assignment. Artifact tests independently reconstruct Git trees.

The [v2 preparation](../../../docs/ISSUE16-PREPARATION.md),
[stopped v3](../matched-v3-20261013/README.md) and
[stopped v4](../matched-v4-20261013/README.md) retain their original missing slots,
failures, source archives and separate costs. None was resumed, silently repaired
or pooled into this separately approved cohort. There were 22 live coding
invocations across v3/v4/v5, while each study retains its own declared denominator.
Study authoring and initiating-agent costs remain unknown; controls and grading
are separated from episodes and their overlapping wall/process times are not added.
