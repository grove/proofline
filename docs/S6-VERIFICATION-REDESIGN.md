# S6 verification redesign — candidate-blind remedy unqualified

12 October 2026. **Decision: keep the comparison gate closed and continue redesign. S6 remains incomplete.** The candidate-blind experiment produced no usable source-challenge handoff. It has not earned promotion to the default delivery path.

Read alongside the preserved [historical results](S6-RESULTS.md), [first follow-up](S6-FOLLOWUP.md), and [pilot protocol](S6-PILOT.md). Neither previous report was rewritten. No previous campaign resumed, no new efficacy campaign was declared, and no push, PR, merge or deployment occurred.

## Diagnosis and implemented change

All nine retained verification trials and their 60 native stage records/transcripts were inspected, including invalid handoffs and early misclassifications. The v3 prover's correct identification of string-score narrowing remains evidence; later positive judgments do not supersede it. Defective positive references and unavailable invocations remain separately classified.

Repeated native source-domain failures survived prompt changes while binding and isolation remained intact. The next remedy therefore changes the information boundary: optional `--source-challenges` adds a fresh source-challenge author before implementation. It receives original source, accepted-input/context and public interface guidance in a stub repository. Base/candidate implementations, implementation tests, peer judgments and the private oracle are inaccessible. A native read-denial canary targets the real implementation in addition to the existing protected-input, receipt, oracle and network canaries.

The author returns source quotations, domain reasoning and executable Python probes. The controller requires all material IDs, executable syntax, an exact source quote, a valid native handoff and intact boundaries. It seals probes outside the product after implementation, binds their identity into verification, and requires successful exact native command citations for every frozen probe before positive proof. Reviewer/prover duties and the complete original promise remain intact. Disputed expectations or observation failures are evidence gaps; assertions cannot redefine the promise. Changed probes or candidate bytes invalidate acceptance. The extra dispatch consumes the existing cumulative budget; correction retains the source design and still checks fresh candidate bytes.

This is an opt-in experiment in the production `deliver` controller, not a default change. It adds no dependency, benchmark answers or private evaluator access. Candidate-blind design prevents copying an implementation's restrictions directly, but does not mechanically establish correct expectations or complete coverage.

## Frozen native qualification

The successful declaration is `.proofline/s6/source-challenges-v2/manifest.json`, SHA-256:

`76c4836431a8955e548c36ab290143cb30028ce6c5d7dc4ff78c6aeea849c8b0`

`source-challenges-v1` is an aborted declaration with zero model dispatches: one preserved candidate had a root commit, so the initial `HEAD^` lookup failed. That failure is retained; the runner now handles root commits. It was not a model trial or an executed comparison.

Before dispatch, v2 froze sources, candidate snapshots/history, independent evaluator expectations, runtime archives, exact models (`gpt-6-luna` and `gpt-6.1-sol`, both reasoning `high`), a 600-second allowance per native stage and concurrency four. The installed runtime remains macOS, Codex CLI 0.162.1 and Python 3.14.8 through the selected Homebrew interpreter. The actual P2P checkout remains `/Users/grove/projects/promise-to-proof` at `a26e0a9c50a7d75fc3a02feda491bf497de94cf4`; its controller/interfaces were inspected, with no P2P modification or new P2P model delivery.

Six independent native evaluator controls matched before model dispatch: four preserved defective candidates (pagination string scores, integer-subclass paging, Unicode whitespace and UTC representations) failed; the final corrected comparator-based pagination and insertion-based alternative passed. Preserved source bytes and candidate snapshots matched their origins at declaration. These are finite native control observations, not model-verification qualification.

The planned qualification had six candidate-blind author invocations and 24 fresh reviewer/prover invocations, covering both models on all six candidates. Source design was a prerequisite for each subsequent invocation; unavailable invocations were not retried.

| Model | Author dispatches | Usable designs | Observed design-stage NOT VERIFIED | Unavailable design invocations | Known summed stage seconds |
|---|---:|---:|---:|---:|---:|
| Sol/high | 3 | 0 | 2 | 1 timeout at 600 seconds | 1,538.2 |
| Luna/high | 3 | 0 | 2 | 1 invalid handoff | 284.9 |

All six authors finished; **all 24 reviewer/prover invocations remain NOT EXECUTED**. Four authors returned observed `NOT VERIFIED` about scalar payload/result mappings and coverage. The source-only stub withheld the existing adapter facts: the CLI passes `json.loads` directly to `process` and serializes its returned value. The authors refused to infer that mapping from the scalar source promises. This exposes inadequate interface guidance in the experiment; it is not an independently adjudicated product defect or permission to narrow the source. Sol also raised unresolved portions of the named timestamp standard. Luna's pagination report returned `PLANNED` with nonempty findings, violating the strict handoff; its invocation is unavailable. Sol pagination exhausted its frozen stage allowance without a completed handoff or available usage.

The gate failed before product judgments. There were **zero observed positive or negative reviewer/prover judgments**, so no new false-acceptance, recoverable/terminal false-rejection or natural-delivery reliability rate can be estimated. Positive acceptance, native product rejection and native unchanged-code recovery for this new path remain unqualified. All six native boundary canaries passed, including denied implementation access; the timed-out author's canary was independently read back from its partial transcript. The timeout demonstrates a bounded native stage, not completed delivery or bounded successful recovery. Existing native recovery evidence remains historical; deterministic new-path recovery tests do not establish model judgment quality.

