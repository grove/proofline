# Sol-guided Luna: prepared, empirical acceptance incomplete

Issue [#32](https://github.com/grove/proofline/issues/32) asks whether selective
Sol planning/verification enables Luna to approach Sol implementation quality at
a lower **total cost per independently correct delivery**. This change implements
the five-arm runner and freezes twenty assignments. **No live task or model
handoff has run. There are no measured correctness gains or monetary savings.**
The issue must remain open until its empirical acceptance is genuinely met.

The local native probe failed with `sandbox-exec: sandbox_apply: Operation not
permitted` (exit 71). Loopback qualification was also unavailable in this
restricted environment. The native app-server catalog readback could not obtain
a `model/list` response. Existing authentication was reported as available;
neither that nor cached catalog metadata qualifies live access. No unprotected
fallback, model substitution or reasoning change is permitted.

The [protocol](../evaluation/sol_luna/protocol.json),
[freeze](../evaluation/sol_luna/FREEZE.json),
[preparation evidence](../evaluation/results/issue32-preparation/README.md), and
[runner](../evaluation/sol_luna/study.py) are separate from the completed
[#16 / PR #31 study](../evaluation/results/matched-v5-20261013/README.md).
All its frozen files, results, failures and source archives remain unchanged.

That study delivered 4/4 in every Sol-implementation arm, a correctness ceiling:
Intentline-only and combined added 72.9% and 89.1% episode time without an
observed gain. Its earlier catalog drift and invalid worker-export failures
motivate this pinned catalog and the distinction between infrastructure stops
and scored advisory failures. The new tasks and fresh Sol-only arm avoid pooling
that easy baseline into the Luna comparison.

## What is prepared

| Arm | Implementation | Additional stages |
| --- | --- | --- |
| A `luna` | GPT-6 Luna:high | Normal tests/self-checks |
| B `plan` | GPT-6 Luna:high | Sol:high advisory Intentline plan |
| C `verify` | GPT-6 Luna:high | Actual Proofline checks, fresh Sol:high source review, at most one qualified Luna correction |
| D `hybrid` | GPT-6 Luna:high | Sol plan plus C's verification/correction |
| E `sol` | GPT-6.1 Sol:high | Fresh normal tests/self-checks reference |

Exact IDs are `gpt-6-luna` and `gpt-6.1-sol`, both at `high`. The pinned local
catalog lists support for these settings, as do the official
[Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and
[Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) documentation.
Native `model/list`, isolation and the separately authorized handoff must still
succeed before dispatch. The provider's backend weight revision is unobservable.
Every invocation supplies the pinned catalog and explicit reasoning setting.

Four new tasks target plausible omissions beyond a green example suite:

| Task | Main traps and independently observed obligations |
| --- | --- |
| Idempotent ledger | Conflicting/invalid replays, intermediate overdrafts, replay ordering, ignored extra keys |
| Path router | Precedence, split before strict UTF-8 decoding, decode once, encoded slash, empty wildcard tails, unused invalid routes |
| Stable scheduler | Simultaneous completions, original-order readiness, immediate zero-duration completion, worker reuse, disconnected cycles |
| Tiered invoice | Graduated prices, exact large integers, aggregate half-up rounding, remainder ties, repeated rows, unused invalid tiers |

All include batch, error/input immutability, extra keys and exact CLI compatibility.
The public tests cover only simple examples. Two immutable public assertions per
task expose an ordinary case and the **original request's explicit example** to
every arm. The other literal grading vectors, expected outputs and controls stay
outside all worker read permissions. Sol never receives independent grading
results, even during correction. Model-authored tests and claims cannot grade
their own outcome.

Seventeen offline controls passed: four reference and four alternative
implementations were accepted; four algorithm defects, one JSON-type defect and four missing-batch
implementations were rejected despite green public suites. Native controls remain
unqualified. Exact JSON type checks reject float-for-integer outputs accepted by
Python equality. This establishes a finite grader control, not correctness on every
possible input or an empirical model result.

## Reuse and trust boundaries

The runner calls the existing `coding_attempt.run`, candidate capture/freezing,
`codex_live.run_stage`, native isolation canaries, `local_run.check`/`inspect`,
Intentline exporter/strict adapter and `actionable_failure` APIs. Historical
grading/canary modules have fixed corpus globals and hash-pinned source. The
small adapter loads them into separate namespaces bound to this corpus; it does
not change their historical bytes or copy their grading/execution implementation.
No production CLI, mandatory stage, dependency or orchestration service is added.
`proofline.py check` remains model-free.

Planning uses one Sol pass through the pinned existing Intentline skill and
offline prepare/propose/check/render/export interfaces: only S1, schema 1,
initial revision 1. Its source identities, proposed oracles, constraints and
gaps remain advisory. Invalid worker advice is retained and scored; it cannot
stop remaining assignments or create a product handoff blocker. Both verifying
arms predeclare direct checks even if an optional plan import fails.

Sol verification gets the complete original source, actual frozen candidate,
captured original-to-candidate diff, and receipt-bound check observations.
Plan metadata is removed from the verification view. Findings require literal
source citations. Review judgments, newly proposed probes and missing coverage
are advisory. Only current executable Proofline results gate C/D handoff.

Correction is deliberately conservative. It requires both the existing strict
receipt validation and failure of immutable public check 0 on the exact candidate.
Failures only in candidate-authored tests, speculative findings, private grades,
unchecked expectations, timeouts or missing/unavailable checks do not qualify.
The original Luna thread gets one attempt with original source and native failure
evidence and any source-cited Sol diagnosis linked to that failing public check,
still marked advisory. The new candidate is frozen, all checks rerun, and independently graded.
Initial and final candidates/checks/grades remain separate. A real defect outside
this narrow repair oracle may remain uncorrected; do not silently expand it after
seeing results.

## Budgets, measurements and interpretation

Each assignment has the same 900-second total deadline, including setup, model
tools, Intentline export, Proofline, freeze/readback, corrections and independent
grading. A shared 600-second model allocation includes all Sol/Luna stages.
Planning and verification cap at 120 seconds each; correction at 180. Verifying
arms reserve 240 model seconds before implementation. Unused planning time
returns to implementation, and an unnecessary correction is never dispatched.
Token/FLOP caps are not enforceable through this native transport; equal wall
budgets must not be described as identical compute. The serial arm order gives
each arm four distinct positions; four tasks cannot fill a five-row Latin square.

Receipts retain actual native input/cached/output tokens, model settings, prompts,
tool executions, stage time, check overhead, correction time and total assignment
time. Cached input is a subset, never an additional input charge. Native turns
are distinct from unexposed provider-internal calls. Failed activity and missing
slots stay in the denominator and cost record. Initial/final independent grading
is also reported separately; unchanged finals reuse their bound initial grade.

Dollar cost remains **unknown** without reliable native billing and compute
charges. Public API token rates are not actual Codex subscription spending.
Reports therefore retain null total dollars and null dollars per correct delivery;
they may compare observed seconds and usage but cannot claim monetary savings.
Study preparation, qualification, initiating-agent usage and active human attention
are separate overhead; unmeasured quantities remain unknown.

Paired reports cover planning, the verification package, their interaction,
hybrid versus fresh Sol, and Luna versus fresh Sol, both initially and after repair.
Four-task bootstrap intervals are descriptive; a zero interval at a correctness
ceiling cannot rule out effects on unseen tasks. These arms identify **checks +
Sol review + eligible correction as a package**; they do not identify each
component's separate causal benefit.

| Capability | Current recommendation |
| --- | --- |
| Optional Sol planning | **INCONCLUSIVE**; no live evidence, preserve opt-in |
| Optional Sol verification | **INCONCLUSIVE**; no live evidence, preserve opt-in |
| Proofline checks | **INCONCLUSIVE** about incremental model correctness; retain existing model-free optional checks |
| Bounded Luna correction | **INCONCLUSIVE**; simulated flow is tested, native handoff unqualified |
| Luna:medium / Luna:xhigh follow-up | Neither justified by preparation alone; both require a separate frozen and authorized study |

If high is sufficiently reliable and total billing is measurable, medium is the
next cost-reduction hypothesis. Xhigh is worth considering only for observed
high-effort defects or costly repairs. Neither belongs in this primary cohort,
and neither is authorized here.

## Reproduction and authorization

Offline, with Python 3.11+:

```sh
python -B -m unittest tests.test_sol_luna -v
python -B -m evaluation.sol_luna.study controls
python -B -m evaluation.sol_luna.study report
```

On the frozen native host, `qualify` is a one-shot **no-model** preflight. It
retains twenty identical-per-task seeds and their identities, verifies exact
host/runtime/catalog, worker and reader isolation, all seventeen native controls,
and the existing producer/export/adapter/check/readback path.

```sh
/opt/homebrew/bin/python3.14 -B -m evaluation.sol_luna.study qualify
```

Live dispatch additionally requires **explicit user authorization** for this
exact freeze, twenty assignments plus at most four handoff-control calls, max
48 native turns and 18,360 seconds of assigned live work. Dollar billing is unknown.
The ignored `.proofline/issue32-sol-luna-high/approval.json` records `study_id`,
`freeze_sha256`, `max_native_dispatches: 48`, `max_seconds: 18360`, and the literal
`user_authorization`. A file records the actual authorization; it cannot create
authorization or authenticate its author. Preparation/PR publication is not
model-spending permission.

```sh
/opt/homebrew/bin/python3.14 -B -m evaluation.sol_luna.study execute
/opt/homebrew/bin/python3.14 -B -m evaluation.sol_luna.study bundle --output /new/evidence/directory
```

Before the twenty assignments, the authorized four-call disposable handoff tests
Sol plan → Luna staged defect → actual failing check → Sol original-source review
→ same-Luna correction → freeze/recheck. It exposes no primary task or private
grading data and is never counted as a successful delivery. Its failed/successful
costs are retained separately. A local bundle archives source, model catalog,
producer bytes, raw receipts and candidates; it never publishes by itself.

This declaration has stopped during preparation in the current environment.
There is no replay, retry, denominator reset, oracle repair or silent cohort
replacement. A repaired native environment needs a separately frozen and
authorized fresh declaration. Do not merge the PR or close #32 on preparation.
