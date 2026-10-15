# Issue #52 phase 2 — controls observed; live cohort NOT QUALIFIED

The model-free qualification adapter is implemented. Native controls observed
all 12 expected outcomes, including a green-original-suite omission. Worker and
grader isolation and the real initial-S1 Intentline/Proofline round trip passed.
**Independent complete-source/cohort review remains pending.** Zero coding-model
turns were dispatched; all 16 coding assignments remain NOT_EXECUTED. These
observations measure qualification machinery, not intervention effectiveness.

| Provisional task | Reference | Local alternative | Deliberate defect | A | B | C | D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Feedback (#14) | probes pass | probes pass | probes fail | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| Promise mapping (#13) | probes pass | probes pass | probes fail; original suite green | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| Intentline adapter (#23) | probes pass | probes pass | probes fail | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| Next-check hints (#50) | probes pass | probes pass | probes fail | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |

The omission control passes **109 original tests, 7 opt-in skips** while the
withheld oracle detects its incorrect promotion of an unlinked requirement.
No ordinary-worker failure is observed, so the baseline spending gate has not
been attempted or passed. Whole-request correctness is UNKNOWN for controls;
finite probes and syntactically matching source clauses are not source review.
The alternatives are small equivalent rewrites, not independent whole-product
implementations; their fitness and complete oracle coverage require review.

## Exact evidence

[results.json](results.json) retains every slot, source/base/reference/control
identity, original suite argv/cwd and output, per-attempt process times, unknown
costs, blockers, archive hashes and every evidence member's SHA-256.

- [evidence.zip](evidence.zip): six preparation attempts, protected observations,
  failed canaries, actual test failures, real export, native receipts, check
  report, CLI status readback and regression log. No stopped attempt is erased.
- [source-v2.zip](source-v2.zip): exact completed native-host revision and
  Intentline producer bytes; overlay [source-v3-delta.zip](source-v3-delta.zip)
  for the completed control revision. Each recorded input hash is verifiable.
  Earlier developmental attempts retain input hash inventories and executed
  probes; not every overwritten transient authoring file was retained.

The raw report retains original absolute paths. Readback was observed at its
original location; extracting an archive is not a claim that path-bound native
receipts become a newly executed or relocatable check. Control trees are
reconstructible from pinned Git commits, original test blobs and exact patches.

Native host: macOS 26.6.2 arm64, Python 3.14.8 (resolved Homebrew executable),
Codex CLI 0.162.1. Fresh no-turn catalog readback observed Luna:medium support;
that availability is not a model dispatch or future availability guarantee.

## Retained preparation stops and overhead

| Attempt | Observed process seconds | Result |
| --- | ---: | --- |
| Offline v1 | 87.325 | 12 controls matched; stopped for input drift during authoring |
| Native controls v1 | 54.391 | stopped: original suite hit Apple Git shim; truncated evidence |
| Native host v1 | 40.925 | stopped: temporary-path reads allowed; absent Git-head fixture |
| Native controls v2 | 64.791 | 109 tests ran; one archival-history prerequisite failure |
| Native host v2 | 44.558 | worker/grader boundaries and producer/check/readback observed |
| Native controls v3 | 143.644 | all 12 controls matched; complete original suite green |

These process durations **overlap**; adding them would double-count elapsed
time. Complete preparation elapsed, organizer model tokens, active human time
and billed costs are UNKNOWN. No inference was dispatched by qualification.
Repository validation separately ran **285 tests in 179.770 seconds**, with
9 opt-in skips. Neither those tests nor control successes answer the hypothesis.

## Decision

| Added intervention | Decision | Reason |
| --- | --- | --- |
| Short checklist | INCONCLUSIVE | no coding episodes or comparative overhead observed |
| Proofline checks / #50 hints | INCONCLUSIVE | machinery and advisory readback work; delivery benefit unmeasured |
| Intentline contract/export | INCONCLUSIVE | supported round trip works; quality/time tradeoff unmeasured |

**Next smallest product/skill adjustment: no change.** Complete independent
source/control adjudication and resolve historical-solution exposure before a
separate live freeze and bounded authorization. No unseen holdout is triggered
by these machinery controls; if a later discovery cohort is promising, freeze
new unseen holdout tasks before adoption. See [phase-2 scope and remaining
gates](../../issue52/PHASE2.md). Issue #52 remains open; this PR does not claim
that its live-study prerequisites or empirical acceptance are complete.
