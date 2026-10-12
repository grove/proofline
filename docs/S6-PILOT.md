# S6 — Independent full-workflow pilot

S6 is an experiment, not a claim that Proofline is better. The executable pilot
compares four approaches on **20 distinct component-development requests**:
ordinary agent, ordinary agent plus one fresh review, current P2P, and Proofline.
All four use the same Sol model, task source, starting tree, public interface,
independent expectations, and authorized **local** delivery target. The separate
model experiment adds Luna alone and Luna with Proofline on those same tasks;
Sol's corresponding arms are reused rather than charged or counted twice.
There are **120 assignments** per repetition, with ten raw-request tasks and ten
shared-preplanned tasks per approach. Repetitions do not increase the number of
independent tasks.

## What is fixed before execution

`checks/s6_compare.py declare` creates a new private operator directory and an
immutable manifest before any task model is dispatched. It records the exact
model IDs and reasoning effort, task/evaluator bytes, runtime and P2P instruction
hashes, repository revisions, local target, budgets, concurrency, assignment
population, deterministic shuffled order, and optional declared token prices.
The Sol and Luna defaults are `gpt-6.1-sol` and `gpt-6-luna`; the initiating user
selected the Luna/Sol experiment. Model availability failures remain failures;
the runner does not switch models to obtain a better score.

Each disposable repository contains the existing two-module JSON CLI, a public
library seam, README and compatibility test. Requests cover Unicode validation,
stable pagination, quoted CSV, decimal invoice arithmetic, nested settings,
archive-path safety, interval union, dependency ordering, capped retry schedules,
UTC timestamps, URL query decoding, numeric versions, recursive redaction,
JSON pointers, expiring caches, atomic patches, event deduplication, sliding rate
limits, idempotent schema migration and atomic inventory batches. The last eight
are designated held-out before prompt tuning. These are unfamiliar component
fixtures, **not a representative sample of large production repositories**.

The evaluator's expected values are independently authored from the original
requests. It executes the candidate through the public CLI in Codex's native
sandbox with read-only inputs and separate scratch, checks return codes, JSON,
errors, version compatibility, unexpected output files and unchanged candidate
bytes. Separate public-library probes check error families and input immutability;
the large-CSV CLI probe uses a trusted launcher to populate the same JSON argument
without exceeding Linux's per-argument limit, and compares large output inside
the evaluator process to keep native receipts bounded.
Static import checks reject undeclared third-party dependencies. It never imports candidate tests as an answer key. **46 controls** must
first accept all 20 known-good candidates and three structurally different
alternatives, and reject all 20 defective seeds. A failed or unavailable control
blocks the task pilot. Raw receipts and every control remain private; workers
cannot read the operator repository, oracle, previous contexts or sibling P2P
executions under the existing qualified host boundaries.

## Four approaches and input accounting

The agent-alone arm uses its normal autonomous implementation and useful checks.
It has no independent reviewer or prover. Agent plus review adds one fresh
read-only reviewer; it does not inherit Proofline's targeted correction loop.
Both use the qualified native sandbox, with a minimal completion or review flag
and summary. They receive no Proofline criterion, binding, command-citation or
correction protocol. Native transport overhead is counted.

P2P invokes the **actual current delivery controller and stage packages** using
the S3-qualified native permission transport. The transport changes permission
configuration and explicitly declared model preference only; it does not
replace P2P's readiness, implementation, review, proof, diagnosis or recovery.
Raw requests first run P2P's current `plan-acceptance` guidance and protocol in a
fresh model invocation; that time, dispatch and usage consume the same episode
budget. The enclosing synthetic local benchmark has a source-preserving
planning mandate, not historical production approval or tracker authority.
Shared-preplanned arms receive the same frozen source-linked synthetic plan.
Plan authoring human time/cost is unknown and is never called free.

Proofline uses the existing production `deliver` path, independent review and
proof, current recovery and same cumulative limits. Raw briefs mechanically
index the already numbered source promises, with preparation time recorded.
Shared plans are guidance for the experiment's direct local promises; the pilot
does not invent an existing P2P approval or bypass S2 adoption for a customer's
contract. Accepted Proofline records are read back through `status` before
being scored. The independent evaluator decides whether acceptance was correct.

Every method receives 900 episode seconds by default. Agent alone gets the
whole episode for coding. Agent plus review reserves up to 240 seconds for its
fresh reviewer; its coding invocation gets the remaining allocation. P2P and
Proofline use 240 seconds per stage.
P2P and Proofline share twelve dispatches including preparation and recovery;
Proofline reserves 120 seconds for independent checking. P2P may make three
repairs within its same cumulative budget. Ordinary arms have one implementation
and at most one review, reflecting the approaches being compared. The main
pilot does not inject faults after implementation or force a predetermined
number of repairs. Natural omissions and regressions are judged from the fixed
source expectations, even when existing tests pass.

