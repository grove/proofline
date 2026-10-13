# S6 source contracts: native calibration stop

12 October 2026. **S6 remains incomplete; the trust gate did not pass.** The
explicit source-contract path is implemented and its mechanics tested. Native
calibration found another defective positive reference before model dispatch.
There is no completed comparison or new model-quality result.

This follows the [interface-repair report](S6-SOURCE-EVIDENCE.md),
[candidate-blind redesign](S6-VERIFICATION-REDESIGN.md),
[original follow-up](S6-FOLLOWUP.md), and [historical results](S6-RESULTS.md).
Those reports and their retained trials remain unchanged, including early
misclassifications. The historical and stopped follow-up campaigns are not resumed.

## Change and scope

Repeated source-domain false certifications survived general prompt guidance.
Candidate-blind evidence authoring then produced no usable designs in either
retained qualification. This experiment moves explicit interface facts, domains
and executable invariants into an optional caller-supplied artifact. It does not
add another model author, acceptance authority, or narrower task promise.

`deliver --source-evidence FILE` binds `source-evidence-v1` to the original source
hash and captured baseline Git tree. Each indexed criterion needs an exact source
quotation, domains, invariants and executable Python evidence. Unresolved source
obligations stop delivery as INPUT NOT READY before model dispatch. The existing
implementer, reviewer and prover stages remain responsible for the full source;
the supplied interpretations are explicitly fallible. Positive proof requires
successful, exact native command receipts for all sealed probes. Missing receipts
remain missing evidence, and unavailable invocations remain unavailable.

The artifact and probe bytes are protected outside the product, included in
binding and readback, and retained through bounded correction and unchanged-code
evidence recovery. No private grader answers, candidate implementation, or raw
trial transcripts are copied into the artifact. There is no automatic compiler
from natural-language promises to correct predicates: source provenance and
syntax validation cannot establish semantic adequacy.

Exposed feasibility profiles exercise pagination ordering and preservation
properties across numeric, string, Decimal and custom comparable scores,
conditional ID comparison, nonboolean integer subclasses and malformed rows;
username identity/rejection across Unicode code points and White_Space pairs;
and CLI/interface preservation. Interval properties exist for conditional
recovery. Finite properties supplement independent reasoning and isolation; they
do not restrict the promised domain to sampled values. Foreign-import syntax and
file readback are supplementary observations, not exhaustive effect proofs.

The predicates were authored from source and public domain definitions, separately
from the private grader. Their operator authoring and adjudication cost is unknown,
not zero. Supplying such artifacts to Proofline alone would privilege its comparison
arm: any future shared-preplanned comparison must expose the same authorized public
information to all arms and count its preparation; raw-request preparation also
counts. This experiment establishes neither scalable contract preparation nor
trustworthy automatic certification.

## Frozen qualification and native findings

New single-use declaration: `.proofline/s6/source-contracts-v1/manifest.json`.
SHA-256:
`860488628b25b0d9fcf1de673f208316c313308074c0829507b0de5b3fbdbe51`.
Sources, nine preserved candidates, private acceptance expectations, runtime
archives, source predicates and conditional population were frozen before
execution. Models remained exactly gpt-6.1-sol and gpt-6-luna, both high reasoning.
The conditional population was 36 fresh reviewer/prover judgments and six
production recovery episodes. Limits were four concurrent judgments, 600 seconds
per model stage and 30 seconds per native predicate. Recovery retained 2,400
episode seconds, 600-second stages, twelve dispatches and the existing 120-second
verification reserve, justified prospectively against the prior 1,635.4-second
recovery observation. All tasks here are exposed regressions.

Native calibration ran with Codex CLI 0.162.1 and Homebrew Python 3.14.8 on macOS,
using the existing nested sandbox with read-only candidate inputs and network
denied. All nine private evaluator controls matched their earlier finite
expectations. The 27 source-invariant executions produced 21 passes and six
failures, with no unavailable observation or timeout:

