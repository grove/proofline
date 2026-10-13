# Authorized 75-second qualification attempt — stopped, 0/20

The user authorized declaration `issue32-sol-luna-high-native`, freeze SHA-256
`25486e814d0060a59f48f40eba7eebab76a125dba9998db8e5c0e1cd2bdf1f8f`.
Model-free preparation passed the exact model catalog, native worker/read-only
boundaries, all 17 independent grader controls and the Intentline/Proofline
roundtrip. The first live Sol:high planning control was interrupted after
75.032 seconds. Luna was never dispatched and all 20 primary assignments remain
unexecuted. This declaration is stopped permanently.

Sol read the original staged control, ran its isolation canary, and completed
Intentline prepare/propose/check/render/export before the deadline. There was
no completed native turn, final schema response or usage total. This is evidence
of actual inference/tool execution, but not successful end-to-end qualification.
The canary also reported the private-grader read as unknown: the continuation
directory lacked the grader path expected by the historical advisory helper.
That missing fixture must be repaired independently of increasing the timeout;
unknown access is never accepted as denial.

| Accounting | Observed |
| --- | --- |
| Native dispatches | 1 Sol:high; 0 Luna:high |
| Model invocation time | 75.032 seconds |
| Handoff control time, including setup | 75.373 seconds |
| Model tool executions | 14 |
| Input / cached input / output tokens | Unknown; no completed-turn usage |
| Dollar spending | Unknown |
| Primary assignments / independently correct deliveries | 0/20; unobserved |

The raw result's blocker text, `Configured native handoff model unavailable`,
is too broad. The receipt demonstrates an interrupted call and an absent denial
fixture; it does not demonstrate denied model entitlement. It is retained
verbatim for auditability.

The user subsequently requested a more lenient timeout and continuation. The
separate fresh declaration uses four calls of at most 180 seconds within a
900-second qualification budget and provides the actual pinned grader alias.
Primary requests, grading expectations, models, efforts, assignment budgets and
correction rules are unchanged. Neither this control nor the new disposable
control counts as a primary assignment or an efficacy observation.

`frozen-source.zip` retains this attempt's original code and both freezes;
the current continuation code must not be substituted when replaying this
failure. `raw-evidence.zip` retains prompts, native events, receipts, plan export,
native controls and all 20 unexecuted slots. Private app-server state is omitted.
The unpacked JSON files provide the declaration, authorization and result.