Final whole-fixture validation also exposed an operator integrity mistake: a `git status --porcelain` inspection after declaration refreshed index stat caches in four copied frozen repositories. The changed snapshots remain retained. Disposable reconstructions replacing only the copied index with its origin bytes reproduce each declared snapshot hash, establishing that source/product bytes and Git trees were unchanged. This does not erase the failed immutable-fixture check or make the qualification valid. The runtime archives still match; future operator inspection must disable optional Git locks and preserve metadata. The separate audit is `operator/freeze-integrity-readback/report.json`. Neither these fixtures nor this failed qualification can be silently resumed as an immutable comparison.

## Independently adjudicated blind-probe defects

The invalid Luna pagination handoff remains invalid. Its raw probe source was separately frozen and replayed in the native read-only sandbox, without another model invocation, against the preserved numeric-only candidate and both corrected pagination structures. All nine executions left inputs unchanged.

R1 passed all three candidates. It tested only numeric scores, so it failed to discriminate the already adjudicated string-score defect despite never seeing the implementation. Candidate blindness alone did not prevent the recurring domain assumption.

R2 failed all three candidates because its expected tied-row order was wrong. For the authored rows, score 3 comes first, followed by score-2 IDs `a` then `b`; offset one therefore returns `a,b`. The probe expected `b,a`. Native output was `a,b` for all three candidates, consistent with the source. R3 passed its narrow import/mutation observations on all three.

These are failures in model-authored evidence design, **not observed model false acceptances or false rejections**. Compiling, freezing and citing a probe cannot make its expectation correct. We did not edit the failed probes, reclassify their invocation as available, or repeat qualification until favorable.

## Checks, resources and retained evidence

- Native regression suite: **164 tests run, 162 passed, two Linux-specific platform skips**, 137.779 seconds. Log: `.proofline/s6/source-remedy-native-tests.log`.
- Final focused mechanics: **7/7 passed**, including two tests added after the full-suite run. They check inaccessible candidate/test content, strict frozen citations, failed or altered probes, invalid source/hand-offs, cumulative dispatch limits, product correction, unchanged evidence recovery and drift. These authored transport doubles establish mechanics only. Log: `source-remedy-mechanics.log`.
- Focused transport suite: **17 tests run, 14 passed, three native opt-in skips**; the subsequent native full suite covered the applicable native checks. Log: `source-remedy-transport-tests.log`.
- Native evaluator controls: **6/6 matched**. Independent raw-probe replay: **9 completed observations**, as adjudicated above, 1.538 seconds wall time.
- `git diff --check` passed. Historical reports, stopped declarations, original candidates, receipts, prior ledger/index and retained trials remain preserved. An initial offline run exposed a new compatibility bug with a transport double lacking saved commands; the execution validator was restricted to remedy-enabled records, the focused reproduction passed, and the final native suite passed. The original failed log remains retained.

New model study cost is **six native dispatches**, **1,823.1 known summed native stage seconds**, and **618.8 qualification wall seconds** including controls and coordination. Known usage is **531,988 input tokens**, including **364,544 cached**, and **43,124 output tokens**. One timed-out dispatch has unknown usage; token totals are lower bounds. Cached input is not added again, and reasoning output is not charged twice. Every unsuccessful author invocation is charged. These are qualification costs, not additional independently correct natural deliveries or a Luna/Sol efficiency comparison. Observed stage times span 84.8–600.0 seconds; six diagnostic calls do not support a long-tail population percentile.

No task-specific human intervention occurred during these native invocations. Study/operator attention and initiating-agent time/tokens remain unknown. Dollar prices, cost per independently correct natural delivery and correct deliveries per workflow hour remain unknown; no natural comparison deliveries were dispatched. Partial CLI process receipts and replay/test wall times are recorded separately and overlap the enclosing qualification time; they are not added to model-stage totals as independent costs.

The private `source-challenges-v2/report.json`, `native.log`, runtime archive, protected author streams, `operator/blind-probe-readback/`, `operator/ledger.json` and `operator/evidence-index.json` retain this attempt. `source-remedy-prior-trial-readback.json` indexes the original 60 stage handoffs without changing them. Raw transcripts and oracle artifacts remain ignored and outside worker allowlists. `checks/s6_verification.py declare NEW_DIRECTORY` and `run NEW_DIRECTORY` provide single-use qualification; failed invocations remain recorded rather than silently rerun.

## Decision and unresolved work

**Do not promote this remedy or dispatch comparisons under it.** The information boundary worked within observed native canaries, but the added design stage produced no usable plans, repeated the numeric-domain assumption and authored an incorrect expected order. Its observed cost has not bought qualified acceptance. Retain the opt-in implementation for diagnosis and continue redesign; do not expand automation or the efficiency claim.

A subsequent design needs sufficient original public-adapter facts without importing product algorithms, and a way to challenge the correctness and coverage of generated expectations. That work requires another justified, frozen qualification, not a wording change presumed trustworthy. Positive controls, structural alternatives, observed defect rejection, binding/isolation and native bounded recovery remain prerequisite gates.

**No new comparison population was declared or dispatched.** The stopped followup-v2 remains four executed and 140 unexecuted assignments under its original declaration; it cannot resume under changed code. The original full four-way Sol comparison and separate matched Luna/Sol experiment, genuinely unfamiliar held-out tasks, realistic larger autonomy tasks, prospective operator measurements and efficacy decision remain outstanding. E1–E3 and S6 are explicitly incomplete.
