# Issue #52 Phase 3 follow-up — NOT QUALIFIED

Four source-pinned Click/Arrow requests now form a **preparation shortlist**,
including one straightforward documentation task. Their original Python suites
run. Supported native isolation, actual new-oracle exclusion, and the existing
Intentline/Proofline S1 round trip were observed. One new behavioral-control set
discriminates a green-suite omission. **Independent semantic review and the
other three task graders/controls are incomplete. No live study is authorized.**

| Preparation candidate | Starting commit | Qualification evidence | A | B | C | D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Click #3362](https://github.com/pallets/click/issues/3362), usage hyphens | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` | two positive controls pass native probes; deliberate omission fails with original suite green; semantic review pending | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| [Click #2992](https://github.com/pallets/click/issues/2992), usage metadata | same Click commit | dependency health observed; field/interface adjudication and validated controls pending | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| [Arrow #1287](https://github.com/arrow-py/arrow/issues/1287), shift keyword docs | `2224255c4acc594d734cef0bbc83360452a67983` | small control; original suite green; rendered-doc review/build and controls pending | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| [Arrow #1293](https://github.com/arrow-py/arrow/issues/1293), timezone fallback | same Arrow commit | original suite green; new API/precedence adjudication and independent oracle/controls pending | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |

These are new **proposed** slots, not replacement observations or assigned live
episodes. The historical Phase 1/2 sixteen-slot ledger and all published earlier
studies remain unchanged. There are zero ordinary-A deliveries to grade; the
A-first spending gate has neither been attempted nor passed. Constructed
defects do not count toward its two independently confirmed material failures.

## Sources, task fitness and semantic limits

[candidate-cohort.json](../../issue52/candidate-cohort.json) pins full request
blobs, original API captures including discussion, commit/tree identities,
proposed order and all sixteen NOT_EXECUTED cells. [COHORT-REVIEW.md](../../issue52/COHORT-REVIEW.md)
inventories draft obligations, acceptable alternatives and unresolved decisions.
No upstream issues, comments or PRs were created or changed.

The six original replacement requests were re-read: all remained open, their
captured title/body bytes matched, none had comments, and all pinned repository
commit/tree identities still matched. Three P2P requests remain dependent on
real native/performance evidence; Lore billing remains deferred and lacks
attributed billing inputs.

After the user installed OpenJDK 21, Exmeso's original Maven build failed at its
Java 1.6 compiler target. Without modifying the repository, the declared
`-Dmaven.compiler.release=8` setting let 3 core, 13 Jackson and 3 Kryo tests pass.
The complete reactor timed out at 180 seconds in MessagePack. No orphaned
Exmeso surefire process was found afterward. The full suite, task oracles and
native dependency environment remain unqualified; these bugs were not forced
into the new shortlist.

A wider bounded search covered eleven additional Grove trackers and eleven
public Python repositories. Evidence includes issue/PR metadata and explicit
exposure exclusions: Boltons #581/#565/#553/#551/#566 have prepared PRs;
Humanize #438/#366 and Dateutil #1591/#1611/#1432 have public fixes; Pydash
#289/#290/#308/#313 and SortedContainers #219 have open implementations;
Cachetools #417 already has a tested upstream development solution;
More-itertools #1268 was already merged, #1332 has a prepared fix, and #1315
supplies implementations and reserves the work to its author. Click #3652 has
unsettled maintainer semantics; #3886 was declined by a maintainer. We did not
read or fetch those solution branches into worker inputs. Public-source/model
training exposure for the selected requests remains UNKNOWN.

The [16 historical review questions](../../issue52/REVIEW-ASSESSMENT.md) were
assessed against current source, tests and actual native evidence. Some already
have partial engineering coverage. None was self-approved; the separate
reviewer name and attestation remain null. No source quote, passing test,
successful control or UNKNOWN coverage label certifies whole-source correctness.

## New oracle/control observations

The withheld `usage_tokens` probe accepts different line layouts and two
different wrapping implementations. Exact [patches and hashes](../../issue52/fresh-controls.json)
reconstruct each control from the pinned Click base. Native observations:

| Control | Finite behavior probe | Unchanged original default suite |
| --- | --- | --- |
| Original Click base | rejects avoidable hyphen splitting | 2,261 passed; 25 skipped; 31,000 default stress deselections; 1 xfailed |
| Reference control | passes | same suite result |
| Alternative control | passes | same suite result |
| First-layout-only defect | rejects second-layout splitting | same suite result |

Both positive implementations and the negative control were authored during
preparation, separately from any worker (none exists). They are **not independently
attested correct complete deliveries**. The original suites ran as trusted
control subprocesses outside the native sandbox; the withheld probes ran
through the existing protected native adapter. Stress tests were deselected by
the project's original default configuration, not removed by this experiment.

