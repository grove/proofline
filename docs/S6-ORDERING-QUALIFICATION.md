# S6 ordering-domain qualification: trust stop

12 October 2026. **Decision: redesign verification; S6 remains incomplete.**
The caller-supplied source predicates did not establish source coverage. Twelve
fresh Sol reviewer/prover judgments completed: three false acceptances and nine
correct product-defect rejections. The coordinator stopped on independent
adjudication; already-dispatched bounded workers finished. Forty judgments,
including every Luna judgment, and all six conditional recovery controls remain
unexecuted. No comparison was declared or dispatched. Do not resume this frozen
qualification under changed code or restart trials to seek favorable results.

This follows the [complete-timestamp experiment](S6-FULL-TIMESTAMP-QUALIFICATION.md),
[clarified-source trial](S6-AMBIGUITY-QUALIFICATION.md),
[UTC trial](S6-UTC-QUALIFICATION.md),
[source-contract calibration](S6-SOURCE-CONTRACTS.md),
[source-evidence experiment](S6-SOURCE-EVIDENCE.md),
[verification redesign](S6-VERIFICATION-REDESIGN.md),
[first follow-up](S6-FOLLOWUP.md) and [historical results](S6-RESULTS.md).
The earlier retained reports, transcripts and original predictions remain intact.
The original stopped comparison campaigns remain incomplete.

## Failure and independent adjudication

The original pagination promise requires descending score order and ascending
IDs for ties, with no score-type restriction. Both proposed positive controls
required score equality before ordering or ID tie-breaking. An independently
orderable library score can supply less-than comparison while equality raises
TypeError. Native Python sorting establishes its descending order; both candidates
reject those valid distinct scores. No ID tie comparison is needed in this case.

The alternative prover independently found a second defect: ordering equivalence
need not match operator equality. Its less-than-only equal-rank scores and
standard-library aware datetimes representing the same instant returned IDs in
the wrong order. Independent native readback reproduced both defects in both
preserved candidates. This prover FAIL is a correct product-defect rejection,
not a false rejection of a supposed positive control.

| Candidate | Reviewer | Prover | Independent classification |
| --- | --- | --- | --- |
| Preserved unary-negation pagination (0) | FAIL | FAIL | Correct rejections |
| Proposed comparator pagination (1) | PASS | PROVEN | Two false acceptances |
| Proposed insertion pagination (2) | PASS | FAIL | One false acceptance; one correct rejection |
| Exact-int pagination (3) | FAIL | FAIL | Correct rejections |
| Preserved username (4) | FAIL | FAIL | Correct rejections |
| Preserved UTC (5) | FAIL | FAIL | Correct rejections |

All twelve judgments are observed, with executable receipts and unchanged
candidate binding. None is an unavailable invocation. There are zero confirmed
false rejections, but no genuinely correct candidate received a judgment in this
run; it supplies no false-rejection rate or recovery qualification. All twelve
native boundary readbacks preserved denied oracle/other-role access, protected
writes, and denied network access. Isolation was never disabled.

The public predicates themselves used equality-capable score objects and equated
score ties with equality. The positive verifiers also used equality-capable
objects, then asserted full coverage. Sealed source predicates, passing finite
controls, independent model contexts and strict command citations did not remove
this shared domain assumption. The alternative prover's discriminating evidence
must be retained alongside the three false acceptances.

## Corrected earlier classifications

The pagination source, adapter and candidate implementation bytes match the
preceding UTC qualifications. A separate expanded readback therefore identifies
two false-acceptance judgments in source-contracts-v2 and four in
source-contracts-v3. Their narrower initial classifications remain preserved;
they are not qualified positive evidence. This is disclosed regression readback,
not six fresh efficacy observations. The existing historical campaign scores are
unchanged: its six pagination candidates already failed expanded source readback.
UTC clarification is prospective and does not change the pagination source.

## Repairs and retained evidence

The current comparator and insertion reference implementations use less-than
ordering in both directions and compare IDs only within ordering-equivalent
score groups. The public regression predicate now exercises less-than-only
scores, unavailable equality, ordering-equivalent ties, unavailable ID equality,
and incomparable IDs in distinct-score groups. It checks row identity and input
preservation without accidentally requiring score equality itself. Declaration
code retains the disproved pagination controls as negatives with their original
positive prediction history; repaired structures are separate proposed controls.
The independent library evaluator also exercises ordering-only score and ID
representations without changing any original expected result. No replacement
model qualification or comparison was declared.

