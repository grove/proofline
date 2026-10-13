# Fresh matched declaration with a frozen native model catalog

The [protocol](../evaluation/matched_v4/protocol.json) and [freeze](../evaluation/matched_v4/FREEZE.json) declare four unchanged
requests × four arms, one turn per assignment, identical model/host and time
allocation, no extra planner/reviewer, no retries or correction turns. Planning
and exports consume the same coding budget. Original requests, independent
finite oracle, valid-alternative/green-but-incomplete controls and source pins
reuse the v2 corpus unchanged. The stopped v2 and [v3](../evaluation/results/matched-v3-20261013/README.md)
denominators and failures stay separate; no results are pooled.

Every native coding invocation explicitly loads [model-catalog.json](../evaluation/matched_v4/model-catalog.json)
through `model_catalog_json`, instead of the mutable host cache. The selected
catalog entry, tool instructions and CLI bytes are hashed. A read-only native
`model/list` query successfully loaded this exact catalog without a task or
model dispatch. This cannot freeze an unexposed backend weight revision.

Preparation is authorized by the user's continuation request. Execution requires
explicit approval of this fresh sixteen-slot declaration because the issue's
twenty-four-assignment limit does not authorize accumulating multiple declared
cohorts. The private approval must bind the exact FREEZE.json SHA-256; absence
or mismatch prevents any dispatch. No original stopped cohort can resume.

Native host commands (Python 3.14.8, macOS 26.6.2, Codex CLI 0.162.1):

```sh
python3.14 -B -m evaluation.matched_v4.study qualify
python3.14 -B -m evaluation.matched_v4.study execute
```

Qualification is a one-shot no-model preparation: native coding/grading boundary,
all twelve behavioral controls and real Intentline export → adapter → check →
readback. Execution additionally needs the declaration-bound approval in ignored
study storage. No missing exports, unavailable observations or protocol drift
are replaced by ordinary checks or retries. Retain every missing assignment.

Raw receipts remain in `.proofline/issue16-matched-v4-20261013/`. Any later public
report must retain source/candidate/prompt identities, exports, bounded native
observations, reported usage, all-assigned outcomes, paired descriptive effects
and separate authoring/control/grading resources. Four tasks do not establish
general superiority or semantic completeness. No mandatory product action is
justified by preparation or the two stopped v3 observations.
