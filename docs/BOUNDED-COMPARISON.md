# Bounded comparison of the simplified workflow

13 October 2026. **All 18 assignments completed once. Decision: keep the existing runner optional; add no assurance machinery.** Ordinary agent and agent plus review each delivered six candidates that passed the frozen private criteria. Proofline delivered five; its pixel-history invocation failed before coding because the selected model was at capacity. No incorrect handoff or correct-but-blocked candidate was observed.

Proofline supplied cheap, frozen command receipts, but showed **no added correctness benefit** in this sample and delivered one fewer candidate. The capacity failure occurred in the shared native coding transport; it does not identify a runner-specific coding defect. Faster consumed time cannot compensate for that missing delivery or establish superiority.

This is the new owner-authorized observed-performance study following [S6’s abandon/simplify decision](S6-DECISION.md). It does not complete the original S6 comparisons or restore full-promise certification. The [historical results](S6-RESULTS.md), [original protocol](S6-PILOT.md), [follow-up](S6-FOLLOWUP.md) and [retired redesign experiments](S6-VERIFICATION-REDESIGN.md) remain unchanged. P2P and Luna/Sol comparisons remain deferred.

## Frozen design

The checkout was clean at `4f3432e`. The supported workflow and transport were inspected before dispatch. Execution used macOS 26.6.2 arm64, Codex CLI 0.162.1 and Homebrew Python 3.14.8. Every coding and review invocation selected `gpt-6.1-sol` with reasoning `high`; there was no model substitution.

The immutable study inputs are under ignored `.proofline/bounded-comparison-20261013-v1/frozen/`. Manifest SHA-256:

`f9bd99a4f11032282dacf9c1b58407b7e4c0b561340586e00ec9e7f858456ed5`

That directory freezes all six requests, Git starting repositories and public seams; caller-check argv; private expectations and grader bytes; correct references, defective controls and alternatives; runtime source and native binary archives; model settings; population, order, budgets, outcome definitions, stop rules and accounting. Its files were made read-only and their hashes checked before every assignment and after execution. System libraries and the entire operating system are not archived.

The six new tasks were crate packing, attendance summaries, reversible pixel edits, bounded character runs, weighted approval ballots and tag-based menu selection. Each started with a JSON CLI, `product.process`, `service.process`, a named domain seam, README and compatibility test. Requests required behavior across the library/service/CLI seams plus focused tests and documentation. No exposed S6 task, preserved counterexample or retained workload draft was reused. These are modest synthetic repositories, not production systems.

Each matched arm received the same raw request, starting tree and public caller-check definitions. The checks were one concrete behavior assertion and CLI version compatibility, executed from frozen argv rather than candidate-authored tests. Further private probes and answer keys were inaccessible to workers and reviewers. There was no model-authored planning stage or shared-preplanned cohort.

All arms reuse `checks/s6_baseline.run` and `checks/codex_live.command` for coding. The runner invokes that helper through the actual `checks/local_run.run` implementation used by `proofline.py run`. Ordinary coding ends at its useful self-checks and completion handoff; review adds one fresh read-only reviewer and no correction; Proofline adds the caller-selected host checks and current status readback. The runner’s prompt explains the subsequent checks; the baselines receive the same definitions as public guidance. This is a comparison of added checking and handoff behavior, not different coding architectures.

Every episode had a 900-second cumulative cap, coding at most 600 seconds, fresh review at most 240 seconds and each runner check at most 60 seconds. Baseline review used the existing 840-second allocation with a 240-second reserve, leaving at most 600 seconds minus preparation for coding. Ordinary and runner coding used the same 600-second allocation minus preparation. Preparation, preflight, freezing, native stage overhead and check/status work are included in measured workflow time; shared study construction and private grading are separately charged. All observed episodes and stages stayed within their caps.

One repetition, serial concurrency of one, and rotating arm order were frozen: O/R/P, R/P/O, P/O/R, then repeat for tasks four through six. There were 18 coding dispatches and six reviewer dispatches. No retry, correction loop, budget extension or scoring-time code/criteria change occurred. Stop rules covered isolation failure, oracle leakage, corrupted inputs and unsafe execution; an incorrect handoff would have been recorded without retiring the population. No stop condition occurred.

## Grader controls and isolation

Before any model dispatch, all **18 finite native controls matched**: six correct references and six algorithmic alternatives passed, and six deliberately defective controls failed. Alternatives share validation helpers and service wrappers but use different domain algorithms. There were no native control mismatches requiring adjudication. An earlier offline mechanics pass also matched all 18 product controls and positive domain probes; its elapsed time was not retained. Controls establish mechanics for this study, not universal source coverage.