| Controls | Native source-invariant result |
| --- | --- |
| Two corrected pagination implementations | All three criteria passed on each, including the structural alternative |
| Two corrected username implementations | All three criteria passed on each, including the structural alternative |
| Four preserved defective candidates | At least one invariant failed on each |
| Formerly positive UTC reference | Leap-second identity failed; CLI and supplementary constraint checks passed |

The source-grounded new counterexample is `2016-12-31T23:59:60Z`. It denotes a
real UTC instant: [IERS Bulletin C 52](https://datacenter.iers.org/data/16/bulletinc-052.txt)
records that sequence at the end of 2016. The
[NASA ISO time overview](https://science.data.nasa.gov/fits/documentation/iso-time)
includes second 60 during a leap second. An already-UTC input should retain its
instant in the source-requested `YYYY-MM-DDTHH:MM:SSZ` representation. The preserved
reference instead raises `ValueError: second must be in 0..59, not 60` through
`datetime.fromisoformat`. [Python's datetime documentation](https://docs.python.org/3.14/library/datetime.html)
states that its time model has no leap seconds. The independently adjudicated
classification is a product defect in the reference, not an unsupported probe
expectation and not a model false rejection.

The available ISO overview is not a complete parsing specification. Both UTC
contracts therefore explicitly retain an unresolved full-grammar and leap-second
obligation. Seven contracts passed structural/readiness validation; two did not.
No Python-parser subset, patched finite example or narrower promise was substituted
to make calibration pass. The formerly positive UTC fixture remains byte-preserved;
the old finite evaluator result remains visible beside the new contradictory
source readback. Its earlier passing controls cannot establish full correctness.

Final status: **TRUST QUALIFICATION FAILED**, with frozen runtime and all fixture
hashes intact. The declaration took 39.046 seconds wall time; 223 deduplicated
native process probes, including private evaluator controls and the 27 invariant
executions, totaled 35.022 known process seconds. These are sandboxed process
probes, not model dispatches. Zero provider model calls were made, so dispatched
model input/output tokens are zero for this qualification. Initiating-agent costs,
operator attention, artifact preparation and dollars remain unknown.

All 36 product judgments and six conditional production recovery episodes were
unexecuted. No new comparison campaign was declared or dispatched. There are no
observed new verifier false acceptances/rejections, terminal or recoverable false
rejection rates, natural delivery reliability rates, workflow-hour rates, or cost
per correct delivery to infer from this calibration-only population.

## Validation, decision and limits

Focused delivery mechanics tests cover source/baseline mismatch, unresolved
obligations, malformed predicates, missing criteria, immutable artifact drift,
unchanged-code evidence recovery and the unchanged three-stage path. Gate tests
check that a source-readiness gap dispatches neither models nor recovery. These
tests validate controller mechanics, not native model judgment quality.

The complete native regression suite ran 176 tests: 174 passed and two
Linux-specific platform tests were skipped, in 145.099 seconds. The 15 focused
delivery/probe tests and two source-profile/gate tests passed separately. Native
logs are `.proofline/s6/source-contract-native-tests.log`,
`source-contract-mechanics-v2.log` and `source-contract-gate-tests.log`. No
runtime/source changes were made after the qualification declaration; documentation
updates do not requalify any earlier campaign.

The decision remains **redesign**, with automatic full-source certification
unqualified. The source-contract path stays optional and disabled by default.
Before another native qualification, independently establish a complete applicable
ISO interpretation and genuinely correct, structurally different UTC controls;
resolve representation/conversion obligations without narrowing the source.
Retain this failed calibration and every earlier trial. Do not resume it under
changed code or treat fixing one leap-second example as complete ISO coverage.
Only passing native negative/positive judgment, binding, isolation and production
recovery gates can unlock the required new immutable matched comparisons.

Retained evidence includes the frozen manifest and runtime archive, `report.json`,
`native.log`, `operator/probe-controls/`, independent oracle execution receipts,
the qualification ledger and evidence index. These remain ignored operator
artifacts, outside worker/verifier inputs. Historical results, follow-up declarations,
resource ledgers and failure classifications are preserved.
