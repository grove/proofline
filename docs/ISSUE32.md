# Sol-guided Luna: completed native pilot, no observed assistance gain

Issue [#32](https://github.com/grove/proofline/issues/32) asks whether Sol:high
planning/verification helps Luna:high deliver independently correct software at
lower **total cost per correct delivery** than either model alone.
The separately authorized live comparison completed **20/20 correct deliveries,
4/4 in every arm, initially and finally**. No managed correction was needed.
Sol assistance added time without an observed correctness gain on these tasks.
Observed dollar spending remains unknown, so monetary acceptance is unestablished.
PR [#33](https://github.com/grove/proofline/pull/33) remains unmerged and the issue
remains open.

The [completed report](../evaluation/results/issue32-lenient-results/README.md)
contains the actual native receipts, independent grades, all twenty outcomes,
phase times, model-separated tokens, failed commands and pricing sensitivity.

| Arm | Correct deliveries | Mean total seconds per correct delivery |
| --- | --- | ---: |
| Luna:high alone | 4/4 | 102.60 |
| Sol plan → Luna | 4/4 | 322.37 |
| Luna → Sol verification | 4/4 | 207.40 |
| Sol plan → Luna → Sol verification | 4/4 | 463.45 |
| Sol:high alone | 4/4 | 151.83 |

The full hybrid took 4.52× Luna-only time and 3.05× Sol-only time. False
acceptances, correct-but-blocked deliveries, unavailable assignments and
finite-grader omissions despite green repository tests were all zero.
Thirty-six native turns completed: 16 Luna and 20 Sol. All eight advisory plans
and eight independent reviews were valid; reviews reported no defects. Four
fixed tasks and one repetition create a correctness ceiling, not evidence of
reliability on arbitrary software. The verification package does not identify
checks, review and repair as separate causal contributions.

## Blockers resolved and history retained

The original declaration stopped at 0/20: native sandbox-exec returned exit 71
inside the enclosing execution sandbox, and model/list timed out at 15 seconds.
Host execution supports the **same native sandbox**, independently tested for
private-read, protected-write and loopback-network denial. No permission profile
or managed restriction was weakened. Actual completed inference now qualifies
both exact models at `high`.

App-server initialization took 37–39 seconds. A stack sample showed rollout
backfill during startup; removing no-daemon did not shorten it. The repaired
[catalog client](../checks/codex_catalog.py) awaits successful initialization,
then sends initialized and model/list using explicit stdio. It handles pagination,
drains bounded stderr and kills/reaps failed process groups under a 60-second
total deadline. Tests cover ordering, RPC/EOF/timeout failures, catalog identity,
reasoning support and bounded output. Catalog advertisement alone is not model
access qualification.

The denial fixture also needed a real host-owned results.json before preflight;
previously it existed only in finally. A grader-path canary required the pinned
corpus alias rather than an absent file. Both defects were fixed and tested.
Seventeen native grader controls and the existing model-free
Intentline/Proofline roundtrip passed before live dispatch.

Historical evidence remains separate and immutable:

- [Original preparation](../evaluation/results/issue32-preparation/README.md)
  and [host diagnosis](../evaluation/results/issue32-host-diagnosis/README.md).
- [75-second stopped live qualification](../evaluation/results/issue32-native-stopped/README.md):
  one Sol dispatch, no completed handoff, 0/20 primary assignments; usage unknown.
- [180-second qualified handoff and stopped primary attempt](../evaluation/results/issue32-qualified-stopped/README.md):
  four actual Sol → Luna → Sol → original-Luna turns completed in 343.35 seconds.
  The first primary Luna candidate passed public checks and a labeled post-stop
  finite grade. Sol completed inference after about 102 seconds, but CLI shutdown
  exceeded its 120-second lifecycle cap; the invocation/delivery stayed unverified.
- [Earlier #16 study](../evaluation/results/matched-v5-20261013/README.md):
  its 4/4 Sol correctness ceiling and overhead observations are not pooled here.

The user requested more lenient timeouts, then explicitly authorized fresh
`issue32-sol-luna-high-lenient`, freeze
`c8ea1f9b55ce5f8319e3c77090caf6c8038c597c0bc610348751382dc011da4e`.
No stopped declaration was resumed. The completed native control was reused
without new inference; fresh model-free native qualification took 201.51 seconds.

## Frozen workflow and trust boundaries

The [continuation protocol](../evaluation/sol_luna_host/protocol.json) and
[freeze](../evaluation/sol_luna_host/FREEZE.json) preserve the original requests,
starting implementations, order, private grading expectations and correction
policy. Every assignment gets a 1,200-second total / 900-second shared native
budget. Planning/review cap at 300 seconds, correction at 180; checks and grading
limits are unchanged. Verifying arms reserve 300 native seconds before
implementation. These are equal wall-time policies, not identical compute.
The maximum was 44 native turns / 24,000 seconds; actual execution used 36 turns
and 83.19 minutes. No retry, substitution, effort change or grader repair occurred.

The four tasks are idempotent ledger, path router, stable scheduler and tiered
invoice. They exercise replay conflicts, intermediate overdrafts, strict decoding,
precedence, zero-duration scheduling, disconnected cycles, exact integer rounding,
repeated rows, validation of unused entries, batch handling, nonmutation and CLI
compatibility. Private expectations were unavailable to either worker model.
Four correct and four alternative controls passed; nine defective controls failed
despite green public suites, including exact JSON-type and omitted-batch defects.
This qualifies a finite executable grader, not every possible input.

The existing runner, coding_attempt, candidate snapshots, native canaries,
local_run.check/inspect, Intentline exporter/adapter and actionable_failure APIs
are reused. Historical source bytes remain pinned. No production CLI, dependency,
new orchestration service or mandatory planning/review/approval stage was added.
`proofline.py check` stays optional and model-free.

Sol planning exports one advisory Intentline S1/schema-1/revision-1 plan. Luna
still receives the complete original request. Fresh Sol verification receives the
complete source, frozen candidate/diff and actual receipts with earlier-plan
metadata removed. Native command output confirms a full-source reread in all
eight reviews. The final audit revalidated all 36 native event/thread identities,
exact model/high arguments, eight check bindings, source copies, unchanged final
trees, budgets and frozen inputs. A focused regression validates archived live
evidence using the existing native parser.

One correction requires an intact candidate-bound assertion failure in immutable
public check 0 plus the existing strict actionable_failure validation. Only the
original Luna thread can correct; the new candidate is frozen, checked and
independently graded. Candidate-authored tests, Sol-authored expectations,
speculative findings, green checks, unchecked requirement links, private grades
and unavailable isolation cannot trigger repair. Actual same-thread repair was
qualified on a staged disposable control; no primary defect exercised it.

The [correction assessment](ISSUE32_CORRECTIONS.md) proposes the smallest separate
comparison: Sol selects a predeclared public probe whose expected result is
source-grounded and independently validated. Only its observed executable
failure can authorize repair. A checks-only comparison is needed to distinguish
Sol selection from better tests. This remains unimplemented and unauthorized;
the original correction rule and grader were never expanded after results.

## Cost and practical decision

Actual primary usage was Luna 2,731,000 input / 2,258,176 cached / 92,492 output
and Sol 3,686,481 input / 2,988,928 cached / 100,224 output tokens. Cached input
and reasoning output are subsets. The [accounting postprocessor](../evaluation/sol_luna_host/accounting.py)
preserves raw session totals, derives original-thread correction deltas and
retains hash-bound completed-turn usage without upgrading a timed-out invocation.
Earlier unknown consumption is not invented as zero.

Read-only account/usage/read returned no thread estimate for all 36 actual
primary threads, as it did for the earlier experimental threads. Its installed
schema can expose model/effort/speed groups and estimated credits/USD when the
billing route supports them. No credentials were retrieved; account-wide
activity was not published. Observed dollars and credit debits stay null; public API prices do not
establish Codex subscription spending. The API Costs endpoint requires separate
organization billing authority, which the current ChatGPT login does not establish.

The report's explicitly **hypothetical** published-standard-token-rate projection
gives credits per correct delivery: Luna .1886, plan 4.3035, verify 3.1882, hybrid
7.1522, Sol 2.7446. Its break-even family also finds no positive Sol/Luna unit-price
ratio where hybrid beats Sol alone, and hybrid beats Luna only below .003193,
versus the published credit ratio of 20. This excludes check compute, preparation,
qualification, authoring, human attention and unexposed charges. It is not observed
spending or monetary savings.

Use Luna:high alone for this corpus. Keep Sol planning/review and existing
Proofline checks optional. Receipt mechanics and bounded repair work, but their
incremental correctness value is unmeasured at this ceiling. No additional
benchmark framework or mandatory process is warranted. Neither medium nor xhigh
was tested or authorized; any changed follow-up needs its own frozen comparison.
