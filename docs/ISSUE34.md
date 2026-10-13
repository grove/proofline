# Issue #34 — recovery comparison

The [fresh declaration](../evaluation/recovery/README.md) is implemented and
native-qualified, with **zero live model dispatches**. Its [preparation evidence](
../evaluation/results/issue34-preparation/README.md) retains all 24 assigned cells
as `NOT_EXECUTED`. Live execution awaits the fresh spending approval explicitly
required by [issue #34](https://github.com/grove/proofline/issues/34).

Freeze: `e6cd153ae5582fcbba5c7639b0f8e67fdb6ab09037376f19e67b44e6def5f2b9`.
The complete issue text, six source requests, source-grounded probes, hidden
oracle, seeds, controls, prompts, runtime code/binaries, models, host, ordering,
budgets and stop rules are hashed before any live dispatch.

- A is ordinary Luna:high. All six A cells execute and receive hidden grades first.
- With fewer than two defective A candidates, stop as a correctness ceiling pilot;
  keep all 18 B/C/D slots unexecuted and claim no recovery effectiveness.
- Otherwise run all remaining cells. B uses ordinary protected commands; C uses
  optional model-free Proofline check/receipt feedback; D adds Sol:high diagnosis
  only after the same validated public assertion failure.
- B/C/D get one correction maximum on the original Luna thread. Private grades,
  reviewer claims, unavailable checks and green probes cannot trigger it.

Maximum live expenditure is 24 primary assignments, 48 native turns and 28,800
seconds. Every arm has the same 1,200-second total limit; B/C/D have matched initial
and correction limits. No planner, production router, normal-workflow change,
correction-policy expansion, integration requirement or new dependency was added.
PR publication is requested; merging remains unauthorized.

## Observed qualification

All **24/24 controls** matched offline and under the native protected command
boundary: six correct, six alternative, six probe-detected defects, and six hidden
defects with green public probes. All controls pass their original repository
tests. B/C agreed on **12/12 correct/defective pairs**, including identical repair
eligibility on the exact candidate. Fresh worker/reader canaries denied unrelated
files, Git metadata, receipt writes and network access with the expected candidate
write permissions. The reused #32 staged same-thread control qualifies machinery
only; it contributes no natural recovery observation and no new inference.

The initial `proofline-check` usability exercise against this agent-built change
was unavailable because the Proofline repository has unsupported directory
symlinks. An isolated agent-built repository fixture was then unavailable inside
the tool sandbox; running it on the host passed the selected test with **zero
models**. These are documented observation/host boundaries, not reproducible
production defects requiring broader file or sandbox permissions.

Preparation took **14.95 seconds**, and fresh native qualification **98.18
seconds**, including all fresh controls and B/C comparisons. The archived
usability and exploratory native receipts retain additional development/setup
execution costs separately; those are not primary assignment outcomes. Test-suite
execution is separate implementation validation. Total authoring time/tokens,
active human time and actual billing remain **unknown**; probes are not free.

## Limits and next decision

Implementation validation: **241 tests passed**, with eight native opt-in tests
skipped. Fresh macOS qualification was executed separately. Archive hashes and
every frozen source byte were revalidated; historical #16/#32 files are unchanged.

No initial/final delivery grades, recovered natural defects, paired benefits,
reliability improvement, dollar costs or monetary savings have been observed.
The recommendation for Proofline and selective Sol is **INCONCLUSIVE** until a
live cohort or the predeclared baseline early stop is reported. Preparation does
not meet issue #34's live definition of done; the issue must remain open.

The tasks are representative synthetic Python repositories rather than sampled
production issues. The oracle is finite and single-agent-authored; alternative
controls share validation and are not independent human replication. All live
comparisons are conditional on the baseline gate, six fixed tasks and one
repetition. Preserve these limitations even if every live cell is correct.
