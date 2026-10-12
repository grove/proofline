# S4 — Bounded correction and resume

S4 implements local product repair, evidence-only recovery, failure classification,
and durable episode budgets/resume. The original source, adopted contract and
local-only authority remain binding. The S3 observations and P2P failures are
preserved; this slice does not establish a performance advantage.

## The delivery boundary

A reproduced product defect returns a concise gap containing affected criteria,
original obligations, observations and executable references to the **same native
implementer session**. The runner freezes its new candidate and dispatches fresh
independent review and proof. It never imports an old verdict onto changed code.
An evidence-only gap dispatches focused independent checking against unchanged
code; an exact applicable engineering PASS may be retained. Broken tooling/native
execution is an environment failure, and source/approval/prerequisite gaps are
explicit input blockers. Malformed or missing proof is never evidence of a
product defect.

The clean path still has three model stage dispatches. Default episode limits are
900 elapsed seconds, 240 seconds per stage, 12 attempted host/model dispatches,
and a 120-second verification allocation. Implementer dispatches require two
remaining checking slots and the time allocation; review leaves half that
allocation for proof. These are configurable host limits, not universal tuning
claims. All repairs and rechecks use the same limits. Per-stage provider usage is
retained; missing usage and monetary cost are unknown.

Progress comes from independent material criterion observations. Two consecutive
product correction rounds without a strict gain in satisfied criteria stop
early; edits, implementer confidence and unrelated green tests do not count.
A productive third round is allowed within the existing time/dispatch budget and
verification reserve. Evidence/environment rechecks have their own finite
non-progress stop and do not consume product correction rounds. After fixing
that gap, explicit resume can attempt one further check within the unchanged
budget; another failure stops again. This deliberately
conservative progress rule does not infer improvement from a new approach alone.

`resume <report.json>` locks the episode, validates host receipts and the frozen
source/contract/approval, execution map, base and current candidate, then
reconciles any unfinished dispatch. A completed protected stage result is
recovered without duplication. A terminated incomplete verifier gets a fresh
context. A terminated partial implementer resumes its exact host-issued session
and must complete a new handoff followed by independent checks. Running workers,
uncertain launches, unavailable session identities or changed protected inputs
block redispatch. A controller crash after a candidate commit but before its
checkpoint may require explicit reconciliation; ambiguous work is preserved,
never silently accepted or repeated.

Elapsed accounting combines wall time (including downtime) with monotonic active
execution and preserves consumed dispatches, even for interrupted workers.
Backward clock movement blocks resume. Exhaustion preserves the candidate and
remaining gap. Resume has no budget-reset/extension flags and cannot reopen a
terminal source or non-progress decision. Historical schema-1 S1/S3 records
remain inspectable; only S4 episodes are resumable. Publication and merge remain
S5 capabilities.

## Qualification

The final native qualification uses disposable copies of the established S0
username product and original source. The fixed private oracle is unchanged and
unavailable to every worker. It checks the public CLI in a protected native
sandbox and confirms candidate identity before/after observation.

```sh
python3.14 -B checks/s4_live.py --output .proofline/s4-live/final
python3.14 -B proofline.py status .proofline/s4-live/final/seeded-product-repair/run/report.json
python3.14 -B proofline.py status .proofline/s4-live/final/evidence-only-recovery/run/report.json
PROOFLINE_NATIVE_TESTS=1 python3.14 -B -m unittest discover -s tests -v
python3.14 -B checks/fixtures/s0/test_oracle.py
```

The qualified host is macOS/Darwin 25.6.0, Python 3.14.8 and Codex CLI 0.162.1,
using the existing configured `gpt-6.1-sol` / `high` preferences. Workers retain
the existing restricted native policy: protected source/candidate/Git/receipts,
separate writable scratch, and no network, external writes, MCP, plugins or
delegation. Only the implementer persists/resumes; every reviewer/prover context
is fresh. These are small local observations, not a general recovery guarantee.

