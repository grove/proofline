# Live ordinary-agent baseline v1 — 13 October 2026

**All six assignments executed once; 6/6 independently correct deliveries (100%).**
Every worker completed its implementation handoff before independent evaluation.
There were 0 false acceptances, 0 unnecessary blocks,
0 failed implementations, 0 unavailable attempts and
0 unexecuted assignments. No candidate was repaired or rerun.
This completes the outstanding live observation for [issue #9](https://github.com/grove/proofline/issues/9).

| Metric | Observation |
| --- | ---: |
| Assigned / executed | 6 / 6 |
| Independently correct deliveries / assigned | 6 / 6 |
| Correct delivery rate | 100% |
| False acceptances / unnecessary blocks | 0 / 0 |
| Failed / unavailable / not executed | 0 / 0 / 0 |
| Total workflow seconds, all attempts | 533.928 |
| Seconds per correct delivery | 88.988 |
| Reported input tokens | 492,670 |
| Cached input subset | 357,760 |
| Reported output tokens | 15,242 |
| Input + output tokens per correct delivery | 84,652.0 |
| Unknown-usage coding dispatches | 0 |
| Operator candidate edits / extra worker messages | 0 / 0 |
| Human active effort / initiating-agent usage | unknown / unknown |
| Dollar cost | unknown; no authoritative rates frozen |

Cached input is already included in input. Reported reasoning output
(1,292 tokens) is a subset of output and is not added again.
Provider-internal request counts and an immutable backend model revision are
unavailable; the exact selected model and CLI version are recorded.

| Assignment | Outcome | Workflow seconds | Input | Cached subset | Output |
| --- | --- | ---: | ---: | ---: | ---: |
| 1. [collision-slugs](assignments/collision-slugs/result.json) | correct delivery | 70.700 | 73,055 | 39,936 | 2,254 |
| 2. [ordered-inventory](assignments/ordered-inventory/result.json) | correct delivery | 139.598 | 89,010 | 56,064 | 3,209 |
| 3. [half-open-union](assignments/half-open-union/result.json) | correct delivery | 71.728 | 85,214 | 68,096 | 2,374 |
| 4. [form-multimap](assignments/form-multimap/result.json) | correct delivery | 88.254 | 73,305 | 56,064 | 2,322 |
| 5. [largest-remainder](assignments/largest-remainder/result.json) | correct delivery | 84.325 | 85,994 | 68,736 | 2,581 |
| 6. [four-way-islands](assignments/four-way-islands/result.json) | correct delivery | 79.323 | 86,092 | 68,864 | 2,502 |

All frozen checks passed, so observed failed requirements and counterexamples
are empty. This does not imply there are no defects outside the finite probes.

## Execution and integrity

The original [protocol](../../v1/protocol.json), [FREEZE.json](../../v1/FREEZE.json),
source corpus, references, oracle and preparation ledger remain byte-identical
to `6c85055f3159dbc3f334442dd1d7e6782ece51f2` (PR #19).
The original ledger continues to describe preparation, not this later execution.
The historical S6 Git objects and `docs/BOUNDED-COMPARISON.md` were preserved;
[manifest.json](manifest.json) records their identities and the evaluator/runtime hashes.

Host: native macOS 26.6.2 arm64, Darwin 25.6.0, Python 3.14.8,
Codex CLI 0.162.1, `gpt-6.1-sol`, reasoning `high`, existing authentication.
The cached native model listing supported that selection; all six native turns
then completed successfully. No model substitution, retries, concurrent workers,
AI reviewer/prover, manual implementation correction or post-scoring repair occurred.
The six original requests and seeds were given only to their own ordinary workers,
with identical execution/handoff guidance and their original self-test recommendation.
The fixed [campaign adapter](../../live_v1.py) reuses the existing native transport;
it does not invoke Proofline's delivery/review workflow.

Limits remained 900 seconds per episode, 600 for coding (including preparation
and self-checks), 120 for independent evaluation and five per grader probe.
Each episode's coding receipt, workflow and evaluation durations are in its result.
All measured episodes and stages stayed within those limits. No timeout, capacity
failure, worker crash, unavailable grading or campaign stop occurred.

Both offline and protected native controls matched **18/18**: six references and
six materially different alternatives passed, and six defects were rejected.
Worker and grader-profile native canaries denied source/Git/receipt mutations,
private observations, the grader, repository and sibling candidates, credential-directory
model metadata and network access, while permitting scratch writes. The worker profile
additionally allowed product edits. Loopback was reachable outside the sandbox and
permission-denied inside it. Every assignment also passed a grading-profile preflight.
The initial nested tool-sandbox probe could not initialize `sandbox-exec`
(`Operation not permitted`); host execution initialized the native sandbox successfully.
Isolation was retained. That pre-dispatch diagnostic is hashed in the evidence index.

The coordinator kept expected outputs outside candidate processes. **Every** frozen
scorer invocation was replaced with native protected execution; no model candidate
used the offline unsandboxed subprocess path. Candidates were frozen even independently
of their handoff status. Full snapshots matched after grading, native workers reconciled
as finished, and the final frozen/runtime identities matched their declaration.
The grader is publicly committed, so this is not a permanently secret holdout.
Disabled network and external tools prevented workers from retrieving it here.

## Separate costs and interpretation

Workflow time starts with each assignment's seed preparation and preflight, includes
coding/self-checks and candidate freezing, and excludes retrospective independent grading.
All assigned attempts enter the six-task denominator and the resource totals.
Native coding stages consumed **531.364 seconds** within the
**533.928 workflow seconds**. Campaign wall time including grading and
integrity overhead was **563.800 seconds**.

Native qualification took **67.983 seconds**,
including **66.581 seconds** for controls
(432 processes; 61.999 summed process seconds).
Independent live grading took **19.822 wall seconds**
(144 processes; 19.652 summed process seconds).
The earlier trusted offline control pass took approximately 32.88 seconds; pre-dispatch
regressions took 31.515 seconds. Process time overlaps its enclosing stage/wall time,
so these figures must not be added twice. Earlier inspection, runner authoring,
reporting effort, human attention and initiating-agent tokens remain unknown.
These are study costs, separate from ordinary-agent workflow execution.

The ordinary agents delivered all six candidates before retrospective grading;
no additional Proofline verification was needed to obtain these observed deliveries.
Their autonomous implementations and self-checks worked on this modest population.
No failure mechanism or benefit from added assurance was observed in this baseline.
This is one repetition on six synthetic tasks, one model and one host, with finite
CLI/library/service and compatibility coverage. The task and oracle author is the
same study author; independence is from candidate implementations, not a second human.
Task contamination from prior public availability cannot be excluded. System libraries
and the complete OS are not archived. Four worker file searches returned exit 1 because no AGENTS.md matched; these
were ordinary no-match search results, not failed implementations or infrastructure errors.
No general reliability, universal source
correctness, statistical superiority or comparison with another workflow/model follows.
Any later matched arm must freeze its own version and preserve the original source,
starting bytes, model/host, budgets and grading controls as the original protocol requires.

## Reproducibility and retained evidence

[results.json](results.json), [resources.json](resources.json), [controls.json](controls.json)
and each linked assignment retain the observations and unknowns. Published candidate
files are exact bytes; their Git trees, original source/base identities, complete probe
observations, native invocation/thread IDs, settings, usage and completion status are
recorded. Machine paths in receipts use documented placeholders. Completion responses,
raw prompts, model streams and process receipts remain in protected ignored storage;
[evidence-hashes.json](evidence-hashes.json) identifies those local artifacts without
publishing private transcripts or authentication data.

Validation passed: 58 local deterministic tests (six native opt-in tests skipped),
including candidate Git-tree reconstruction, published hash/accounting reconciliation,
sandbox-only grading guardrails and rejection of campaign retries. The actual live
native controls and all six candidate evaluations ran separately. Whitespace and
relative documentation links were checked.

Safe deterministic identity/accounting checks (no models or candidate execution):

```sh
python3 -B -m unittest discover -s tests -p test_live_v1_results.py -v
python3 -B evaluation/v1/benchmark.py controls  # bundled trusted fixtures only
python3 -B evaluation/v1/benchmark.py report    # original preparation stays unexecuted
```

Regrading published candidates requires a newly qualified native boundary. Copy each
candidate into clean worker-only `inputs/product`, retain its bytes/modes, and keep
published scores, the repository, oracle and private evidence outside its read allowlist.
Use the protected `grade` adapter with the frozen scorer; never execute candidates via
the offline control harness. The one-shot campaign refuses retries/resumption. These
records are the original pass, not authorization for another model campaign.
