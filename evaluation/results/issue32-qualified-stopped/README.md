# Complete native qualification; first primary review exceeded lifecycle budget

Declaration `issue32-sol-luna-high-qualified`, freeze SHA-256
`13403c60f405062941f9d05b3c0a83236ab6034b73ba86a0de80284835429863`,
was authorized through the user's original live approval and subsequent request
for lenient qualification and continuation. All model-free native controls
passed. The actual four-call Sol → Luna → Sol → same-Luna correction passed.
The first primary assignment then stopped; the other 19 were never dispatched.
This declaration is never resumed or pooled into a subsequent comparison.

| Observed stage | Seconds | Input tokens | Cached subset | Output tokens |
| --- | ---: | ---: | ---: | ---: |
| Qualification Sol plan | 131.841 | 206,998 | 176,768 | 3,889 |
| Qualification Luna initial | 47.896 | 79,736 | 59,392 | 1,493 |
| Qualification Sol verification | 86.798 | 58,976 | 28,928 | 1,248 |
| Qualification original-Luna correction | 73.808 | 78,843 | 73,728 | 676 |
| Primary Luna idempotent-ledger implementation | 124.656 | 119,654 | 97,536 | 4,257 |
| Primary Sol verification, CLI timed out | 120.027 | 73,976 | 51,456 | 2,883 |

Qualification took 343.355 seconds including setup/checks. The primary episode
took 246.706 seconds before stopping. It made two native dispatches; qualification
made four. Dollar spending is unknown. These costs exclude the separately
preserved earlier 75-second failed call, whose token usage is unknown.

The resumed CLI reports **cumulative session** usage: its 158,579 input tokens
already include the initial 79,736. `normalized-accounting.json` reports the
78,843-token correction delta and preserves both raw values. This matches the
[installed-version CLI source](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L108)
and the qualification's native session counters. The original result and its
raw summed metrics remain unchanged. Accounting corrections do not change
grading, model exposure, repair eligibility or delivery outcomes.

The primary reviewer emitted a final structured finding and `turn.completed`
usage at approximately 102 seconds (host evidence-file timestamps), but the CLI
had not exited when the 120-second lifecycle budget expired. The host killed and
reaped it. The invocation remains NOT VERIFIED; its token observation survives
without upgrading its status. The broad original blocker text is retained, but
does not establish unavailable entitlement or a failed sandbox.

Luna's exact frozen candidate passed both public checks. A separate **post-stop**
run of the unchanged native private grader accepted its finite obligations.
`post-stop-grade.json` retains the native receipts; it does
not turn the interrupted workflow into a completed delivery. Sol also suspected
overvalidation of unused empty balance keys, an interpretation not resolved by
the public examples. This remains advisory and cannot trigger correction. The
finite grader is not comprehensive proof of every possible source interpretation;
neither its expectations nor controls were amended after this observation.

The read-only `account/usage/read` probe returned `threadUsage: null` for all
five distinct experimental threads. `thread-consumption.json` excludes
account-wide activity and credentials. No observed dollar cost or monetary
savings can be inferred from tokens.

The practical next step is a separately authorized fresh declaration with
generous startup/shutdown-inclusive stage budgets, equal total budget policy
across arms, and reuse of this completed native control. That comparison must
retain these failures separately. No model substitution, primary retry, new
reviewer, grader repair or speculative correction is justified.

`frozen-source.zip`, `raw-evidence.zip`, manifests, original authorization and
results bind the exact executed version. The post-stop grade and normalized
accounting are separately labeled additions. No private grading output was
supplied to either model.

Native controls and controller-process logs are retained inside `raw-evidence.zip`
without redundant unpacked generated copies.
