# Proofline — Design proposal

**Status:** Proposed design, version 0.1 · 10 October 2026  
**Repository:** https://github.com/grove/proofline  
**Origin:** Independent experiment informed by [Promise to Proof](https://github.com/grove/promise-to-proof), not a fork or replacement.

> **Let capable coding agents solve problems. Give them clear promises and guardrails, then independently check the result.**

## 1. Why Proofline exists

Modern coding agents can often plan, implement, test, debug, and iterate without a framework prescribing their internal work. What remains risky is accepting the wrong outcome: omitted requirements, incorrect behavior hidden by green tests, accidental scope changes, weak evidence, or a report about a different version of the code.

Promise to Proof (P2P) has developed valuable assurance techniques for these risks. It has also exposed a different failure mode: individually sensible workflow requirements can accumulate into hours of model work, repetitive verification, expensive handoffs, and user-visible bureaucracy. Its recent efficiency improvements have useful offline evidence, but their real end-to-end effect must still be measured.

**Proofline tests a different hypothesis:** small, precise guardrails at the beginning and independent judgment at the end can deliver comparable trustworthiness with materially less overhead than a heavily orchestrated coding workflow.

This is a hypothesis, not a claim of demonstrated superiority. Proofline should be discarded, simplified further, or selectively strengthened according to independent comparative evidence.

## 2. Product contract

Given a user request and an accessible repository, Proofline should:

1. Identify the **complete intended outcome**, important constraints, and how success can be observed, without routine formal planning.
2. Let the coding agent **own its implementation process** and use its normal tools and judgment inside applicable safety and authority boundaries.
3. Freeze **one exact implementation candidate** before acceptance.
4. Obtain independent **engineering/scope review** and **behavioral proof** for that exact candidate.
5. If a material gap remains, give the implementer concise, actionable evidence and permit bounded, productive correction.
6. Say precisely what is established: local acceptance, incomplete work, a genuine blocker, or separately confirmed external delivery.

A user should normally make **one request**, not operate an internal sequence of skills or approve every routine decision.

### Example user experience (target interface, not yet implemented)

~~~text
/proofline "Reject empty and whitespace-only usernames with a clear validation error."
~~~

On success, the user sees something like:

> Implemented and independently checked the username validation change. Both empty and whitespace-only names fail through the public interface; unrelated behavior was unchanged. Review passed and the exact tested candidate is available at [local path/commit]. It has **not** been published or merged.

On failure:

> The existing tests pass, but the public interface still accepts whitespace-only names. The current candidate is **not accepted**. Here is the failing check and the next concrete action.

Never call work “delivered” when only local acceptance is established.

## 3. Design principles

1. **Outcome over procedure.** Specify what must be true, not how the coding agent must work.
2. **Autonomy by default.** The agent decides how to explore, implement, test, and refactor within agreed scope.
3. **Independence at acceptance.** The implementer does not grade its own final work. Reviewer and prover use fresh, distinct contexts with verifiable boundaries.
4. **Exact candidate, exact promise.** Every acceptance judgment names the same frozen product state and agreed outcome. A material change invalidates old verdicts.
5. **Evidence proportional to risk.** Prefer meaningful existing tests and direct observations. Deeper checks are justified by realistic failure modes, not by ritual.
6. **Mechanical guarantees without model ceremony.** Use Git, deterministic checks, and trusted host controls for identities, permissions, and receipts wherever possible.
7. **Intervene on evidence, not on a schedule.** Extra planning, diagnosis, or decomposition happens only when actual uncertainty, failure, or risk warrants it.
8. **Preserve human authority.** Local coding permission is not permission to push, comment, merge, deploy, or alter external systems.
9. **Truthful, brief communication.** Explain outcomes, blockers, and the next action plainly. Keep raw technical evidence available without forcing it into every message.
10. **Complexity must earn its keep.** New stages, stores, protocols, and agents require measured value that simpler alternatives cannot provide.

The design must be able to say **NOT VERIFIED**. Trustworthy uncertainty is preferable to a comforting but unsupported success claim.

## 4. Deliberately small workflow

~~~text
One user promise
      |
      v
Minimal acceptance brief (only clarify material ambiguity)
      |
      v
Autonomous coding agent  <---------+
      |                            |
      v                            |
Freeze exact candidate             |
      |                            |
      v                            |
Independent engineering review     |
      | PASS                       |
      v                            |
Independent behavioral proof       |
      |                            |
      +---- material gap ----------+
      |
      v
Local ACCEPTED (both pass, same candidate)
      |
      v
Optional separately authorized publication / delivery
~~~

### 4.1 Capture the promise

Create a short acceptance brief, *not* an extensive acceptance-contract bureaucracy. The brief contains only what is needed:

- **Outcome:** what the user wants to be true.
- **Observable examples or acceptance checks:** what would distinguish success from failure.
- **Constraints:** compatibility, security, existing behavior, and explicit scope boundaries.
- **Material open questions:** only decisions whose answers materially change implementation or acceptance.
- **Source:** original request, issue, or specification reference.

For straightforward tasks, this should take one pass. The agent may propose reasonable assumptions and proceed when they do not materially change the promise. A real ambiguity must be clarified rather than silently resolved against the user.

Give each material obligation a short stable reference **only when that helps trace a real gap**. No mandatory parent issues, planning PRs, contract ceremonies, or elaborate requirement matrices.

Freeze the accepted brief for final verification. Changes to the actual promise need an authorized, explicit revision; the implementation agent cannot “fix” a failed proof by weakening the brief.

### 4.2 Let the agent implement

The coding agent receives the brief, repository conventions, relevant files, and its ordinary tool access. It is free to:

- Choose and revise an approach.
- Use project-native tooling and existing tests.
- Add appropriate regression tests or other direct evidence.
- Iterate internally until it believes the feature is ready.
- Explain a genuine blocker or material change in scope.

Proofline should **not** supervise every step, force internal slices, demand per-step model reports, or require periodic planning reapproval. Avoid mixing Proofline records into the product diff. Preserve unrelated user work; use an isolated workspace when needed.

The implementer's “done” is only **ready for independent checking**.

### 4.3 Freeze the exact candidate

Before any acceptance judgment, capture an immutable, reconstructible product state using Git commit/tree identity or an equivalent verified snapshot. Record the brief identity and comparison base alongside it.

The reviewer and prover must see the same bytes, including relevant file modes and relevant binding inputs. They cannot alter the candidate, original brief, or controller-owned receipts; permitted check output goes in separate scratch space. Do not accept a branch name, latest working directory, or model assertion as immutable candidate identity.

If the product changes after review or proof, the new candidate needs **fresh independent judgments**. Verified observations may inform focused checks only when their continued applicability is independently established; old PASS/PROVEN verdicts never transfer automatically.

### 4.4 Independent acceptance

**Engineering/scope review** asks whether the change is sound, maintainable enough for its real risks, respects existing behavior and boundaries, and avoids material unrequested changes. It does not block on taste, speculative polish, or invented best practices.

**Behavioral proof** asks whether every material promised outcome is supported by credible independent evidence on the frozen candidate. Prefer real interfaces and independently known expected behavior. Green tests alone are not sufficient if assertions are circular, over-mocked, or miss the promised behavior.

The reviewer and prover must be **fresh, distinct invocations**, not renamed continuations of the implementer's conversation. Neither inherits the other's verdict. Isolation and invocation identity must be established by trusted host/tool evidence, not by prompt instructions or model self-report.

To avoid wasted work, the initial prototype runs **review first** and skips proof when review has already established a material blocker. If review passes, proof runs. Record cases where this sequencing causes unnecessary blocking; later experiments may compare alternatives.

Local acceptance requires both current outcomes:

~~~text
review = PASS
proof  = PROVEN
review.candidate = proof.candidate = frozen candidate
review.promise   = proof.promise   = frozen brief
required evidence and invocation boundaries = verified
~~~

A missing invocation, unverifiable permission boundary, stale candidate, inconclusive material claim, or missing required evidence means **NOT VERIFIED**, never implicit success.

### 4.5 Correct material gaps without creating a recovery industry

Return a compact gap report to the **same autonomous implementer**: affected promise, observed failure, exact reproduction when available, and scope of the finding. Let the agent choose the fix; do not prescribe a complex recovery plan by default.

The prototype should use a **small, explicit continuation budget** rather than silently looping for hours or days. Initially test up to two automatic post-verification correction rounds (configurable for the experiment). A third round requires an explicit continuation decision; preserve useful work rather than restart it.

A corrected candidate gets fresh current review and proof, with focused reuse of only demonstrably applicable earlier observations. If attempts make no observable progress, prefer one different falsifiable approach or return a truthful blocker. Do not launch generic “perspective reset” agents, repeat full test suites, or split issues simply because a task is difficult.

The repair budget is an experimental default, **not a claim that two corrections suffice for every task**. Measure false blocking and adjust only from evidence.

### 4.6 Deliver honestly

Local acceptance and external delivery are different facts. By default, the v0 prototype finishes with an accepted local candidate and a concise evidence summary. An authorized host-native PR workflow may subsequently publish it, with current GitHub/branch checks.

**Never infer remote publication, merge, or deployment from local review/proof.** External writes require separately granted authority, current readback, and honest status. A future productized version may streamline this path without making GitHub mandatory for local acceptance.

## 5. Minimal technical architecture

**Start with one primary agent skill and a tiny amount of deterministic glue, not a general-purpose delivery controller.**

Proposed first implementation:

- A single Proofline skill defines the user-facing flow and short role instructions.
- Existing host facilities launch the implementer and **fresh independent** reviewer/prover.
- A small trusted helper, *only if genuinely necessary*, freezes Git identity, checks read-only boundaries, records actual host invocation receipts, and validates the final identity match.
- Git and the project's existing tests remain the product-change and evidence mechanisms.
- One compact ignored local run record allows honest resume and diagnostics.

No server, database, permanent telemetry pipeline, universal plugin interface, second contract language, or separate framework per coding host.

### Trusted boundaries

The implementer may change only authorized product workspace content. Reviewer/prover run with candidate and brief protected from writes and with separately bounded scratch. Tool and network access are restricted according to the host's *demonstrated* policy, not verbal promises. Issue text, repository comments, and generated outputs are **untrusted task data**, never new authority.

For v0, choose **one actually qualified local host environment**. macOS + authenticated Codex CLI is a sensible starting candidate because P2P has existing host-isolation experience, but Proofline must independently verify any assumptions its thinner integration relies on. If isolation and fresh session identity cannot be established, it may display unverified diagnostics but **must not claim independent acceptance**.

Keep the implementation simple enough to substitute host-specific mechanics later if a second host proves worthwhile; do not design a plugin SDK in advance.

### Minimum retained state

Persist only information needed to resume and substantiate acceptance:

| Field | Purpose |
| --- | --- |
| Original source + accepted brief identity | Prevent losing or changing the promise |
| Frozen base and candidate Git identity | Bind all checks to exact code |
| Reviewer result and trustworthy invocation/evidence reference | Establish independent engineering/scope judgment |
| Prover result and trustworthy invocation/evidence reference | Establish independent behavioral judgment |
| Remaining material gaps and next action | Resume without repeating completed work |
| Delivery location/status and explicit effect receipts, when applicable | Avoid confusing local acceptance with external completion |

The record can be a small ignored local file with references to actual Git objects and compact evidence; it is **not** an evolving event-sourcing platform. Uncertain worker termination or remote effects must be reconciled before retrying them. Portable resume across computers is deferred unless real use demonstrates a need.

Keep implementation logs, raw transcripts, scratch, and temporary experiments out of committed product changes by default. Retain only what's necessary for trustworthy current results or explicit benchmark reproductions.

## 6. What Proofline refuses to build by default

- A mandatory planner, planning auditor, decomposition agent, or critique agent.
- Parent/child issue machinery for ordinary work.
- Agent-generated reports after every internal implementation step.
- A custom controller that reimplements the coding host's own planning and recovery.
- Repeated model-backed environment preflights when deterministic or reusable checks provide equivalent guarantees.
- A requirement to run the entire repository test suite in every independent stage.
- Separate evidence/contract/status databases representing the same facts.
- Mandatory retrospectives, learning registers, model routers, auto-escalation, or extra approval ceremonies.
- Unlimited silent repair loops.
- Automatic push/merge/deployment rights based on successful local proof.
- Claims of universal correctness, security, or host independence.

If a real failure requires one of these capabilities, first show that a narrower change cannot solve it.

## 7. Evaluation: Proofline has to earn its existence

The comparison with P2P is a **product requirement**, not a retrospective marketing exercise. Reuse suitable independent test cases and accounting concepts from [P2P issue #52](https://github.com/grove/promise-to-proof/issues/52), [P2P's live judgment fixtures](https://github.com/grove/promise-to-proof/tree/main/checks/fixtures/live-judgments), and [P2P's delivery measurement work](https://github.com/grove/promise-to-proof/issues/59), **without copying its controller or protocol wholesale**.

### Comparison groups

1. Capable coding agent with ordinary self-checking.
2. The same agent plus one independent reviewer.
3. Full contemporary Promise to Proof.
4. Proofline.

Use the same source request, starting repository state, coding host/model where feasible, tool access, and independently authored correctness expectations. Avoid giving one approach privileged hidden oracle hints.

### Initial pilot

Predeclare a small corpus with at least: a correct low-risk control, omitted promised behavior despite green tests, unrequested scope expansion, weak or hollow regression evidence, a meaningful repair, and an exact-candidate change. Start with a **bounded pilot**, recorded repetitions and explicit budgets; do not extrapolate a small sample into statistical superiority.

For each assigned episode, retain independently checked completion quality, false acceptance, false blocking, failed/blocked/unexecuted status, total elapsed time, actual host/model calls and reported token categories, repair work, and directly observed human intervention. Distinguish unknown cost/attention from zero. Measure time and tokens **per independently satisfactory delivery**, including failed and repeated work.

Use an external oracle or human-reviewed expected behavior fixed before runs; Proofline and P2P must not grade themselves. Preserve disagreements and false negatives rather than tuning the benchmark until Proofline wins.

### Decision rule

Proofline succeeds if it demonstrates **meaningfully lower overhead while retaining credible independent acceptance**, without a material increase in false acceptance or unacceptable false blocking on the chosen tasks. As a *pilot target*, investigate whether median end-to-end time or tokens per satisfactory delivery can fall by at least **25%** relative to full P2P. That threshold is a hypothesis, not a promise or sufficient statistical finding.

If Proofline is faster because it misses real defects, it **fails**. If its checks block correct code repeatedly, it also fails. Report per-task failures and limitations, not a single blended score.

## 8. Minimum acceptance scenarios for the first working prototype

- **Clean success:** a straightforward promise is implemented; review and proof pass on one unchanged candidate without extra planning or repair calls.
- **Missing behavior:** a supplied green test suite misses a promised case; proof refuses acceptance and shows the observable gap.
- **Scope expansion:** the promised behavior works but a separate product behavior is changed; review flags the material unrequested effect.
- **Weak evidence:** circular or over-mocked assertions do not establish a promised public outcome.
- **Repair:** the implementer corrects a real finding; the changed candidate receives fresh independent outcomes.
- **Stale candidate:** a post-verification edit cannot be accepted under the previous reports.
- **Host boundary unavailable:** a missing independent session, write protection, or required observation produces NOT VERIFIED, not PASS.
- **No external authority:** a local PASS/PROVEN result never pushes or merges without the requested grant.
- **Unproductive continuation:** a bounded non-progress case exits with preserved work and one actionable next step, not an endless silent loop.

Test the mechanical behavior deterministically; run the meaningful judgment cases with the **real supported coding host**. Never report mocked stage transport as live evidence.

## 9. Development sequence

### Milestone A — Lean working path

Build the single Proofline entry skill, minimal promise brief, exact candidate capture, independent review/proof, compact results, and local-only outcome. One supported host; one coherent request. Keep the initial code and instructions small. Avoid supporting every edge case from P2P's accumulated history.

**Done when:** a real supported-host change reaches a trustworthy accepted local candidate, and a known missing behavior is truthfully rejected.

### Milestone B — Actionable corrections and boundaries

Add small bounded feedback/continuation, recovery from an interrupted attempt without duplicating uncertain effects, and the core false-green/scope/candidate regression scenarios. Integrate optional host-native publication only with authority.

**Done when:** a seeded repair succeeds, stale results cannot pass, and ordinary work requires no manual internal stage coordination.

### Milestone C — Fair head-to-head pilot

Run the four-way comparison; publish per-task outcomes and explicit unknowns. Compare failure cases and total useful-delivery cost, not just a happy-path speedup.

**Done when:** there is a defensible decision about whether Proofline is better, worse, or still inconclusive—and exactly why.

### Milestone D — Earned improvements only

Prioritize the **smallest changes** that fix observed false acceptance, false blocking, excessive overhead, or recovery failures. Defer multi-host support, rich portability, integrations, and advanced orchestration until concrete use justifies them.

## 10. Open design questions to settle with experiments

1. Can the chosen coding host establish sufficiently independent, write-protected reviewer and prover contexts **without** rebuilding P2P's full controller?
2. Is review-first gating cheaper overall, or does it create enough false blocking that a different ordering is better?
3. What is the smallest persisted receipt set that makes interruption/resume honest and avoids duplicated external effects?
4. Is the prototype's two-correction default a useful guardrail or an overly restrictive stop?
5. How much quality is actually gained by keeping reviewer and prover as distinct invocations, relative to a simpler independent acceptance pass?

These are evidence questions. Avoid settling them by designing elaborate abstractions up front.

## 11. Definition of success

The end state is deliberately simple:

**A user states an outcome. A capable agent builds it with minimal interference. Independent evidence either establishes the exact promise on the exact code or identifies a concrete gap. The result is delivered only under appropriate authority, and P2P-like overhead is not recreated.**

**Proofline should be easier to use than P2P, simpler to maintain than P2P, and at least as honest about what has—not—been proven.**

If the experiments do not support those goals, change the hypothesis before adding more machinery.