The frozen grader exercises the public CLI and product, service and domain library seams, including boundary/error behavior, input preservation and compatibility. It checks unchanged candidate bytes, scratch effects and undeclared imports. Expected values come from the frozen study specification, never worker tests. Observed correctness means all these finite criteria matched; unavailable grading would have remained unknown. Delivery is separate: ordinary completion, completion plus reviewer pass, or current runner CHECKS PASSED.

Native canaries denied candidate/source/Git/receipt writes, private answers, runtime archive and sibling/root repository reads, and network access, while permitting scratch writes. Every assignment’s native boundary preflight passed. Receipt audit found 24 distinct invocation IDs and fresh thread IDs; all workers finished. All frozen inputs and original candidate snapshots matched at final readback. Host execution was used to initialize the native sandbox; isolation was never disabled.

## Matched outcomes

Each cell gives independently observed candidate correctness, delivery and elapsed workflow seconds. The retained seed from the capacity failure is incorrect under the frozen behavior probes; no implementation handoff occurred. All 18 assignments were graded, including that failed workflow.

| Task | Ordinary agent | Agent plus review | Proofline runner |
| --- | --- | --- | --- |
| crate-packing | correct / delivered; 160.3s | correct / delivered; 265.5s | correct / delivered; 202.2s |
| attendance-summary | correct / delivered; 229.3s | correct / delivered; 461.9s | correct / delivered; 143.5s |
| pixel-history | correct / delivered; 169.4s | correct / delivered; 288.3s | incorrect seed / no handoff (capacity); 4.7s |
| bounded-runs | correct / delivered; 196.3s | correct / delivered; 256.4s | correct / delivered; 171.7s |
| approval-ballots | correct / delivered; 162.9s | correct / delivered; 244.4s | correct / delivered; 165.4s |
| menu-selection | correct / delivered; 149.2s | correct / delivered; 538.6s | correct / delivered; 153.7s |

All six reviewers returned passed=true. All ten checks on the five successful runner candidates passed. The pixel runner dispatched no checks because coding was unavailable. Incorrect handoffs: **0/18**. Correct-but-blocked candidates: **0/18**. Those zeros describe the frozen finite observations, not an estimated general defect probability.

The failed runner call lasted 4.182 native stage seconds, 4.704 workflow seconds, exited 1 and emitted “Selected model is at capacity. Please try a different model.” It was retained with unknown token usage. There was no retry, model switch, candidate edit or favorable replacement. This is availability failure, not a check rejection or a false block on correct code.

## Resources

All assigned attempts, including the failure, enter these denominators. Workflow hours are summed episode time, not campaign wall time. No unmatched success-only median is used. Runner totals with missing usage are known lower bounds; its complete tokens per correct delivery remain unknown. No authoritative prices were frozen, so dollars, dollars per correct delivery and deliveries per dollar are unknown for every arm.

| Arm | Correct deliveries / assigned | Workflow seconds | All-attempt median; range (s) | Native dispatches | Seconds / correct delivery | Correct deliveries / workflow hour |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| ordinary-agent | 6/6 | 1067.3 | 166.1; 149.2–229.3 | 6 | 177.9 | 20.24 |
| agent-plus-review | 6/6 | 2055.1 | 276.9; 244.4–538.6 | 12 | 342.5 | 10.51 |
| proofline | 5/6 | 841.2 | 159.5; 4.7–202.2 | 6 | 168.2 | 21.40 |

The runner’s short failure lowers consumed time. Its apparently favorable time ratios do not establish a benefit: it delivered fewer candidates, and its coding invocation is the same implementation as the baseline. Coding variability is substantial: the final review-arm coder alone took 496.4 seconds, versus 148.6 for the matched ordinary coder. Added review cost is directly observable as **496.4 seconds across six reviewer dispatches**. Added runner checking is **1.743 seconds across ten processes**, about **0.349 seconds per checked candidate**. Neither caught a natural defect in this population.

| Arm | Known input | Cached subset | Known output | Unknown-usage dispatches | Input + output / correct delivery |
| --- | ---: | ---: | ---: | ---: | ---: |
| ordinary-agent | 722,266 | 536,704 | 33,103 | 0 | 125,894.8 |
| agent-plus-review | 1,286,352 | 953,984 | 49,525 | 0 | 222,646.2 |
| proofline | 606,889 | 447,488 | 26,831 | 1 | unknown |

Overall: **24 native dispatches**, **3,963.7 summed workflow seconds**, **2,615,507 known input tokens** including **1,938,176 cached**, and **109,459 known output tokens**, with one unknown-usage dispatch. Cached input is already part of input; reasoning output is not added a second time. Native stage usage includes internal agent planning, checking and unsuccessful commands. Provider-internal request counts and initiating-agent usage remain unknown.

Preparation took **143.4 seconds**, including **141.8 seconds** for the 18 native controls. Controls used **1,041 native grading processes / 137.937 summed process seconds**. Final candidate grading took **140.4 wall seconds**, using **1,041 native processes / 138.940 summed process seconds**. Execution wall time was **4,112.1 seconds**; it includes workflow time, private grading and approximately 8.1 seconds of study orchestration/integrity overhead. These process times overlap their enclosing wall measurements and are not added twice. Grading is study cost, not an extra workflow assurance stage.

