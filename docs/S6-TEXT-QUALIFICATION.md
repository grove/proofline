# S6 text-domain follow-up

13 October 2026. **Decision: redesign verification; S6 remains incomplete.**
The [representation qualification](S6-REPRESENTATION-QUALIFICATION.md) failed its
native trust gate. No comparison ran, and no model experiment ran after the stop.
This report supplements the [ordering findings](S6-ORDERING-QUALIFICATION.md),
[original follow-up](S6-FOLLOWUP.md) and [historical report](S6-RESULTS.md).
Those reports and every original trial remain retained.

## Native result and diagnosis

The immutable representation qualification declared fifteen controls, sixty
reviewer/prover judgments and six conditional recovery controls. Its manifest
SHA-256 is `012b8f18bfa506057ec767a08f469850ee215fa88ef975de219e879f84f3c3c2`.
Both models were frozen at reasoning high: gpt-6.1-sol and gpt-6-luna. All fifteen
finite preflight predictions matched, and all evidence artifacts were ready.
These checks missed a shared assumption about the public text domain.

Sixteen Sol judgments executed. Twelve correctly rejected preserved defective
implementations, including both previously certified pagination controls whose
score ordering unnecessarily required equality. Each of the two proposed username
positives then received PASS and PROVEN: four false-acceptance judgments.
Forty-four judgments and all six recovery controls remain unexecuted. Luna had
zero dispatches. There were no unavailable invocations in the executed population,
and no confirmed false rejection. Rejection of a defective proposed positive is
not a false rejection.

The username source accepts nonblank strings unchanged through the public library.
One implementation calls the input's `strip` method; the other iterates the input.
Native witnesses use `str` subclasses with the underlying text `alpha` but an
unavailable instance `strip` or iterator. Unbound base-string operations and JSON
serialization independently establish the text. The original seed accepts both
unchanged; the proposed controls raise TypeError. This is an unauthorized domain
restriction, not an additional feature request or a missing executable receipt.
Witnesses and original-seed readback are retained in
`.proofline/s6/text-protocol-readback-v1/` and `text-baseline-readback-v1/`.

The coordinator stopped before another batch and let its four active bounded
workers finish. The raw interrupted coordinator report and complete final census
remain separate. All sixteen bindings, unchanged-input checks and isolation
canaries passed. Candidate/source writes, oracle and other-role reads, network
access and permission changes remained denied. Integrity and valid citations
therefore did not establish source coverage. The stopped runtime is archived;
it must never resume under changed code.

Separate byte-identity readback establishes four earlier username false-acceptance
judgments in source-contracts-v3. Together with the previously disclosed four
pagination judgments, all eight of that trial's positive judgments are now known
to concern defective candidates. Original labels remain preserved, with the new
adjudication recorded separately. Historical task-level acceptance counts do not
change: all six historical username candidates were already independently defective.

Post-stop UTC readback also found instance `count` narrowing in both unexecuted
proposed UTC positives. A string subclass containing an ordinary valid timestamp
disables `count`; the original seed accepts it. Neither candidate received a model
judgment in this run. They are defective controls, not false acceptances or false
rejections. Native evidence is in `.proofline/s6/utc-text-readback-v1/`.

## Repair and validation

The source-declared representation compiler now includes text representations
that remove optional instance methods or iteration, alongside its existing minimal
ordering representations. It compares normalized returned values or named error
families, and checks input preservation. Source authors must justify each relation;
the compiler has no task names, private answer keys or evaluator input access.
Independent output invariants remain necessary because an incorrect baseline can
be representation-invariant. This finite machinery cannot establish complete
coverage, and no new assurance stage or relaxed acceptance rule was added.

Username references now use unbound base-string operations while returning the
original accepted object. Both UTC structures extract the underlying base string
before parsing. The independent library grader adds separately written text
subclass probes. The default UTC positive fixture now uses the repaired full parser
and includes an actual leap-second control. Original requests and archived programs
remain unchanged; the user's expanded-year clarification applies only where it is
explicitly recorded. Leap-unit fractional conversion remains a documented source
inference, not a quoted standard example or a claim of formally complete correctness.