Eight native reference/predicate repair probes matched: both retained defects fail and both repaired
structures pass independently adjudicated counterexamples and the repaired
public predicates. A further 152 native independent evaluator probes matched all four controls: the
retained candidates fail, and both repaired structures pass. These are
fixture/predicate/evaluator checks, not evidence that model verification works. Further domain gaps remain possible. The optional
source-evidence path remains experimental and disabled by default.

| Evidence | Manifest SHA-256 |
| --- | --- |
| source-contracts-v5 | `4223199fb842c5b5c12cccd4260c01bcbe8a1b57292b1472a507ff2f9a356b85` |
| ordering-only-readback-v1 | `fb215e9f3df3e298c200fa60d811e5fe6dcc9a033751aa670812dc06b5a12825` |
| ordering-tie-readback-v1 | `e033fba7297803408b5187a33677e0c08f15ddaf0cfcfbfebd478a79652dcf0f` |
| ordering-repair-controls-v1 | `d846fa83c4ce1f51c3904b91e48abb1ac779b794ae56dd728b483c6da9901a47` |
| ordering-adjudication-controls-v1 | `5c43d9dd2ce1fec187ab5e507daff075d37fc7a922c9766837e4cb505c5aec05` |

All live evidence is under ignored `.proofline/s6/`. The qualification retains
its manifest, runtime archive, source/brief originals, actual user clarification,
raw coordinator record before reconciliation, all native transcripts, strict
receipts, final 52-entry census, trust-stop record, boundary readback, deduplicated
ledger and evidence index. Earlier reclassification is separately recorded in
`ordering-only-readback-v1/earlier-qualification-readback.json`. Oracle execution
artifacts and raw transcripts remain inaccessible to task workers/verifiers.

## Measurements and limits

The v5 ledger charges all twelve native model dispatches: 2,866.000802 summed
stage seconds, 2,195,823 input tokens including 1,754,240 cached tokens, and
81,681 output tokens. Usage is known for every dispatch. Cached input is included
in input; reasoning output is not added a second time. Its 879 independent native
preflight process probes consumed 131.510589 summed seconds. Qualification wall
time was not retained through interruption and remains unknown.

The two independent ordering readbacks used four native process probes,
0.589650 summed seconds, and zero model calls. The separate repair controls used
eight probes, 1.293232 summed seconds, and zero model calls. They are outside the
qualification model ledger. The independent evaluator repair controls add 152
native probes, 21.813852 summed seconds and 22.012726 elapsed seconds, with zero
model dispatches. Earlier source-contracts-v3 retains its own twenty
calls, 4,780.230972 summed stage seconds, 3,902,066 input tokens including
3,236,736 cached tokens, and 137,579 output tokens. No calls are reused as new
judgments or omitted because they failed.

Final native validation: 185 tests, 183 passed, two Linux-specific skips,
150.316 seconds, with PROOFLINE_NATIVE_TESTS=1. Log:
`.proofline/s6/ordering-final-native-tests.log`. An earlier 184-test run omitted
that flag and skipped three additional native tests; its retained log is not the
final native validation. Thirty-three focused tests passed before the declaration
fixture update; the four source
profile/readiness checks passed again after it. Two additional independent
library/evaluator checks passed after the final grader update. Runtime remains macOS, Codex CLI
0.162.1 and Homebrew Python 3.14.8. Actual P2P controller inspection remains at
clean commit `a26e0a9c50a7d75fc3a02feda491bf497de94cf4`; no new P2P
controller delivery occurred.

There were zero task-worker human interventions and one study-level source
clarification. Study authoring/operator attention and initiating-agent tokens are
unknown. No authoritative prices were frozen, so dollars remain unknown. These
are verifier controls, not workflow deliveries: cost per independently correct
delivery, deliveries per workflow hour, cross-model efficacy, comparative elapsed
time and long-tail delivery behavior cannot be inferred. Terminal versus
recoverable false-rejection behavior was not exercised.

## Required next decision

Finite, caller-authored predicates and two model judgments remain insufficient to
qualify acceptance of unrestricted source domains. Repairing these fixtures does
not remedy that general failure. Do not promote the experimental machinery or
add another prompt-only retry. A future attempt needs a materially different,
source-coverage assurance mechanism with evidence that justifies its necessity
and scope. It must reject all preserved defects and accept independently correct
structural alternatives before the unchanged binding, isolation and bounded
recovery qualification can pass. Only then may a new immutable, matched campaign
include genuinely unfamiliar held-out tasks and realistic larger work.

The required four-way Sol comparison and separate matched Luna/Sol experiment
remain unrun. The existing trust stop takes precedence over completing those
experiments. The current decision is supported as a redesign decision; S6's
required qualification and comparisons are still incomplete.
