# Final matched declaration: distinguish worker failures from infrastructure

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

Live execution requires explicit approval of this new sixteen-assignment
declaration, bound to the exact [FREEZE.json](../evaluation/matched_v5/FREEZE.json)
hash in private study storage. Preparation alone makes no benefit claim and
does not resolve #16. Native commands, once qualified and approved:

```sh
python3.14 -B -m evaluation.matched_v5.study qualify
python3.14 -B -m evaluation.matched_v5.study execute
```