| Gate | Evidence layer | Observation |
| --- | --- | --- |
| R1: targeted product repair | Real native models + fixed oracle | Host seeds the empty-only validator before freeze/review; reviewer rejects whitespace handling, the original implementer repairs it, fresh reviewer/prover check the changed candidate |
| R2: unchanged evidence recovery | Real native models + fixed oracle | First proof deliberately executes only the boundary canary and reports missing behavioral observations; fresh proof checks unchanged code and retains the exact engineering PASS |
| R3: environment vs product | Deterministic fault injection + retained actual failed native setup | Environment reports and unsuccessful transport receipts never trigger product repair; failed native preflight must recover before any model dispatch |
| R4: cumulative budget/reserve | Deterministic controls + native episode records | Exhausted dispatch/time limits prevent further work; restart consumes downtime and retains dispatches; review/proof capacity is reserved and unknown usage stays unknown |
| R5: stopping/progress | Deterministic controls | Two non-progress rounds stop at six dispatches; improving criteria permit a third repair and acceptance at nine dispatches |
| R6: interruption/resume | Separate-process native delivery + native process control + deterministic controls | Controller exits after a protected reviewer result; resume recovers it without duplicate review. An actual orphaned running process blocks reconciliation until termination. Partial implementation, incomplete verifier, stale inputs/candidate/map, malformed budget and concurrent controllers are covered |

The live controls deliberately inject faults. They are not ordinary autonomous
performance observations. Raw local reports, transcripts, native lifecycle IDs,
command evidence, usage and oracle receipts are retained under
`.proofline/s4-live/`; none are tracked as product changes.

Both final cases are **LOCAL ACCEPTED** by fresh `proofline.py status` readback.
The qualification report is **OBSERVED**, and all 19 fixed oracle observations
match for each final candidate without changing its identity.

| Final case | Dispatches | Episode elapsed | Input tokens | Cached input tokens | Output tokens | Candidate commit |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Seeded product repair | 5 | 484.569 s | 555,322 | 447,360 | 15,171 | `7ac58378d3183883fce73915ad5f6218e0c61de1` |
| Evidence-only recovery + restart | 4 | 400.124 s | 333,955 | 221,952 | 10,868 | `757159242b869aa219d1a0f3361093906eda069b` |

The final qualification took 892.435 seconds overall, including fixture setup
and private oracle observations outside the two separately bounded delivery
episodes. Cached input tokens are part of reported input usage, not an additional
charge. Monetary cost is unknown; no rate or zero-cost assumption is made.
The product episode uses one implementer thread twice and three distinct
verification threads. The evidence episode recovers the completed review in
another process, then uses two distinct proof threads on one unchanged binding.
Raw records: `.proofline/s4-live/final/report.json` and each case's
`run/report.json`. Repeat the command with a **new** output directory.

The final native regression suite passed **96 tests**, with two Linux-specific
checks skipped on macOS. This includes actual controller-death/process-group
reconciliation and the existing native isolation/Git checks. The fixed oracle's
three positive/defective/alternative sanity tests also passed. Deterministic
controls establish stopping, accounting and state mechanics; they do not claim
model judgment quality for a third repair round or every possible environment.

Earlier attempts remain visible. `.proofline/s4-live/first/report.json` records
both nested native-preflight failures (zero model dispatches; 4.726 seconds of
qualification work), without acceptance. The intermediate native trial at
`.proofline/s4-live/native/report.json` completed both original recovery controls
with nine dispatches in 856.751 seconds, before execution-map binding and the
separate-process delivery restart were added. Its interim schema-2 records are
not the final current-format acceptance evidence. In total, the two native
trials consumed **18 actual model stage dispatches**; their usage remains in
those receipts. No failures, earlier costs or S3 observations were replaced.

**S4's dependency gate is satisfied within this recorded local host and fixture
boundary.** Live product repair, evidence-only recovery and separate-process
resume are demonstrated; environment/stopping/budget edge cases have the stated
mechanical controls. Missing/uncertain host state still blocks honestly, and
portable resume, limit extensions, the separate P2P exit-2 reporting fix,
publication/merge and a broader repair-heavy pilot remain outside this slice.
