# S6 replacement UTC controls and stopped native qualification

12 October 2026. **S6 remains incomplete.** The new qualification stopped after
four fresh Sol judgments because independent native readback disproved both
proposed UTC positive controls. The character omission is repaired and checked;
the source interpretation still has an unresolved assumption. No new comparison
was declared or dispatched. A stopped qualification is not a completed comparison.

This follows the [ISO readback](S6-ISO-READBACK.md),
[source-basis correction](S6-SOURCE-BASIS.md),
[source-contract calibration](S6-SOURCE-CONTRACTS.md),
[interface experiment](S6-SOURCE-EVIDENCE.md), and
[candidate-blind redesign](S6-VERIFICATION-REDESIGN.md). The
[historical results](S6-RESULTS.md), [original follow-up](S6-FOLLOWUP.md),
early misclassifications, original accepted candidates and receipts remain
unchanged. Neither stopped comparison campaign is resumed.

## Implementation and independent checks

The optional source-evidence path retains the existing three production stages,
source/baseline binding, sealed predicates, exact successful proof-command
receipts, isolation and bounded recovery. It remains disabled by default and
unqualified. Executable predicates supplement the verifiers' full-source work;
they neither replace the promise nor establish semantic completeness.

Two provisional UTC controls replace the defective Python-parser references for
calibration. One uses regular-expression parsing and integer Gregorian calendar
arithmetic. The other uses a manual scanner, exact fractions and a mapped
400-year calendar cycle through Python date operations. They share public leap
metadata and year-formatting helpers, so their independence is partial, not two
independent formal proofs. They cover calendar/ordinal/week dates, basic/extended
forms, fractional hours/minutes/seconds, non-hour offsets, leap seconds, midnight
rollover and year padding/expansion. Calendar arithmetic was checked against an
independent full Gregorian cycle; generated representation/offset properties
exercise both implementations without importing private grader answers.

