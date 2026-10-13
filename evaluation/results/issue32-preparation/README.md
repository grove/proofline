# Issue #32: preparation only — empirical acceptance incomplete

This is a fresh, frozen four-task × five-arm Luna:high study. **Zero model
calls and zero primary assignments ran.** No correctness-rate, latency, token
usage or dollar-saving comparison is available. Issue #32 remains open; the
completed #16 cohort and its archived bytes are unchanged.

The 2026-10-13 no-model qualification stopped at **`Native pinned model/list
unavailable`** after 18.797 seconds. The pinned catalog contains the exact
`gpt-6.1-sol:high` / `gpt-6-luna:high` configurations, but native readback produced
no RPC response within its 15-second limit. Its stderr reports PATH alias creation
was not permitted. Cached metadata does not establish usable model access.

The separate native host probe records `sandbox-exec: sandbox_apply: Operation
not permitted`, exit **71**, with boundary **NOT VERIFIED** and loopback control
unavailable. Existing authentication was available. No unprotected fallback or
model substitution was attempted. The model handoff, native behavioral controls
and live study remain unqualified. Explicit live spending authorization was not
received.

| Approach | Assigned | Executed | Independently correct deliveries | Total live seconds / tokens / dollars | Cost per correct delivery |
| --- | ---: | ---: | --- | --- | --- |
| Luna:high alone | 4 | 0 | Unobserved | Unobserved / 0 dispatched / unknown | Unknown |
| Sol planning → Luna | 4 | 0 | Unobserved | Unobserved / 0 dispatched / unknown | Unknown |
| Luna → Sol verification + eligible correction | 4 | 0 | Unobserved | Unobserved / 0 dispatched / unknown | Unknown |
| Sol planning → Luna → Sol verification + eligible correction | 4 | 0 | Unobserved | Unobserved / 0 dispatched / unknown | Unknown |
| Sol:high alone | 4 | 0 | Unobserved | Unobserved / 0 dispatched / unknown | Unknown |

Offline controls qualify only the **finite behavioral grader** on trusted bundled
code: four correct and four alternative implementations passed; four algorithm
defects, four omitted batch implementations and one float-for-integer defect
failed. All seventeen passed the existing public suites. These are known controls,
not model deliveries or native-isolation evidence. Simulated runner tests exercise
all five arms, one same-thread correction, private-grade separation, invalid
advice and stopping with failed-usage retention; they are not experimental outcomes.

Current recommendations are **INCONCLUSIVE** for optional Sol planning, Sol
verification, Proofline checks' incremental correctness benefit and bounded Luna
correction. Keep the existing optional, model-free check workflow. Neither a
Luna:medium nor Luna:xhigh follow-up is justified by this preparation alone; each
would require a separate frozen and authorized cohort. These five arms compare
the verification package, not the separate causal effects of checks, review and
correction. Four tasks cannot support broad reliability claims.

The [protocol](../../sol_luna/protocol.json), [freeze](../../sol_luna/FREEZE.json)
and [implementation notes](../../../docs/ISSUE32.md) document task requests, seed
identities, private literal vectors, controls, prompts, balanced order, total
budgets, bounded correction and stop rules. Declaration (`FREEZE.json`) SHA-256:
`e391635f69d640cb9dd73118050849bc6b638ae6e0c41edf28207541bdfcd6d0`.

Evidence files:

- `results.json`: all twenty slots, STOPPED status, zero dispatches, unknown cost comparisons.
- `manifest.json`: equal per-task source/seed identities, public checks and full declaration.
- `offline-controls.json`: seventeen literal-oracle controls with raw observations.
- `catalog-readback.json`, `native-host-probe.json`: exact no-model failures.
- `preparation-overhead.json`: measured preparation/control work; unknown authoring, human and dollar costs.
- `raw-evidence.zip`: raw records and all seeds, including Git snapshots; native SQLite state excluded, symlinks archived without reading targets.
- `frozen-source.zip`: exact grader/corpus/runner/check machinery, native model catalog, producer sources and licenses.
- `hashes.json`: SHA-256 of the published evidence and archives.

Validation: the clean-checkout suite ran **214 tests**, passing with **eight opt-in native tests skipped**. No native model experiment was enabled.

Run `python -B -m unittest tests.test_sol_luna -v` and
`python -B -m evaluation.sol_luna.study controls` for offline reproduction.
`qualify` and `execute` refuse replay of this stopped declaration. A repaired host
needs a separately frozen fresh declaration and explicit authorization before
any live spending. Dollar cost stays unknown without reliable actual billing;
public token prices are not substituted for Codex subscription costs.
