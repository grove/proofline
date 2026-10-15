# Detect wasted delivery time and redirect to useful progress

## Outcome

Prevent hours-long `deliver-issue` activity that consumes tokens and wall time **without meaningful progress**, while allowing genuinely long-running productive work to continue autonomously.

Current baseline: completed #74 recognizes repeated material failures and oscillating candidate/repair strategies; PR #87 improves bounded recovery and host errors. New deliveries nevertheless default to unlimited time, dispatches, repairs and no idle watchdog. Logs and heartbeats show activity, not advancement. **Extend the existing recovery/continuation policy, not a new supervisor.**

## Scope

Use #109 real episode evidence and #59's saved attempt/stage observations to distinguish legitimate long tasks from stalled execution. Design a small policy for evidence-based progress: observable changed behavior against a named obligation, verified implementation slice, new reproducible finding, or a materially different executable step that resolves a known blocker. Token output, log chatter, file-touch counts, elapsed time or merely rewriting an action are not by themselves progress.

When the workflow crosses a *configurable advisory* no-progress threshold, assess the saved evidence. Prefer an existing #74 fresh-perspective diagnosis, a different falsifiable implementation strategy, justified small internal step replan, or an honest concrete blocker. Do not repeatedly pay for diagnosis after healthy progress or on the same unresolved state. A recognized worker that is still productive must not be killed just because its wall time is large.

Use existing termination/recovery receipts for optional idle interruption. Respect explicit deadlines and mandates; never assume an expired worker stopped if termination is uncertain. The no-progress signal must not automatically shrink the acceptance contract, declare `PROVEN`, authorize external effects, or force an issue split (#77 is for genuine structural boundaries).

## Acceptance

- Live or captured-real-host examples distinguish (a) active useful work, (b) chatty but unchanged behavior, (c) repeated semantic failure, (d) slow but productive progress and (e) an unresponsive worker with uncertain termination.
- A genuinely stalled example chooses one testable different next action **within existing authority**, or returns an actionable blocker; an advancing example continues without extra routine model stages.
- Recovery never loses verified slices, candidate generations, old proof/review identities, checkpoint portability, or the exact last confirmed worker outcome.
- Configured user limits still take precedence; no blanket silent finite deadline or speculative universal retry allowance is introduced.
- Measure actual reduction in repeated model calls / unproductive elapsed time on a supported live host, with offline regression fixtures for false escalation.
- Status explains useful progress and next action in plain language, without invented percentages/ETAs.

## Dependencies and non-goals

Follow #109's initial baseline or reproduce a small measured no-progress case. Reuse #55/#73 incremental state and #74 diagnosis; do not reimplement any of them, add a second recovery engine, or create mandatory human check-ins. #52 can compare overall value separately.
