# Luna medium/high: two-task exploratory pilot (#38)

**Provisional decision: MEDIUM PREFERRED for this pilot's observed delivery time
and token totals.** Both efforts produced independently source-supported fixes
on both tasks. Medium used 9.6% less attempt time, 23.1% fewer total input tokens
and 33.1% fewer output tokens. **Cheaper delivery is unproven:** medium used
37.4% more uncached input, and actual charges are UNKNOWN. This is a small useful
observation, not a statistical result or product-wide default recommendation.

Four ordinary coding attempts ran on 2026-10-21 using existing ChatGPT login,
Codex CLI 0.163.0, macOS 27.0.1 arm64 and Python 3.15.0. Each requested exactly
`gpt-6-luna` with either `model_reasoning_effort=medium` or `high`. Exact backend
identity and billing are UNKNOWN. No API key, paid fallback, credits, extra
reviewer model, correction turn or retry was used. All four native invocations
completed successfully. The earlier catalog RPC timed out before initialization;
that zero-inference diagnostic did not establish model unavailability. The four
actual completed invocations establish the observed dispatch path.

## Tasks and matching

| Task | Original request | Pinned original base | Order |
| --- | --- | --- | --- |
| 1: small shared-resolution bug | [python-dotenv #715](https://github.com/theskumar/python-dotenv/issues/715): empty `${name:-default}` must use the default | `0b2880591780a426b0551436f47a17e7a76d954f` | medium, high |
| 2: compatibility edge | [humanize #366](https://github.com/python-humanize/humanize/issues/366): custom filesize formatters with text must remain usable while numeric rollover works | `785e5dcc0d0308ad0dff3f6cc0faa7085ad0375b` | high, medium |

[Complete original requests](requests/), [acceptance checklist](acceptance.md),
[protocol](protocol.json), [input hashes](input-hashes.json) and exact tracked
baseline archives are retained. Both requests were open and reproducible at their
selected bases. Neither task/solution was used as a historical Proofline coding
assignment. The humanize repository was previously screened: #52's archive lists
upstream PR #367's title and its link to #366, without implementing or testing this
task. Both are public requests with possible public-solution/training exposure;
these are fresh Proofline attempts, not a claim of globally unseen tasks.

Each attempt began in a fresh ephemeral CLI context, with identical tracked
baseline tree, source, common guidance, tools and native permissions within each
pair. Paths and remaining-budget text differ per slot; reasoning effort is the
only experimental configuration difference. The cap was 900 seconds per
attempt, self-testing included. No cap was reached. The existing
`checks.coding_attempt.run`, `evaluation.recovery.grader.invoke` and
`evaluation.source_preflight.qualify` were reused; no framework or product code
changed. Inputs were declared and hashed before the first dispatch.

The native profile allowed writes only to the assigned candidate and scratch,
kept Git/source/evidence protected, denied siblings/private graders, and disabled
network, plugins, memories and delegation. The process canary passed. Each
worker's ordinary runner preflight also passed; candidate Git and protected
inputs remained intact. Workers received no other implementation or independent
grading feedback. **Zero human interventions within attempts.**

Lessons reused: #36's source-bound expectations and alternative/defect controls;
#37's separation of passing checks from complete acceptance; #41's exact canonical
Python argv and independently recorded execution outcomes. The tasks do not
require Proofline's skill-discovery aliases, so #42 did not add a prerequisite.

## Observed deliveries and resources

“Correct” below means independently supported against the original request by
final source/test-diff review and protected behavioral observations. It does not
mean the entire repository suite or every possible input was verified.

| Task / effort | Correctness evidence | Full attempt seconds | Native task turns / tool calls | Input / cached input / output tokens | Actual cost |
| --- | --- | ---: | ---: | ---: | --- |
| dotenv / medium | Correct; 4 independent public-path cases; regression added | 34.291 | 1 / 18 | 119,620 / 77,952 / 2,351 | UNKNOWN |
| dotenv / high | Correct; same 4 cases; shared-resolution and integration regressions added | 40.638 | 1 / 15 | 167,793 / 145,792 / 3,143 | UNKNOWN |
| humanize / high | Correct; 8 independent cases plus public import/reproducer; prefix/suffix regressions added | 49.530 | 1 / 22 | 183,628 / 137,728 / 4,035 | UNKNOWN |
| humanize / medium | Correct; same 8 cases plus public import/reproducer; prefix/suffix regressions added | 47.223 | 1 / 8 | 150,699 / 99,072 / 2,449 | UNKNOWN |

All four are **independently supported correct deliveries within this scope**;
zero confirmed material defects and zero disputed expectations were found.
Original pytest suites are **unavailable**, not passed. No independent human
whole-request review was performed; the organizer's review is independent of the
coding workers, not independent human replication. A future contradictory
source-grounded observation should supersede these finite assessments.

Elapsed covers baseline capture, native preflight, coding, all worker self-tests,
self-repairs and terminal freeze. Independent grading is additional: native
behavioral commands took 0.161, 0.165, 0.111 and 0.111 seconds respectively; the
complete host commands took 0.366, 0.359, 0.445 and 0.424 seconds. The shared
supplementary public-import command for both humanize candidates took 0.946
seconds. Other preparation, organizer/source-review time and tokens, active human
time and publication overhead were not metered and remain UNKNOWN. These are not
claimed as free or included in a complete project cost.

| Paired total | Medium | High |
| --- | ---: | ---: |
| Source-supported deliveries | 2 / 2 | 2 / 2 |
| Full coding attempt seconds | 81.514 | 90.168 |
| Native coding invocation seconds | 78.765 | 87.387 |
| Native task turns / tool calls | 2 / 26 | 2 / 37 |
| Input tokens (cached included) | 270,319 | 351,421 |
| Cached input tokens | 177,024 | 283,520 |
| Uncached input tokens | 93,295 | 67,901 |
| Output tokens | 4,800 | 7,178 |
| Attempt seconds per supported delivery | 40.757 | 45.084 |
| Actual dollars / dollars per supported delivery | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN |

Cached input is a subset of input. Reported reasoning output (1,017 medium;
2,365 high) is a subset of output and is not added again. Cache-write input was
zero. “Turns” is the observed CLI task-turn count; internal backend model-request
counts are UNKNOWN. Tool calls count completed command-execution and file-change
items, including failed calls. High's larger cache fraction prevents inferring
cost savings from medium's smaller total input. The elapsed advantage was 15.6%
on dotenv and 4.7% on humanize; normal latency variation could explain part of it.

## Testing, difficulties and source fidelity

All four workers added genuine pytest regressions and used stdlib assertions.
Dotenv medium passed five integration plus two direct checks; high passed five
direct checks. Both passed compilation and whitespace checks. Humanize high
passed five direct checks plus compilation/whitespace; medium passed four direct
checks and whitespace. All observed test commands, outputs and intermediate
failures are retained in [results.json](results.json) and the execution archive.
Per-tool cwd is not exposed by CLI events; it is not invented. Native invocation
and protected grader cwd/argv are recorded.

Both humanize workers initially invoked unavailable `python`, switched to
`python3`, and initially asserted the wrong GNU result for 999,999 bytes. Both
corrected their own check to use `1024**2 - 1`, without external feedback. This
was a self-test expectation error, not a confirmed implementation defect. Pytest
was absent for every worker and network/dependency installation was disabled
uniformly. Full/focused pytest results remain UNKNOWN/UNAVAILABLE; no fake test
runner or permission expansion was used to turn them green.

The predeclared source checks accept both explicitly proposed humanize fixes:
skipping rollover for decorated output, or deriving rounding independently.
Reference and plausible alternative controls pass; original baselines and
intentional defects fail, including a fix that accepts text but drops numeric
rollover. Both source declarations qualify with the existing preflight. All
eight control outcomes are in [controls.json](controls.json). The humanize module
probe bypasses package initialization to avoid depending on generated version
metadata; a separate later native observation verified actual public imports
and the original reproducer for both candidates. No new failure criterion was
introduced by that supplementary observation.

The existing freezer includes ignored bytecode produced by explicit compilation:
20 `.pyc` files in each dotenv candidate and seven in humanize high. Humanize
medium has none. These generated files remain in the exact terminal candidates
and binary patches; no candidate was cleaned or repaired after its attempt.
They are not source-required changes or a demonstrated behavioral defect, and
these terminal trees are not proposed as upstream release branches.

## Evidence and next step

[Per-candidate source audits](source-audits.json) record the reviewed obligations.
[results.json](results.json) records candidate commits/trees, original bases,
initial/grading tree equality, usage, native receipts, test commands, handoffs and
limitations. [execution-evidence.zip](execution-evidence.zip) retains each exact
binary-capable patch, tree manifest, actual dispatch prompt/source/guidance,
boundary receipt and relevant lifecycle/usage/self-test observations. Full raw
journals remain local; the archive explicitly omits model reasoning and redundant
code-reading output. Original raw-journal hashes remain in native receipts;
archived observation subsets have their own artifact hashes. Four full
copy-paste prompts and a [minimal worksheet](worksheet.md) are also retained.

All patch reconstructions, original baseline archive trees, frozen input hashes,
request/prompt identities, native receipt outcomes and local evidence links were
checked. [validation.json](validation.json) records the results. Historical
studies and results remain unchanged. No production routing changed, issue #38
remains open, and publication is a draft PR without merge authorization.

**Next:** if this direction is useful, add two to four fresh tasks from #38's
remaining scope, with at least one substantial multi-file compatibility change
and matched test dependencies ready before coding. Keep both effort choices
available until that evidence exists. This two-task exploratory phase does not
satisfy #38's original four-to-six-task comparison.