## Difficult recovery controls

`checks/s6_challenges.py` is a **separate diagnostic**, excluded from the natural
pilot's quality rates. Native workers and independent verifiers exercise:

- Two defective implementations followed by a third correct implementation:
  the first injected candidate violates behavior and version compatibility;
  the second retains the behavior defect but restores compatibility, establishing
  observable criterion progress; the third must receive fresh independent checks.
- Correct code with intentionally missing first-proof observations: a new proof
  must remedy the evidence gap on the unchanged binding with no implementation
  correction.
- A valid alternative implementation, plus deliberate post-check candidate
  drift that must invalidate saved acceptance.

Faults are host-injected before candidate freeze and explicitly recorded. These
show recovery mechanisms, not the coding model's natural failure probability.
These diagnostics declare 1,800 seconds per episode and 360 seconds per stage
before dispatch, allowing the deliberately added recovery work. They do not
alter the paired pilot's 900/240-second limits.
Their calls, usage and elapsed time remain visible separately from the paired
comparison. S4's existing budget, non-progress and separate-process recovery
checks remain binding.

## Measurements and decision

Every assigned task remains in the ledger: correct acceptance, false acceptance,
false blocking, failure, budget exhaustion, unavailable observation, interrupted
worker, or not executed. The JSON summary retains paired per-task outcomes,
preparation/delivery/end-to-end elapsed time, dispatches, native token categories,
role times, recovery, human intervention, success-only and all-attempt medians,
maximum delays, recoverable false rejections, and unknown measurement counts.
The call metric counts native stage dispatches. Internal provider request counts
are unavailable; reported native turn usage includes internal agent work.
End-to-end delivery time reaches the workflow's final candidate handoff; the
private evaluator then determines whether that delivery was actually correct.
Its additional observation time is recorded separately and in campaign wall
cost. The per-success ratios charge **all unsuccessful attempts** to satisfactory
deliveries. Cached input is already included in total input; it is not counted a
second time as tokens or charged again at the uncached rate.

The summary reports seconds/tokens/USD per satisfactory delivery and satisfactory
deliveries per workflow hour/per dollar. A workflow hour is summed episode time,
not parallel campaign wall time. USD is available only from prices explicitly
frozen with the declaration; it is a token-price estimate, not an invoice or a
claim to include unreported tool charges. Missing usage or prices stays unknown.
Automatic task execution records zero task-specific human interventions; common
corpus authoring, initiating preparation and unmeasured human attention remain
unknown. Shared-preplanned full-request cost stays unknown when plan authoring
is unavailable. None of these missing values becomes zero.

The 25% median-time-or-token target is tested separately by input mode on at
least ten distinct paired tasks. Faster failure cannot establish it: Proofline
must have no observed false acceptance, no lower satisfactory-delivery count,
and no more than the predeclared 10% terminal false-blocking rate. Success-only
medians additionally require the same successfully delivered task set. There is
no statistical superiority claim from one small host/corpus sample. Broader
correct deliveries per dollar and per hour matter more than the target alone.
A Proofline false acceptance stops new batches; already running bounded workers
finish and all remaining assignments stay visibly unexecuted.

The decision is driven by trust first: strengthen verification for false
acceptance, remedy or simplify chronic blocking, reconcile missing observations,
or reconsider overhead when no quality-gated advantage is demonstrated. Production
review/proof is not weakened by this experiment. The optional one-checker versus
two-checker experiment, new hosts and new publication infrastructure are deferred
until actual observations justify them.

## Reproduce

Use Python 3.11+ and the qualified macOS/Codex 0.162.1 host with existing
authentication. Host execution may be needed so the native sandbox can initialize;
never remove that sandbox to make a run succeed. No publication authority or
GitHub write is implied.

```sh
python3 -B checks/s6_compare.py declare \
  --p2p-repo /path/to/current/promise-to-proof \
  --output .proofline/s6/new-pilot --sol gpt-6.1-sol --luna gpt-6-luna
python3 -B checks/s6_compare.py run .proofline/s6/new-pilot
python3 -B checks/s6_compare.py summary .proofline/s6/new-pilot
python3 -B checks/s6_challenges.py --output .proofline/s6/new-challenges
python3 -B -m unittest discover -s tests -v
```