Eight native public-predicate repair controls matched: four retained defects fail
and four repaired structures pass. Independent library adjudication also matched
all eight, across 272 native process probes, 35.682634 summed process seconds and
36.092693 elapsed seconds. Its frozen manifest SHA-256 is
`76a3ad1d451523420420a558e176e3c9e96957427b0fb3a35b20887301107be0`.
Artifacts are in `.proofline/s6/text-repair-controls-v1/` and
`text-adjudication-controls-v1/`. These experiments dispatched zero models and
cannot qualify the repaired production remedy.

An intermediate full suite ran 189 tests with one failure and two platform skips:
the ordinal-date readback fixture retained a wrapper dependent on an import from
the former UTC reference. The new parser already handles ordinal dates. Removing
the obsolete wrapper preserves the independently authored expected timestamp and
passes its focused check. The failed log is retained as
`.proofline/s6/text-default-final-native-tests.log`; the final native rerun has a
separate log. Earlier successful suites remain retained rather than substituted
for a final-state check.

The final suite ran 189 tests: 187 passed and two Linux-specific checks skipped,
with PROOFLINE_NATIVE_TESTS=1. Log:
`.proofline/s6/text-default-final-native-tests-v2.log`. All 47 default native
evaluator controls matched. Focused relation, reference and grader tests, Python
compilation, local documentation links and `git diff --check` also passed.

Preservation readback verified 1,103 files against the closed qualification index
and all nineteen archived runtime hashes. Post-stop adjudication has a supplemental
index; the original index was not rewritten. The stopped followup-v2 manifest
still hashes to `ca7cafad63071bf3f470cc89e2f7210262fcd0652a8489c52da574fb0ffc517b`.
The historical report, first follow-up and initial redesign report have no changes.
Transcripts, private probes and draft tasks remain ignored and unavailable to
workers/verifiers. No push, PR, merge, deployment or remote mutation occurred.

## Resources and remaining work

This failed qualification charges all sixteen calls: 3,936.971521 summed native
stage seconds; 2,734,379 input tokens including 2,153,472 cached; 99,897 output;
zero unknown-usage calls. The full run includes 1,017 native process probes and
152.057069 summed process seconds. Exact run wall time is unknown. Worker-specific
human intervention was zero; study-level authoring, adjudication and operator
attention were not measured and are unknown. The inherited owner clarification
is explicitly retained, not counted as zero study intervention.

Observed native model stages ranged from 175.088284 to 343.058293 seconds, with
zero stage timeouts. These are verifier-control durations, not complete workflow
deliveries or matched comparative long-tail measurements. Remaining stages and
recovery episodes provide no observations.

The deduplicated `.proofline/s6/redesign-ledger-v2/` combines the original follow-up
ledger and closed redesign trials: 158 distinct model dispatches, 30,989.131843
known summed stage seconds, 28,521,595 input tokens including 23,500,544 cached,
1,087,934 output tokens, and six calls with unknown usage. Initial pilot resources
remain separate. Test-provider aggregate usage and initiating-agent costs remain
unknown. Cached input is already included; reasoning output is not charged twice.
Pricing, dollars, cost per independently correct delivery and comparative throughput
remain unknown. Verification controls do not provide workflow-delivery denominators.

Eight unfamiliar component/service requests have been drafted privately with zero
model dispatches. They are not a campaign declaration, frozen acceptance population
or qualified workload; service interfaces still require precise independent
criteria and controls. The previous 4/144 stopped campaign remains incomplete,
with 140 assignments unexecuted, and followup-v1 remains declared but undispatched.

The repaired controls have no new model qualification. A future materially justified
verification design must pass the entire frozen two-model gate, including correct
structural alternatives, evidence/unavailability distinctions, binding, isolation
and bounded production recovery, before any fresh comparison declaration. Required
four-way Sol and matched Luna/Sol experiments, actual P2P delivery comparison,
long-tail reliability and comparative cost findings remain unexecuted. This failed
gate cannot support superiority or an S6 completion claim. The evidence supports
continued redesign and retention of the trust stop; it does not yet complete S6.