Prospective operator events cover the authoring window starting 07:30:40 UTC, frozen declaration at 07:39:55 UTC, dispatch at 07:45:01 UTC and execution finish at 08:53:33 UTC. The **861.2-second authoring-to-dispatch window** includes control execution and waiting; it is not active human attention. A separate **310.2-second readback/report-writing window** was recorded through documentation checks, also as elapsed wall time rather than human attention. Earlier inspection time, human authoring/attention and initiating-agent tokens remain unknown. Operator events retain these distinctions. Task-specific manual corrections and interventions were **zero**; that does not make study/operator cost zero. No worker received additional answers or candidate edits.

Per-assignment usage follows. The capacity failure’s dashes mean unknown, not zero.

| Assignment | Workflow seconds | Dispatches | Input | Cached subset | Output |
| --- | ---: | ---: | ---: | ---: | ---: |
| 01-ordinary-agent | 160.3 | 1 | 114,082 | 76,160 | 5,168 |
| 01-agent-plus-review | 265.5 | 2 | 202,737 | 157,440 | 6,969 |
| 01-proofline | 202.2 | 1 | 154,906 | 117,248 | 5,535 |
| 02-agent-plus-review | 461.9 | 2 | 214,036 | 165,760 | 7,832 |
| 02-proofline | 143.5 | 1 | 95,645 | 59,904 | 4,663 |
| 02-ordinary-agent | 229.3 | 1 | 136,343 | 112,384 | 5,544 |
| 03-proofline | 4.7 | 1 | unknown | unknown | unknown |
| 03-ordinary-agent | 169.4 | 1 | 99,722 | 76,672 | 5,650 |
| 03-agent-plus-review | 288.3 | 2 | 225,824 | 173,696 | 8,982 |
| 04-ordinary-agent | 196.3 | 1 | 138,801 | 99,200 | 6,531 |
| 04-agent-plus-review | 256.4 | 2 | 214,898 | 149,888 | 8,299 |
| 04-proofline | 171.7 | 1 | 100,554 | 76,928 | 5,656 |
| 05-agent-plus-review | 244.4 | 2 | 227,873 | 166,272 | 7,518 |
| 05-proofline | 165.4 | 1 | 117,772 | 93,568 | 5,475 |
| 05-ordinary-agent | 162.9 | 1 | 137,841 | 97,664 | 5,645 |
| 06-proofline | 153.7 | 1 | 138,012 | 99,840 | 5,502 |
| 06-ordinary-agent | 149.2 | 1 | 95,477 | 74,624 | 4,565 |
| 06-agent-plus-review | 538.6 | 2 | 200,984 | 140,928 | 9,925 |

## Limits and practical decision

This is one repetition on six synthetic tasks, one host and one model. The task/criterion author also authored the references; independent means independent of task workers and reviewers, not a second human oracle author. Alternatives share validation code. Finite coverage can miss defects. The frozen score does not assess README accuracy or the quality of worker-authored tests; a separate post-scoring presence readback found README and test changes in all 17 delivered candidates, without changing any scores. Subclasses, standards-heavy domains, large repositories, deployment and long-running production behavior were outside scope. No statistical superiority, general reliability or human-attention saving follows.

**Continue the thin runner only when frozen caller-command receipts are useful. Simplify usage around ordinary autonomous coding and those explicit checks; do not make model review mandatory or add another assurance stage.** The observed benefit is cheap mechanical check recording, not better correctness. Ordinary delivered all six; review added six calls without changing observed correctness; Proofline delivered five and lost one to shared model availability. Keep the missing-delivery result visible. There is no evidence here to reopen certification, broaden the benchmark or claim a P2P/Luna advantage. No production runtime change was needed.

## Checks and retained artifacts

All native controls passed, all 18 assignments executed once, and final receipt/identity/budget assertions passed. Seven focused runner/baseline tests passed in 5.396 seconds. The earlier 196-test validation remains historical; the full suite was not rerun because production code did not change. Documentation link and whitespace checks were run for this report and the README/IMPLEMENTATION update.

Private artifacts remain ignored and preserved: `.proofline/bounded-comparison-20261013-v1/frozen/manifest.json`, `frozen-hashes.json`, `controls.json`, `controls/`, `assignments/`, `report.json` and `resource-readback.json`. Every assignment retains its native streams, prompt, lifecycle receipt, frozen candidate and independent `evaluation/grade.json`. Authoring/check logs, the fixed one-off script and prospective events are under `.proofline/bounded-study-authoring/`. No old campaign resumed, no historical score changed, and no push, PR, merge, deployment or other remote mutation occurred.