The initial campaign's uniform source-regression readback and study resource
report are reproducible without rerunning task models:

```sh
python3 -B checks/s6_regression_audit.py .proofline/s6/pilot-v4 \
  --output .proofline/s6/new-regression-readback
# Exit 2 means an observed Proofline false acceptance; inspect the retained report.
python3 -B checks/s6_results.py .proofline/s6/pilot-v4 \
  --readback .proofline/s6/final-regression-readback-v3/report.json \
  --preliminary .proofline/s6/pilot-v2 --preliminary .proofline/s6/pilot-v3 \
  --challenges .proofline/s6/final-challenges/report.json \
  --output docs/S6-RESULTS.md
```

`--jobs`, `--seconds`, `--stage-seconds`, `--dispatches` and `--repetitions` are
fixed at declaration, never extended after scoring. An optional `--rates rates.json`
file maps each exact model ID to USD-per-million `input`, `cached`, and `output`
rates. All categories must be finite nonnegative numbers. Unknown prices can be
left undeclared. A run never overwrites an existing task directory or silently
reruns a failure. Finished worker results can be collected after controller
interruption; uncertain workers require reconciliation before more dispatch.
Changed code, instructions, task keys, prices or assignment population reject
execution under the old declaration. Declare a new campaign and retain the old
one when a change is necessary.

The private `operator/manifest.json`, `report.json`, `summary.json` and
`results.md` contain the predeclaration, full ledger, metrics and human-readable
per-task findings. Raw native streams stay with their original role/runtime
records. Oracle inputs and model transcripts remain ignored local artifacts.
Only supported **local** targets are compared; PR/merge target coverage is
explicitly NOT EXECUTED, as this experiment has no remote effect grant.

## Actual observations

The corrected campaign stopped at its trust gate under
`.proofline/s6/pilot-v4/operator/manifest.json`. Earlier campaigns, source archives,
failures and resource consumption remain preserved. Two comparison defects were
corrected openly: raw P2P planning now uses its actual parser and planning mandate;
ordinary baselines now receive a minimal native completion protocol and their
full coding allocation. All affected method cohorts were repeated, including
failures; valid P2P/Proofline observations were retained by exact artifact hash.

The original CLI-only evaluator was amended uniformly to check the promised
public library and input immutability. A native independent reviewer subsequently
found the standard CSV reader's inherited field-size limit. The original source
sets no size limit and the original implementation accepts such fields.
`checks/s6_regression_audit.py` independently checks this concrete regression
across every CSV method/model. Another reviewer identified rejection of a valid
ISO-8601 ordinal date; the source did not narrow ISO-8601 to calendar dates.
[NASA's ISO-8601 reference](https://science.data.nasa.gov/fits/documentation/iso-time)
confirms ordinal notation. Uniform native readback preserves original scores,
corrects two false-block classifications, and exposes five false acceptances,
including one by Luna with Proofline. The pilot stopped new batches immediately
after that independent observation; bounded workers finished, leaving **69
executed and 51 unexecuted** assignments in the complete 120-case ledger.
These protocol amendments and carried observations limit causal inference.
No illustrative numbers become measured results. The [measured report](S6-RESULTS.md)
includes all preliminary trial resources separately from the qualified comparison.
The decision is **strengthen verification before expanding**. Neither the 25%
target nor a Luna-with-Proofline advantage is established by this stopped sample.

The long-version reviewer rejection was also confirmed by native readback:
5,000-digit numeric components exceed Python's default integer-conversion limit,
while the original source imposes no component-length limit. Both final Proofline
implementations passed that counterexample after correction. No observed terminal
false blocking remains; the six recoverable negative Proofline judgments were
also checked against preserved candidates, with no observed false rejection after
these adjudications. These remain finite-probe observations.

All three separately declared native recovery diagnostics passed. The third
implementation received independent acceptance; an evidence gap was resolved by
a new proof on the same binding with no code correction; the valid alternative
remained unchanged. Deliberate candidate drift invalidated saved acceptance in
all three cases. An incidental incomplete reviewer invocation and its unknown
usage remain charged in the diagnostic record.

The default evaluator now includes the large-field, ordinal-date and long-version
counterexamples, with adjusted reference controls. All 20 original task promises
remain byte-identical. **46 current controls passed inside the native read-only
sandbox**, and the final regression suite ran **144 tests, with two platform
skips**. Evidence is retained under `.proofline/s6/final-default-controls/`,
`.proofline/s6/final-native-tests.log`, and `.proofline/s6/final-challenges/`.
The task pilot was not resumed or rescored by new model runs after the trust stop.