Authoring attempt 1 had a src-layout import error and a `Popen` argument error;
its failures are invalid evidence. Attempt 2 rejected both positive controls
because the oracle required an overlong token to fit an insufficient width.
That unsupported expectation was rejected. Attempt 3 uses tokens that fit on
fresh continuation lines and matches all four finite outcomes. All attempts
are retained; this is oracle authoring before workers, not retries of coding
assignments. `usage_metadata` is an unvalidated draft only; Arrow's remaining
grading requires independent interface/documentation adjudication.

Arrow's full original suite passed **1,902 tests** with its original coverage
gate. Click initially could not collect because distribution metadata was not
installed; after installing its exact pinned package it passed as above. Both
the failed collection and successful execution are retained. Disposable Python
dependency versions, Java/Maven build output and exact commands are archived.
Docs rendering and fully isolated task-dependency exposure have not been
qualified. Installed package copies must not leak into future worker contexts.

## Supported host observations and retained stops

Host: macOS 26.6.2 arm64, Homebrew Python 3.14.8. The installed default Codex is
0.163.0. Its worker/grader canaries passed, but the check round trip correctly
stopped at the existing **0.162.1** version guard; no guard was relaxed.

A retained local Codex binary has SHA-256
`74c6a6d263f40d65f99c27a815275f5b4ed0bcc2baecc396b4cf3255498bdfc0`,
exactly matching Phase 2's 0.162.1 receipt. A disposable executable copy was put
first on PATH. The only runtime change makes qualification honor the discovered
binary consistently in catalog, both role profiles and round-trip producer
commands; the old default remains unchanged for other callers.

- Supported-binary worker and grader canaries passed: candidate writes allowed
  only to the worker, protected input/receipt/oracle/sibling reads and network
  denied, private evidence unchanged.
- Additional canaries denied the **actual new oracle, both positive-control
  patches, source inventory, cohort file and sibling observations** to both
  profiles. These are finite process checks, not general external-tool proof.
- The real initial-S1 revision-1 Intentline prepare/propose/check/render/export,
  Proofline import, two selected checks, and public `status --show-source`
  succeeded. The source remained intact; unlinked R rows stayed NOT DEMONSTRATED
  and overall coverage stayed UNKNOWN.
- Supported-binary catalog initialization timed out at 60 seconds. A separate
  bounded 120-second diagnostic observed Luna:medium support after **72.223
  seconds**, with no thread/turn. The stopped directory was not resumed.
  Actual completed-inference access remains UNKNOWN; this preparation does
  not authorize a turn to test it.

The hard-coded-path correction touches only the existing qualification adapter
and shared round-trip helper. No new coding runner, model reviewer, controller,
semantic prover, benchmark framework or mandatory delivery stage was added.

## Evidence, validation and next action

[results.json](results.json) contains hashes for every member of
[evidence.zip](evidence.zip), exact control trees and decisions.
[runtime-overlay.zip](runtime-overlay.zip) preserves the relevant runtime
changes and actual Intentline producer bytes over Proofline commit
`45a23160102e9e1ba1a4915165b29883721b997e`. Execution scripts and actual probes
for all three authoring revisions are retained. The overlay's `final/` entry
records the subsequent binding of the historical control grader to the same
selected binary; a further native probe verifies that exact receipt argv.
Reconstruct controls by
fetching the pinned Click commit and applying the named patch; run the archived
native adapter script with the supported binary. Do not overwrite output or
claim that extracting path-bound receipts re-executes them. Exclude every
evaluator artifact from worker input snapshots and deny reads to this checkout.

Validation passed: **291 tests, 9 opt-in skips** in the full repository suite;
after the final path-binding and archive regressions, **20 focused Phase 3,
Phase 2 and recovery tests** also passed, as did all **3 fixed oracle controls**.
Native observations supplement CI;
Linux CI does not qualify the macOS execution boundary. Per-process times are
retained, but overlapping durations are not summed. Complete preparation
elapsed time, organizer tokens, active human time and actual billed costs stay
**UNKNOWN**. Study-model dispatches: **0**.

**Readiness: NOT QUALIFIED. Next action:** a separate qualified reviewer must
adjudicate the complete four-request inventories, API choices and control
fitness. Finish the remaining three task graders/controls and docs/native
dependency qualification. Exclude or replace a candidate before any freeze if
it cannot qualify; do not shrink its request to keep four tasks. Then freeze
the exact qualified cohort, oracle/control/runtime/catalog hashes, permissions,
order and equal episode budgets, and obtain separate explicit live authorization
bound to that freeze. Until then, every A/B/C/D slot remains NOT_EXECUTED.

Checklist, Proofline hints/checks and Intentline interventions all remain
**INCONCLUSIVE**. The smallest justified product/skill adjustment is **no
change**. If a later discovery cohort is promising, predeclare fresh unseen
holdout tasks before adoption. Do not merge this preparation PR.
