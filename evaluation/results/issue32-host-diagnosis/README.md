# Host diagnosis — no empirical model result

No inference turns were dispatched by these diagnostics. The original
`issue32-sol-luna-high` declaration remains stopped at 0/20; its source archive,
results and failure receipts are unchanged.

| Observation | Result | Meaning |
| --- | --- | --- |
| Original pipelined catalog client, host launch | No RPC response within 15 seconds | Host execution alone does not fix the timeout |
| Sequential initialize → initialized → model/list | Response after 37.7 seconds | Initialization exceeds the original deadline |
| Explicit stdio without `--no-daemon` | Response after 38.5 seconds | CLI routing flag does not explain the delay |
| Native read-only canary launched from host | All protected accesses and loopback denied; scratch allowed | Existing native isolation works outside the enclosing sandbox |
| First repaired no-model preflight | Catalog passed; worker canary stopped | Missing `results.json` returned unknown, not denial |
| Worker and reader canaries with actual protected results | Both observed | Real denial fixtures resolve the additional qualification bug |
| Independent native grader controls | 17/17 matched | Eight correct/alternative controls accepted; nine green-suite defects rejected |
| Native Intentline → adapter → Proofline → receipt readback | Observed | Existing model-free handoff path works |
| Native thread-specific consumption RPC | `threadUsage: null` | Dollar spending and model-specific consumption estimates remain unavailable for this active initiating thread |

A one-second startup stack sample contained
`codex_state::extract::apply_rollout_item`, consistent with backfilling rollout
state into the fresh `sqlite_home`. The sample is retained in local diagnostic
storage, not committed as a large platform stack dump. The experiment's repaired
catalog client retains its private state directory, waits up to 60 seconds total,
and reports initialization versus catalog timeouts separately. It never creates
a thread or turn. A catalog is not an entitlement check; completed native
inference remains required after explicit spending authorization.

`failed-preflight.zip` contains the stopped no-model proposal's source/freeze,
all twenty unexecuted slots, manifest, catalog response and failed worker
receipt. `original-host-timeout.json`, `sequential-catalog.json`,
`direct-catalog.json` and `native-boundary.json` retain the independent native
observations. `thread-consumption.json` contains only the relevant usage response;
account-level activity and credentials are not included. Additional passing
control receipts are archived separately with the fresh qualification evidence.

These are transport/isolation/grader observations, not Sol/Luna coding
improvement. No assignment success, token saving or monetary saving is claimed.
The [fresh protocol](../../sol_luna_host/protocol.json) preserves the primary
study's source, grader, correction, order and budgets and requires its own live
authorization. The broader [correction proposal](../../../docs/ISSUE32_CORRECTIONS.md)
is separate and unauthorized.
