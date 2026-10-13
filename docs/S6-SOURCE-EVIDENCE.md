# S6 source-evidence qualification — interface repair

12 October 2026. **Decision: do not promote the candidate-blind stage; stop pursuing this design as the production verification remedy. The new native qualification failed. S6 remains incomplete.**

This follows the preserved [first follow-up](S6-FOLLOWUP.md), [candidate-blind redesign](S6-VERIFICATION-REDESIGN.md), [historical results](S6-RESULTS.md), and [pilot protocol](S6-PILOT.md). Those reports remain unchanged. This is verification qualification, not an efficacy comparison.

## Implemented repair

The new experiment supplies the exact original public `app.py` adapter as execution context, after checking that its bytes match every preserved candidate and reference. It makes the JSON-to-`process(data)` and return-value-to-JSON mapping explicit without exposing product algorithms, tests, private inputs or expected results. Production callers already supply this context through the existing execution map; no task-specific payload rule was added to the controller. A protocol clarification keeps nonblocking observations out of the author’s blocking findings array, preserving the existing strict handoff rule.

Qualification now privately replays unchanged model-authored probes before verifier dispatch. Every criterion must pass all independently adjudicated positive controls, including structural alternatives; at least one probe must fail on each preserved defective control. Unavailable executions, input mutation, incorrect expectations and insufficient discrimination keep the gate closed. These finite controls test the evidence apparatus; they do not establish universal source coverage or become worker-visible requirements. No failed probe is edited or retried to obtain a pass.

Read-only fixture Git operations now disable optional index writes. Native judgments run in bounded batches, with no subsequent batch after an observed positive judgment on an independently defective candidate. The existing production recovery driver accepts the experimental source stage and its interface context. Conditional native recovery controls retain product correction, unchanged-code evidence recovery and structural alternative checks, cumulative budgets and drift rejection.

## Frozen declaration

`.proofline/s6/source-challenges-v3/manifest.json`, SHA-256:

`196b049b45c8bdf1995fb0eae048612cecf78272af768cf522a8c69c23d576c0`

Before dispatch, the declaration froze archived runtime code, original source and brief bytes, adapter/context, candidate snapshots/history, independent controls, exact `gpt-6.1-sol` and `gpt-6-luna` models with reasoning `high`, concurrency four, 600 seconds per model stage and 30 seconds per native probe. Runtime: macOS, Codex CLI 0.162.1, Homebrew Python 3.14.8. The actual P2P checkout remains at `a26e0a9c50a7d75fc3a02feda491bf497de94cf4`; no new P2P delivery or modification occurred.

Nine native controls were declared: four preserved defective candidates (string-score pagination, integer-subclass paging, Unicode whitespace and UTC), two corrected pagination structures, two corrected Unicode structures and the corrected UTC reference. All nine matched the frozen independent evaluator before model dispatch. They remain finite controls, not a guarantee that the references satisfy every possible interpretation of the source. New counterexamples require independent adjudication.

The conditional population is six candidate-blind authors, 36 reviewer/prover judgments and six production recovery episodes. Recovery uses interval union, both models, 2,400 episode seconds, 600-second stage allowances, twelve dispatches and the existing 120-second verification reserve. These equal limits were justified before outcomes: the earlier third-implementation diagnostic consumed 1,635.4 seconds, and the added source author can consume another 600 seconds. No previous campaign resumed.

## Checks

The native regression suite ran **169 tests: 167 passed, two Linux-specific skips**, in 145.188 seconds. The final focused qualification checks passed **3/3** after an additional initialization-failure guard. They exercise real Python probes to distinguish wrong expectations, nondiscrimination, unavailable native execution and input mutation, and verify that Git inspection preserves frozen index bytes. The earlier combined focused run passed **10/10**, retained in tool output. Native-suite and final focused logs remain under `.proofline/s6/source-interface-*.log`. These mechanics checks do not establish model judgment quality.

## Native outcomes and adjudication

| Model | Author task | Observed outcome | Native seconds |
|---|---|---|---:|
| Sol/high | pagination | unavailable: timeout | 600.0 |
| Sol/high | Unicode usernames | NOT VERIFIED: payload/result semantics and coverage gaps | 414.2 |
| Sol/high | UTC timestamps | unavailable: timeout | 600.0 |
| Luna/high | pagination | NOT VERIFIED: numeric-only domain and effect-coverage gaps | 71.8 |
| Luna/high | Unicode usernames | NOT VERIFIED: payload/result semantics and coverage gaps | 67.2 |
| Luna/high | UTC timestamps | NOT VERIFIED: payload/result semantics, ISO scope and effect-coverage gaps | 101.7 |

**Zero usable designs.** Consequently, all eighteen model/candidate probe-control groups were unexecuted, all **36 reviewer/prover judgments were unexecuted**, and all **six production recovery episodes were unexecuted**. No author was retried, no probe was rewritten, and no positive verdict was obtained by changing source obligations. The new preflight’s mechanics are tested; its model-authored native evidence path remains unqualified because the prerequisite never passed.

