# Stopped matched v3: two observations, fourteen missing assignments

13 October 2026. **Empirical acceptance INCOMPLETE; no paired effects or
efficacy decision.** All sixteen slots remain in [results.json](results.json).
The ordinary and Proofline-only atomic-transfer assignments each delivered
correctly at the frozen finite seams. No planning arm executed. This does not
establish complete semantic correctness or a marginal benefit for either tool.

Before dispatch, the native worker/grading boundaries, all twelve unchanged
reference/alternative/green-but-incomplete controls and real producer → adapter
→ check/readback passed. Qualification took 67.253 seconds, separately from
delivery episodes. The two episodes took 144.525 and 132.181 seconds; reported
input/cached-input/output tokens were 78,204/58,112/3,767 and
80,278/41,728/4,497. Cached input is a subset, not additional tokens. There were
two native coding invocations, twenty observed agent tool executions, two
selected check processes, no manual candidate edits or additional worker
messages. Independent grading took 11.371 seconds. Dollar costs, initiating
agent usage, active human attention and provider-internal calls are unknown.
See [resources.json](resources.json) for separate process/wall accounting.

The selected local model-catalog entry changed after the first assignment;
the second was already running when that change was detected. The coordinator
retained its observed result, then stopped under the frozen drift rule.
Only the original catalog hash was retained, so exact changed fields cannot be
reconstructed. The selected `gpt-6.1-sol` slug and `high` reasoning remained
available; this is not evidence of an unavailable model or isolation breach.
[drift.json](drift.json) records both hashes. Fourteen missing runs were not
replaced, retried, resumed, counted as successes or pooled into another study.

[manifest.json](manifest.json), [qualification.json](qualification.json) and
[controls.json](controls.json) retain the original declaration and native
observations. [frozen-source.zip](frozen-source.zip) retains the exact original
runner, dependencies, protocol and tests so a squash merge cannot erase their
provenance. Active v3 execution is retired. Candidate bytes/modes, original
prompts, bounded grader observations and check feedback are retained for the
two executed assignments. Missing slots retain source/base identities and seed
bytes for reproduction; their seeds are not deliveries. Raw transcripts remain private;
[raw-evidence-hashes.json](raw-evidence-hashes.json) binds their original bytes.

**INCONCLUSIVE:** keep existing checking, planning and mapping optional. No
new mandatory planner, reviewer, audit, adoption or correction stage follows
from these two observations. The v2 preflight remains separately visible.