Public leap metadata is frozen through
[IERS Bulletin C 72](https://hpiers.obspm.fr/iers/bul/bulc/bulletinc.dat), with
[Leap_Second.dat](https://hpiers.obspm.fr/iers/bul/bulc/Leap_Second.dat)
effective dates. It is time-dependent context, not a permanent rule for future
announcements. Decimal-unit and midnight interpretations use the published
[2022 amendment](https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf).
Possession of a full standard PDF is not a prerequisite for independently
supported interpretations.

The formerly positive UTC reference stays byte-preserved and is declared a
negative in this experiment, following the earlier independently established
leap-second and fractional-unit defects. This reclassification does not rewrite
its prior finite passing controls or turn legitimate negative judgments into
false rejections.

## Frozen population and actual native observations

Declaration: `.proofline/s6/source-contracts-v2/manifest.json`, SHA-256
`0484fffd91994fe57897ddc7589c6e6cd8a80942328d81cf1574ccd81d06e16d`.
Sources, eleven controls, public source properties, private expectations and
runtime archives were frozen before execution. All tasks are exposed regressions.
The population was 44 reviewer/prover judgments using exactly gpt-6.1-sol and
gpt-6-luna, both high reasoning, followed conditionally by six production recovery
episodes. Limits were four concurrent judgments, 600 seconds per model stage
and 30 seconds per property execution. Recovery budgets were prospectively
frozen at 2,400 episode seconds, 600-second stages, twelve dispatches and the
existing 120-second verification reserve, justified against the prior
1,635.4-second recovery observation.

Native execution used macOS, Codex CLI 0.162.1 and Homebrew Python 3.14.8 with
the existing nested sandbox. No isolation control was disabled. All eleven
finite private controls matched their frozen predictions; all source-property
replays matched, including failure on the five declared negatives and passing
on the six proposed positives. Those finite results proved insufficient.

| Completed fresh judgment | Result | Native stage seconds |
| --- | --- | ---: |
| Sol reviewer, preserved defective pagination | FAIL | 227.337 |
| Sol prover, preserved defective pagination | FAIL | 263.258 |
| Sol reviewer, corrected pagination control | PASS | 176.031 |
| Sol prover, corrected pagination control | PROVEN | 327.721 |

All four judgments have valid observed receipts and unchanged candidate inputs.
All four isolation canaries passed. The negative judgments identify actual
source-domain defects, including unary-negation narrowing and exact-type paging
checks; they are correct rejections. The positive control passed independent
native readback for this exposed task. These observations are judgments on
preserved candidates, not four new deliveries or workflow reliability samples.
No new false acceptance, false rejection, missing-evidence outcome or unavailable
invocation occurred in this completed subset.

## External counterexample and trust stop

Independent character readback was frozen separately at
`.proofline/s6/utc-character-readback-v1/manifest.json`. Both UTC controls reject
`2024-02-29T23:30:00−01:00`, where the offset sign is U+2212 MINUS SIGN, and its
basic-format equivalent. The expected UTC instant is
`2024-03-01T00:30:00Z`: subtracting a negative one-hour offset adds one hour and
crosses leap day. The original Unicode JSON library interface supplies this
string without an ASCII-only restriction.

The published [ISO 8601-1:2019 excerpt, clause 3.2.1](https://standards.iteh.ai/catalog/standards/iso/b42c90ed-008a-40be-b79a-27e15c0de2dc/iso-8601-1-2019)
distinguishes graphic minus/hyphen symbols from their ASCII hyphen-minus mapping.
The [Library of Congress working draft](https://www.loc.gov/standards/datetime/iso-tc154-wg5_n0038_iso_wd_8601-1_2016-02-16.pdf)
corroborates that distinction and labels encoding outside its scope; it is draft
context, not the final standard. Both native CLI and public-library observations
reproduced the rejection with inputs unchanged. This is a defective proposed
positive control, not missing executable evidence or a model false rejection.

The coordinator received an interrupt before another batch. Its four active
bounded workers finished normally; their process records were reconciled before
finalizing the retained report. The original interrupted coordinator report and
traceback remain preserved beside the externally finalized report. Status is
**TRUST QUALIFICATION FAILED**, with an external trust stop and no observed
model false acceptance. Forty judgments, including every Luna judgment and both
UTC controls' judgments, and all six recovery episodes remain unexecuted. No
qualification or comparison is resumed under changed code.

## Repair readback, readiness and validation

Both parser controls now recognize Unicode minus signs in year/offset positions
and Unicode hyphens in date separators. They preserve the distinction between
those symbols rather than indiscriminately replacing every sign. Tests also
check rejection of misplaced symbols. The public source properties include
graphic-symbol equivalence.

The subsequent native readback at `.proofline/s6/utc-character-repair-v1/`
passed both implementations against the retained finite corpus, new character
cases and all six source-property executions. Manifest SHA-256 is
`c1131a5880eba16aaaa5019ece5e0c405860c3dd06d3e15832dd720edfdb0302`.
No model calls ran in this repair readback. The qualification's frozen copies
remain defective and untouched; this repair does not requalify that declaration.

The controls still assume six year digits for expanded basic dates. The original
scalar-string request supplies no year-width agreement; the working draft
explicitly describes such expansion as requiring interchange agreement. This
is an unresolved interpretation, not an established additional product defect
or grounds to score an unrun verifier. The UTC source artifacts now record it
and fail readiness before implementation. An ASCII-only domain or a six-digit
agreement is not silently substituted for the original promise. Additional
unsupported assumptions must remain gaps rather than positive qualifications.

The actual production CLI was exercised separately at
`.proofline/s6/utc-readiness-control-v1/`: it returned **INPUT NOT READY** for
that unresolved artifact in 0.661 seconds, with zero model dispatches and zero
stages. This is a source-readiness refusal, not a product rejection, missing
proof receipt, or unavailable model invocation.

Before qualification, the native regression suite ran 181 tests: 179 passed,
two Linux-specific platform skips, in 142.503 seconds. After the repair, eleven
focused reference/readiness/delivery tests passed. The final native suite ran
181 tests: 179 passed and two Linux-specific platform skips, in 144.977 seconds,
recorded in `.proofline/s6/utc-character-remedy-native-tests.log`. Mock
handoff/recovery tests check mechanics; this stopped experiment establishes no
new native recovery result.

## Resource accounting and decision

The retained deduplicated model ledger records four native dispatches, 994.347
known summed native stage seconds, 714,577 input tokens including 580,352 cached
input tokens, and 30,324 output tokens. All four usage records are available.
Cached input is already part of input; reasoning output is not charged twice.
The interrupted coordinator did not retain exact end-to-end qualification wall
time, so it remains unknown rather than equated with summed concurrent stages.

Qualification controls used 353 deduplicated native process probes totaling
50.702 known process seconds. The external character readback used sixteen
probes, 2.117 summed process seconds and 2.353 wall seconds. Repair readback used
118 probes, 16.229 summed process seconds and 16.433 wall seconds. These are
process probes, not additional model dispatches. Native regression tests and
operator/initiating-agent work are separate from this dispatch ledger.

Task workers recorded zero task-specific human interventions. Study-level source
authoring, external stopping, adjudication and operator attention occurred but
were not measured prospectively; their cost remains unknown. Initiating-agent
tokens/cost and dollars also remain unknown. No prices were frozen. There is no
defensible cost per correct delivery, correct deliveries per workflow hour,
reliability rate, terminal/recoverable false-rejection rate, long-tail comparison
or superiority claim from this partial qualification.

The decision remains **redesign**. The source-evidence machinery preserves
receipts and boundaries and can refuse unresolved inputs, but trust qualification
is incomplete. Neither full-domain contract preparation nor reliable model
acceptance has been established. No new campaign is declared until genuinely
qualified controls, both models' required judgments and production recovery
pass; the complete matched Sol comparison and Luna/Sol experiment remain owed.

Retained private evidence includes manifests, archives, frozen candidates,
independent native execution receipts, raw model transcripts, completed and
unexecuted judgments, the external stop record, worker reconciliation, ledgers,
boundary readback and evidence indices. Raw/oracle artifacts remain ignored and
outside worker/verifier access. Historical reports and campaign populations are
preserved with their original outcomes and limits.