The supplied adapter was present in the prompts and execution maps, and completed native tool reads confirm that the scalar-task authors read it. It explicitly decodes the JSON argument, calls `process(data)` and serializes the return. However, this transport mapping does not itself declare a semantic payload schema. Both models continued to regard the scalar input/result shape as unspecified. This qualifies the initial diagnosis that the adapter alone would supply all necessary interface facts: it did not solve the author’s semantic-interface question. The existing baseline API behavior could inform an original public interface description, but deriving that description reliably would itself need assurance. We did not invent a schema or narrow the promise to obtain a usable handoff.

Luna pagination explicitly limited its probes to string IDs and integer scores while reporting other sortable domains unresolved. It did not certify the preserved defect. Its `NOT VERIFIED` preserves that uncertainty; it is not a negative product verdict. The recurring domain-inference problem remains unresolved despite implementation blindness. The two scalar authors also treated absent product observations or general effect guarantees as design-stage gaps. This mixes evidence design with later product verification: a blind author cannot inspect the implementation to establish those properties. The protocol already distinguishes PLANNED from acceptance, but native behavior did not reliably maintain that distinction.

Some UTC standards questions and the limits of finite observations are legitimate unresolved concerns. None is labeled a product defect or false rejection without an executable, source-grounded counterexample. The four observed author judgments concern evidence design; the two timeouts are unavailable invocations. There are **zero observed product acceptances or rejections**, so new false-acceptance and terminal/recoverable false-rejection rates remain unavailable.

All **six native boundary readbacks passed**, including denied access to the actual implementation and private oracle, protected inputs/Git/receipts, writable scratch and denied network access. The two timed-out calls’ canaries were independently read from their partial native transcripts; this does not make the invocations available. Every author input snapshot still matches its saved stage snapshot. Final whole-fixture and archived-runtime validation **passed**, including Git index bytes. The operator metadata drift from the previous trial remains preserved there; it did not recur here. Workers were reconciled as finished.

## Resources and limits

This qualification consumed **six native model dispatches**, **1,855.0 known summed native stage seconds**, and **628.4 qualification wall seconds** including controls and coordination. Known usage is **385,659 input tokens**, including **301,568 cached**, and **37,466 output tokens**. Two timed-out Sol calls have unknown usage, so token totals are lower bounds. Cached input is a subset of input and is not added again; reasoning output is not charged twice. All unsuccessful invocations are included.

Sol’s three calls consumed 1,614.2 native stage seconds, with 135,090 known input tokens (106,496 cached), 15,126 output tokens and two unknown-usage calls. Luna’s three calls consumed 240.8 native stage seconds, with 250,569 input tokens (195,072 cached) and 22,340 output tokens. Different failure times and unknown usage do not establish model superiority. The observed 67.2–600.0-second range is diagnostic, not a defensible population long-tail percentile. Test wall time overlaps the experiment and is not added to summed model-stage cost.

Task-specific human interventions were zero during the native calls. Study/operator attention and initiating-agent costs remain unknown; zero task intervention is not zero study effort. Authoritative dollar pricing was not frozen, so dollars remain unknown. There were no natural delivery assignments or independently correct natural deliveries: cost per correct delivery and correct deliveries per workflow hour remain unknown, rather than using a zero-success or incomplete-population denominator.

Private retained evidence includes the manifest, runtime archive, `native.log`, all six author stage records and raw transcripts, `operator/author-readback.json`, `operator/boundary-readback.json`, `operator/ledger.json`, its receipt-accounting script and `operator/evidence-index.json`. Raw artifacts remain ignored and outside worker/verifier read allowlists. The historical reports, previous ledgers, original candidates, failed qualifications and stopped follow-up declarations remain unchanged.

## Decision and outstanding work

The bounded interface repair did not qualify the candidate-blind design. Preserve its opt-in implementation for diagnosis, keep it disabled by default, and **do not make further author/prompt retries a route to a favorable comparison**. The native preflight and integrity protections are useful safeguards, but have not produced qualified source coverage or demonstrated new-path recovery. Further assurance stages are not justified merely by their availability.

This supports abandoning this particular design as the production remedy and reconsidering how original public interface facts and source obligations can be established without inferring them from a candidate or granting generated probes oracle status. It does not support relaxing acceptance, automatic certification, or declaring Proofline broadly effective or ineffective from these diagnostic subsets.

**No new comparison campaign was declared or dispatched.** The original four-way Sol comparison and matched Luna/Sol experiment, unfamiliar held-out tasks, larger autonomy tasks, prospective study-level operator measurement and complete efficacy decision remain outstanding. The stopped `followup-v2` remains four executed and 140 unexecuted assignments under its original frozen code/settings; it cannot resume under changed runtime. A genuinely different remedy must pass fresh native qualification, including independent source adjudication and production binding/isolation/recovery, before those comparisons run. E1–E3 and S6 remain explicitly incomplete.
