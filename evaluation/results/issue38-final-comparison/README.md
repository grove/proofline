# Final pragmatic Luna medium/high comparison — #38

**Recommendation: MEDIUM PREFERRED for similarly scoped coding work.** Across
the [two-task pilot](../issue38-two-task-pilot/README.md) and these two fresh
tasks, medium and high each delivered **3/4 supported correct candidates**.
Medium used **171.887s versus 250.901s** of full coding-attempt time, a **31.5%**
reduction, with lower combined input, uncached input and output totals. High
showed no correctness advantage: both efforts introduced the same compatibility
regression on Boltons. This is enough for the requested exploratory effort
decision. No further cohort, routing change, supervisor or mandatory verifier
is proposed. Actual monetary cost remains **UNKNOWN**.

This completes the requested four-paired-task exploratory comparison following
merged PR #61. It does not establish general reliability, statistical certainty,
or that medium is universally cheaper. The pilot's missing pytest coverage is
still a historical limitation; its two deliveries retain their original scoped
assessments. Neither #38 closure nor merge is authorized by this report.

## Two fresh tasks and matched execution

| Task | Exact original base | Why selected | Order |
| --- | --- | --- | --- |
| [Boltons #510](https://github.com/mahmoud/boltons/issues/510): preserve positional-only generated signatures | `4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d` | Shared formatter/builder/caller compatibility, defaults, mixed parameters, actual keyword collisions; implementation plus regression files | medium, high |
| [ItsDangerous #429](https://github.com/pallets/itsdangerous/issues/429): untimed loads must not silently ignore expiration arguments | `672971d66a2ef9f85151e53283113f33d642dabd` | Important negative behavior across serializer inheritance and runtime/static typing, while retaining timed loading | high, medium |

These are genuine public bug requests, not synthetic algorithm exercises. Neither
was used in previous Proofline coding evaluations. Possible public solution or
training exposure is UNKNOWN. Both yielded two-file changes; each production
fix stays in one shared module. These are moderate compatibility tasks, not
large cross-module architecture work. ItsDangerous's final code fix is one line;
its challenge is the negative contract and preserving the inherited timed API.
The complete unabridged requests, including the original code, are retained in
[requests/](requests/), with exact tracked baseline archives alongside this report.

On 2026-10-21, four fresh ephemeral Codex CLI 0.163.0 contexts each requested
`gpt-6-luna` at exactly medium or high, with **900 seconds per attempt**, including
self-checks. Each pair starts from identical Git tree bytes and receives the
same full request, guidance, dependencies and tools. Native prompt paths and
remaining-time text vary per slot. Each completed one native task turn; backend
request counts, exact backend identity and actual billing are UNKNOWN. No retry,
correction turn, effort escalation, worker grading feedback, delegated agent,
paid API or fallback was used. No budget was reached. Current user instructions
authorize these four attempts and draft PR publication.

The existing `checks.coding_attempt.run`, `evaluation.recovery.grader.invoke`
and `evaluation.source_preflight.qualify` were reused. No framework or product
code changed. The existing native profile adds only the dedicated dependency
directory **read-only**; assigned product/scratch writes, protected Git/source,
private/sibling denial, and disabled network/plugins/memories/delegation remain.
All four native boundary canaries and protected-input checks pass.

## Dependencies, checks and correctness

Before any coding attempt, ordinary dependencies were installed into a dedicated
temporary directory and exercised through the same native sandbox. Pytest
9.1.1 and freezegun 1.5.5 are available; Pyright 1.1.414 and its bundled assets
are available for the requested typing behavior. Versions, dependency hash,
Python 3.15.0, macOS 27.0.1 arm64 and canonical interpreter path are recorded in
[environment.json](environment.json). No global packages or network permissions
were changed. Both workers in each pair received the exact successful test
command and baseline limitations before coding.

ItsDangerous's baseline passes **297 tests**. Boltons's baseline passes **676
tests and 12 subtests**; two socket tests fail with PermissionError because
network access is disabled. Isolation was preserved. The complete baseline
receipts retain actual subprocess outcomes; a failed suite is not called green.

Source declarations and baseline/reference/alternative/defective controls were
frozen and qualified before dispatch. All eight final expected outcomes match.
The first no-model preparation pass needed two fixture corrections, retained
in `preparation-v1-controls.json` and explained in [acceptance.md](acceptance.md).
Crucially, later independent caller review uncovered a shared compatibility
regression also missed by the reference controls. The report does not equate
passing that limited qualification with complete semantic correctness.

| Task / effort | Independent assessment | Original suite on terminal candidate | Full attempt seconds | Task turns / tools | Input / cached input / output tokens |
| --- | --- | --- | ---: | ---: | ---: |
| Boltons / medium | Reproducer and 5 frozen cases pass; **introduced `injected=` regression** | 677 passed, 12 subtests passed; 2 baseline socket restrictions | 50.002 | 1 / 13 | 333,221 / 303,360 / 2,953 |
| Boltons / high | Same correct core fix and **same regression** | Same outcomes | 77.156 | 1 / 11 | 255,966 / 201,216 / 3,101 |
| ItsDangerous / high | **Supported correct**; 3 runtime groups and both typing checks pass | 298 passed | 83.576 | 1 / 17 | 236,540 / 205,696 / 3,430 |
| ItsDangerous / medium | **Supported correct**; same checks pass | 298 passed | 40.371 | 1 / 10 | 180,961 / 163,072 / 2,627 |

All four workers add regressions and run pytest. They self-test normally; high
also demonstrates Pyright's unexpected-argument diagnostic. Exact self-check
commands, outputs, intermediate failures and final handoffs are retained in
[results.json](results.json) and `execution-evidence.zip`. A later protected
Pyright check assesses both candidates identically. The same production change
is delivered by both efforts on each task; tests differ. No existing test was
deleted or weakened. All candidates remain exactly as handed off.

The Boltons review failure is concrete: after injecting the first of two
positional-only arguments, stale `posonlyargs` makes the remaining ordinary
`c` parameter positional-only. `wrapped(2, c=4)` works on the baseline and
raises TypeError on **both** candidates. The supplementary native reproducer
was discovered after medium's handoff and applied identically to both arms,
baseline and controls. It was not part of the frozen probe and was never fed
back to workers. [review.md](review.md) explains the affected documented caller,
the preflight coverage gap, and why this is an introduced compatibility defect.
Even restricting acceptance to the issue's exact reproducer would leave the
efforts tied and would not reverse the recommendation.

## Four-task decision and resources

| Combined observed measure | Medium | High |
| --- | ---: | ---: |
| Supported correct deliveries / assigned | 3 / 4 | 3 / 4 |
| Confirmed defective deliveries | 1 / 4 | 1 / 4 |
| Full coding-attempt seconds | 171.887 | 250.901 |
| Native coding-invocation seconds | 160.774 | 239.778 |
| Native task turns / completed tools | 4 / 49 | 4 / 65 |
| Total input tokens, including cached | 784,501 | 843,927 |
| Cached input tokens, subset of input | 643,456 | 690,432 |
| Uncached input tokens | 141,045 | 153,495 |
| Output tokens | 10,380 | 13,709 |
| Attempt seconds per supported correct delivery, including failed work | 57.296 | 83.634 |
| Input / output tokens per supported correct delivery, including failed work | 261,500 / 3,460 | 281,309 / 4,570 |
| Actual dollars / dollars per supported correct delivery | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN |

Every attempt remains in the denominator; no failed work is discarded. Cached
input is not added again. Cache-write input is zero; reasoning output (2,568
medium; 4,545 high) is already included in output. Medium saves 7.0% combined
input, 8.1% uncached input and 24.3% output. New-task totals are 90.374s medium
versus 160.732s high; medium uses **4.4% more total input on these two tasks**,
but 44.2% less uncached input and 14.6% less output. The pilot had the opposite
uncached-input direction. Cache mix and task/order/latency effects matter;
neither total input alone nor token totals establish an actual dollar saving.

Full attempt time includes snapshot preparation, native boundary preflight,
worker self-checks and terminal freeze. New native coding takes 82.009s medium
and 152.392s high. Additional protected grading takes **21.475s** total host
elapsed (**13.397s** child receipts) across all four, including repository tests
and typing. The five supplementary review commands add **2.150s** native elapsed.
The final complete no-model preparation pass takes **24.117s**, including
dependency-suite checks and controls. Dependency installation, the earlier
preparation iteration, source selection/review, organizer model work, active
human time and publication overhead are not fully metered and remain UNKNOWN.
This is not an all-in project-time or cost claim. Pilot overhead retains its
original reporting. Zero human interventions occurred within coding attempts.

Medium is faster on all four pairs, with equal observed source correctness.
The larger follow-up differences reinforce the pilot's small timing advantage;
high's extra time did not prevent the compatibility defect. Prefer medium as
the pragmatic starting effort for work like this. Keep the conclusion scoped:
four public tasks on one host, one attempt per arm, no reliability guarantee,
no broad Python-version matrix, and no automatic model routing. More research
is not required to make this exploratory decision.

## Evidence and validation

[protocol.json](protocol.json), [input-hashes.json](input-hashes.json), source
preflights, [controls.json](controls.json), [grades.json](grades.json),
[supplementary review receipts](supplementary-review-injected.json), and
[validation.json](validation.json) retain the source bindings and observations.
The execution archive contains four exact binary patches, tree manifests,
native prompts/receipts, boundary reports, command observations and the one-off
organizer scripts; reasoning text and duplicate raw journals stay local.
Baseline archives plus patches reconstruct all four candidate trees. Original
frozen input hashes and the read-only dependency digest remain unchanged.
Historical studies and production code are untouched. Refs #38; do not merge
or close automatically.
