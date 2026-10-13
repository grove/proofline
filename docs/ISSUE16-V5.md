# Completed matched study: delivery outcomes and optional stages

**All sixteen assignments observed; 4/4 correct deliveries in every arm.**
The [published report](../evaluation/results/matched-v5-20261013/README.md) retains
exact candidates, plans, native observations, costs and paired descriptive effects.
Planning added time/tokens without an observed correctness benefit; additional
stages remain optional. This completes the bounded empirical acceptance of #16,
with no general superiority or semantic completeness claim.

The [protocol](../evaluation/matched_v5/protocol.json) declares four unchanged
tasks × ordinary / Proofline-only / Intentline-only / combined arms. Every arm
uses the same pinned Sol catalog, host, agent allocation and total episode cap.
Planning stays inside one coding turn and consumes its budget. Requests, seed
bytes, independently derived finite oracle and all twelve behavioral controls
are unchanged. No correction, separate planner, audit, reviewer or adoption.

Native model/catalog/runtime drift, failed qualification, source/grader leaks,
unavailable check/grading execution and exhausted budgets still stop the study
with every missing slot retained. A deterministic rejection of a worker-produced
artifact is instead an observed failure. Planning-only advice cannot block a
correct product handoff. Combined rejects an invalid import, does not fall back
to unmapped checks, and records whether independently correct code was blocked.
It then continues to the next assignment; no failed assignment is retried.

The qualified export is explicitly initial revision 1 with only the original
S1 request; optional R links remain advisory and unlinked clauses never block.
Regression tests exercise invalid exports across all four arms and confirm
continuation and the absence of a combined fallback. Public artifact checks
independently reconstruct Git trees, verify prompt/source hashes and reconcile
source archives, native controls, receipt-bound candidates and all-assigned metrics.

[V2](ISSUE16-PREPARATION.md), [v3](../evaluation/results/matched-v3-20261013/README.md)
and [v4](../evaluation/results/matched-v4-20261013/README.md) retain their exact
stopped declarations, observed failures, missing slots and original source
archives. None resumes, replaces cases or contributes observations to this
fresh cohort. All stopped costs remain separately visible.

The user explicitly approved this fresh sixteen-assignment declaration before
live dispatch. The [archived approval](../evaluation/results/matched-v5-20261013/approval.json)
binds the original FREEZE.json bytes retained in the source archive. After all
sixteen observations and source archival, the active declaration was retired;
qualification/execution cannot retry or resume this completed study. The corpus,
oracle, prompts and actual native runtime remain exactly as archived. The only
later runner change reads the public results without any model dispatch:

```sh
python3.14 -B -m evaluation.matched_v5.study report
```

The report and artifact tests recompute all-assigned metrics and independently
reconstruct candidate Git trees. Unknown prices, initiating-agent/human costs
and backend revisions remain unknown. Sixteen observations across four fixed
tasks do not establish behavior on unseen requests or another model/run.
