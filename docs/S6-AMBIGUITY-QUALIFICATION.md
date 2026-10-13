# S6 clarified UTC source and native qualification

12 October 2026. **Qualification stopped and failed; S6 remains incomplete.**
Twenty Sol judgments completed. Independent readback disproved both proposed UTC
positives; one fresh prover also found a genuine complete-timestamp defect. The
reviewer identified a material brief omission. No false acceptance or confirmed
false rejection occurred. Twenty-four judgments and six recovery controls remain
unexecuted. No new comparison was declared or dispatched.

This follows the [stopped replacement UTC qualification](S6-UTC-QUALIFICATION.md),
[ISO readback](S6-ISO-READBACK.md), [source-basis correction](S6-SOURCE-BASIS.md),
[source-contract calibration](S6-SOURCE-CONTRACTS.md),
[source-evidence experiment](S6-SOURCE-EVIDENCE.md), and
[verification redesign](S6-VERIFICATION-REDESIGN.md). The
[historical results](S6-RESULTS.md), [original follow-up](S6-FOLLOWUP.md),
prior declarations, original candidates and raw receipts remain unchanged.
Neither stopped comparison campaign is resumed.

## Source clarification and implementation

The final 2019 text makes expanded year widths agreement-dependent; its
six-digit examples do not establish a fixed width. Without an agreement a
compact string can identify different valid dates. The user adopted the proposed
rule: reject ambiguous strings with ValueError and accept unambiguous ISO forms.
No fixed width was supplied. The [2019 text reproduction](https://previewnorm.com/iso/ISO%208601%201%20WG-2019%20PDF.pdf)
supports the distinction in clauses 5.2.2.3 and 5.2.3.2. It also requires a positive
sign for a zero UTC offset (4.3.13). The
[2022 amendment](https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf)
supplies the previously documented fractional-unit and end-of-day corrections.

Both provisional UTC controls now enumerate valid date interpretations and
reject multiple distinct interpretations. Their different parsers and calendar
arithmetic remain; shared public metadata and formatting helpers limit their
independence. Public generated properties cover variable year widths, ambiguity
rejection, graphic signs and zero offsets. The original UTC source is retained
byte-for-byte as `original-source.md`; the new source adds the actual adopted
clarification. Earlier outcomes are not retrospectively scored under this context.
An artifact without that clarification remains input-not-ready.

The remedy remains optional `--source-evidence`, disabled by default. Full-source
model reasoning, source/baseline binding, sealed scripts, exact successful prover
command citations, native isolation and bounded recovery remain required. Passing
finite properties does not establish complete source coverage.

## Frozen native population

Declaration: `.proofline/s6/source-contracts-v3/manifest.json`, SHA-256
`c1b9b0a64b04165e7b5046ccecbaeec81e1acf1cafd11f5aa0f54f2db3b60688`.
Eleven candidates, five negative and six proposed positive, source context,
private acceptance expectations, runtime archives and public source predicates
were frozen before dispatch. All are exposed regression tasks.

The declared population is 44 reviewer/prover judgments using exactly
gpt-6.1-sol and gpt-6-luna, both high reasoning, then six conditional production
recovery controls. Concurrency is four; each model stage has 600 seconds; each
public predicate replay has 30 seconds. Recovery retains the prospectively
justified 2,400-second episode, 600-second stage, twelve-dispatch and 120-second
verification-reserve limits. The runtime is macOS, Codex CLI 0.162.1 and Homebrew
Python 3.14.8. Host execution initializes the nested sandbox; isolation stays on.

All eleven independent preflight controls matched and all source artifacts were
ready under the mechanical artifact checks. Those finite checks missed two
product defects and a brief omission. All sixteen pagination/username judgments
matched the independently confirmed outcomes. Both roles also rejected the former
UTC positive. On the new UTC control, the reviewer returned an observed NOT
VERIFIED for input readiness; the prover returned an observed FAIL for an actual
product mismatch. All twenty have unchanged bindings, finished bounded workers
and observed isolation canaries. No invocation was unavailable.

## Independently adjudicated new counterexample

The first reviewer identified an additional defect in preserved unary-negation
pagination: low Decimal precision rounds distinct scores into equal sort keys.
Separate native readback checked direct descending-score order under that context.
The preserved candidate fails; both corrected pagination controls pass. This is
an independently confirmed product defect, not missing proof evidence or a false
rejection. Its readback did not modify the frozen qualification's predicates.

Readback: `.proofline/s6/decimal-order-readback-v1/manifest.json`, SHA-256
`76a712ff57a9bfde4fe0ec6b3b05fa950a6a5fceeb3e1efe293556f50267a9f9`.
Three native process probes, 0.419380 summed process seconds, 0.432288 elapsed
seconds and zero model dispatches. Inputs stayed unchanged. This diagnostic has
no independently correct delivery denominator.

The UTC reviewer also found acceptance of offset minute `60`. A separate native
library check confirmed acceptance in the retained parser and rejection in both
corrected UTC controls; the controls also passed CLI rejection checks. This
supports an actual malformed-input defect under the original source, independently
of the new year-width clarification. Readback:
`.proofline/s6/utc-offset-minute-readback-v1/manifest.json`, SHA-256
`9ce93cbda59ee294bbb2beb5f9a65de156dd5f9ea26227caa15d2be8ff2b7c33`.
Three native process probes, 0.541187 summed process seconds, 0.554289 elapsed
seconds and zero model dispatches; inputs remained unchanged. Outer probe time
includes its nested CLI checks.

## New UTC defects and the external stop

The prover found that the control rejected ambiguity before validating the
whole timestamp. An expanded compact calendar date and a different ordinal date
can both parse as dates, while the actual announced leap-second time makes only
the calendar interpretation valid. Both controls incorrectly rejected that
unambiguous complete string. Independent native readback confirmed the mismatch:
`.proofline/s6/complete-timestamp-readback-v1/manifest.json`, SHA-256
`8da1ccb8b7eb4691148a766d8721800b66ddc54ec8fa924b4f0a5644c7bb0615`.
Two native probes, 0.285532 summed process seconds, 0.293763 elapsed seconds,
zero model dispatches. The FAIL is a correct rejection of a defective proposed
positive, not a false rejection.

Separate source-grounded readback found that both controls converted decimal
clock units with a fixed nominal duration, even when a leap second modifies that
unit. The expected instant was derived from the clock-unit definitions and the
actual IERS insertion; the standard does not supply that worked example.
Both returned second 59 where the derived instant lies in second 60. Readback:
`.proofline/s6/leap-unit-readback-v1/manifest.json`, SHA-256
`8573d69fb292d5c0fa81de6ac153fdd92f618afadbc30b559194a49ec57b7733`.
Two native probes, 0.282663 summed process seconds, 0.290043 elapsed seconds,
zero model dispatches. This additional interaction was absent from the frozen
predicates; their finite pass could not establish source coverage.

The adopted clarification was added to source.md but omitted from the indexed
R1 brief row. The reviewer correctly treated that material omission as INPUT
NOT READY. This is an observed readiness judgment, separate from a product
rejection, missing executable evidence or an unavailable invocation.

The coordinator received SIGINT before another batch. Four active bounded workers
finished normally. The interrupted RUNNING record and transcript are retained;
external finalization reconciled all twenty receipts and recorded TRUST
QUALIFICATION FAILED. Original predictions remain preserved. Independent
adjudication marks the proposed UTC controls defective without rewriting their
initial positive predictions. Neither received PASS or PROVEN.

## Resource accounting and decision

The deduplicated ledger contains twenty native model dispatches, all Sol high:
4,780.230972 summed native stage seconds; 3,902,066 input tokens, including
3,236,736 cached input; 137,579 output tokens; zero unknown usage dispatches.
There were 569 independent native process probes, 79.107668 summed process
seconds. Exact qualification wall time was not retained after interruption and
remains unknown. Cached input is included in input; output is counted once.

The four separate counterexample readbacks add ten native outer probes and
1.528762 summed process seconds, with zero model dispatches. Their nested CLI
work is included in their outer elapsed time. Authoring/operator attention,
initiating-agent usage and dollars remain unknown. There is no delivery
denominator for cost per correct delivery or deliveries per workflow hour.

Decision: repair the demonstrably defective calibration controls and brief
assembly, retain this failed qualification, and require a new immutable native
qualification before comparisons. This run does not establish model false
acceptance; it demonstrates useful rejection and readiness behavior on exposed
controls. It also demonstrates that passing caller-authored finite predicates
does not establish complete source coverage. The remedy remains unqualified.

Ledger, boundary readback, runtime archives and evidence hashes are retained under
`.proofline/s6/source-contracts-v3/operator/`. The failed declaration is single-use
and will not be resumed under the repaired code. The two newly defective controls
remain unchanged for negative-control use.

## Validation and limits

The complete native suite ran 181 tests: 179 passed, two Linux-specific platform
skips, 142.453 seconds. Log: `.proofline/s6/utc-ambiguity-native-tests-v2.log`.
The earlier invocation with no test-directory argument ran zero tests and is
retained separately; it is not validation evidence. The six focused source/UTC
tests also passed. Mock checks establish mechanics, not native judgment quality.

The actual P2P checkout remains clean at
`a26e0a9c50a7d75fc3a02feda491bf497de94cf4`; its current controller was inspected.
No new P2P delivery or comparison is inferred from that inspection. Pricing,
initiating-agent cost and study-level operator attention remain unknown. The
source clarification is one study-level user contribution; worker intervention
counts do not erase that contribution or implementation/authoring work.

Subsequent control repairs decide ambiguity on complete timestamp validity and
use leap-modified clock-unit duration. Brief assembly retains original source and
brief bytes and indexes the actual clarification in R1. The independent library
adjudicator now enforces ValueError on the specific clarified cases while keeping
other original named error channels. Thirteen focused checks pass; this is
mechanical/control validation, not another native model outcome.

Required comparisons remain gated on complete fresh qualification. Any false
acceptance stops further dispatch; a stopped campaign remains incomplete.
