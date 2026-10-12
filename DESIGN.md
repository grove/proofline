# Proofline — Design proposal

**Status:** Proposed design, version 0.5 · 11 October 2026  
**Repository:** https://github.com/grove/proofline  
**Origin:** Independent experiment informed by [Promise to Proof](https://github.com/grove/promise-to-proof), not a fork or replacement.

> **Let capable coding agents solve problems. Give them clear promises and guardrails, then independently check the result.**

**Optimization rule:** Maximize the coding agent's freedom to find a complete solution and the independent verifier's ability to detect an incorrect one. Every mandatory intervention must improve those outcomes enough to justify its cost.

## 1. Why Proofline exists

Modern coding agents can often plan, implement, test, debug, and iterate without a framework prescribing their internal work. What remains risky is accepting the wrong outcome: omitted requirements, incorrect behavior hidden by green tests, accidental scope changes, weak evidence, or a report about a different version of the code.

Promise to Proof (P2P) has developed valuable assurance techniques for these risks. It has also exposed a different failure mode: individually sensible workflow requirements can accumulate into hours of model work, repetitive verification, expensive handoffs, and user-visible bureaucracy. Its recent efficiency improvements have useful offline evidence, but their real end-to-end effect must still be measured.

**Proofline tests a different hypothesis:** small, precise guardrails at the beginning and independent judgment at the end can deliver comparable trustworthiness with materially less overhead than a heavily orchestrated coding workflow. The original promise must survive summarization intact, and independent acceptance must challenge actual outcomes rather than merely endorse an implementer's tests.

**Division of responsibility:** users/product owners authorize *what is promised*; upstream acceptance planning may express that promise as a versioned agreement. **Proofline owns autonomous implementation, independent review, behavioral proof, and bounded correction.** Reuse P2P's planning outputs without inheriting its delivery controller or planning process.

This is a hypothesis, not a claim of demonstrated superiority. Proofline should be discarded, simplified further, or selectively strengthened according to independent comparative evidence.

## 2. Product contract

Given an accessible repository and **either a direct user request or an already authorized, source-grounded acceptance contract**, Proofline should:

1. Preserve the **complete original promise**, including applicable explicit acceptance criteria, constraints, source references, and any authorized contract identity; never silently narrow it.
2. Let the coding agent **own its implementation process** and use its normal tools and judgment inside applicable safety and authority boundaries.
3. Bound the **entire delivery episode**—implementation, checking, and corrections—rather than only limiting repair rounds.
4. Freeze **one exact implementation candidate** before acceptance.
5. Obtain independent **engineering/scope review** and actively challenging, **criterion-level behavioral proof** for that candidate against the authoritative promise.
6. If a material gap remains, give the implementer concise, actionable evidence and permit bounded, productive correction.
7. Say precisely what is established relative to the **user-authorized delivery target**: local acceptance, PR creation, merge, incomplete work, or a genuine blocker.

A user should normally make **one delivery request**, with any desired publication/merge authority granted up front. Direct requests do not require P2P. Already accepted plans are reused without re-planning or repeated approval; drafts cannot be silently treated as approved. Users should not operate a sequence of internal skills or reapprove previously authorized actions. The first prototype supports local acceptance only.

### Example user experience (target interface, not yet implemented)

~~~text
/proofline "Reject empty and whitespace-only usernames with a clear validation error."

# Or use an already approved contract:
/proofline .p2p/work/username-validation/contract.md
~~~

On success, the user sees something like:

> Implemented and independently checked the username validation change. Both empty and whitespace-only names fail through the public interface; unrelated behavior was unchanged. Review passed and the exact tested candidate is available at [local path/commit]. It has **not** been published or merged.

On failure:

> The existing tests pass, but the public interface still accepts whitespace-only names. The current candidate is **not accepted**. Here is the failing check and the next concrete action.

Never call work “delivered” when only local acceptance is established.

## 3. Design principles

1. **Outcome over procedure.** Specify what must be true, not how the coding agent must work. Acceptance planning is an **optional upstream capability**, not another mandatory Proofline agent.
2. **Maximum useful autonomy.** The agent decides how to explore, implement, test, and refactor within agreed scope. Give it the complete promise, task-relevant repository affordances, and good failure feedback rather than regulating its internal steps.
3. **Independence at acceptance.** The implementer does not grade its own final work. Reviewer and prover use fresh, distinct contexts with verifiable boundaries.
4. **Exact candidate, exact promise.** Every acceptance judgment names the same frozen product state and agreed outcome. A material change invalidates old verdicts.
5. **Evidence proportional to risk.** Independently challenge each material promised outcome through meaningful observations and plausible counterexamples at the relevant risk boundaries. Block only on material evidence or unresolved required assurance, not taste or speculative polish.
6. **Mechanical guarantees without model ceremony.** Use Git, deterministic checks, and trusted host controls for identities, permissions, and receipts wherever possible.
7. **Intervene on evidence, within a budget.** Extra planning, diagnosis, or decomposition happens only when real uncertainty, failure, or risk warrants it; the whole delivery has an explicit cumulative budget.
8. **Preserve human authority.** Local coding permission is not permission to push, comment, merge, deploy, or alter external systems.
9. **Truthful, brief communication.** Explain outcomes, blockers, and the next action plainly. Keep raw technical evidence available without forcing it into every message.
10. **Complexity must earn its keep.** Target three model-backed stage dispatches for a clean first pass—one implementer, one reviewer, one prover. New mandatory stages, stores, protocols, and agents require measured value that simpler alternatives cannot provide.

The design must be able to say **NOT VERIFIED**. Trustworthy uncertainty is preferable to a comforting but unsupported success claim.

## 4. Deliberately small workflow

~~~text
Direct user request or approved source-linked contract
      |
      v
Frozen authoritative source + accepted input
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
Independent challenging proof      |
      |                            |
      +---- material gap ----------+
      |             (within shared budget)
      v
Local ACCEPTED (same source/input/candidate)
      |
      v
Optional authorized PR / merge with confirmed readback
~~~

### 4.1 Consume the promise; leave acceptance planning upstream

**The user/product owner defines and authorizes the promised outcome.** A planning tool can turn that outcome into precise, falsifiable acceptance criteria, but cannot invent, narrow, or change the promise. Proofline begins at *delivery*. It supports two input paths with **one independent verification standard**:

1. **Direct request (lightweight default).** The existing entry flow prepares a small *source-grounded brief*: intended outcome, material observable criteria including relevant negative/boundary/regression behavior, binding constraints and exclusions, material open decisions, and original source identity. The brief is only an index to the source, not a competing agreement. Freeze its identity and the comparison base before implementation. No separate planning agent, approval ceremony, issue hierarchy, or P2P installation is required; preparation consumes the shared budget.
2. **Preplanned request (reuse existing work).** Consume a **user-authorized, approved, versioned acceptance contract**, including one produced by [P2P `plan-acceptance`](https://github.com/grove/promise-to-proof/blob/main/skills/productivity/plan-acceptance/SKILL.md). Keep the existing source-linked criteria and constraints without generating a second brief, rerunning planning, or importing P2P's delivery controller. The original binding source must be available to implementation and both acceptance roles. Equivalent accepted contracts from other tools are a future compatibility goal under the same source and authority requirements; v0 implements the narrow P2P Markdown contract path.

**Upstream P2P roles are distinct and optional.** [`plan-acceptance`](https://github.com/grove/promise-to-proof/blob/main/skills/productivity/plan-acceptance/SKILL.md) proposes a versioned contract with observable requirements, stable IDs, seams, oracles and evidence plans. [`create-parent-issue`](https://github.com/grove/promise-to-proof/blob/main/skills/productivity/create-parent-issue/SKILL.md) optionally publishes one durable source issue from an existing specification; it **does not define acceptance**. [`slice-contract`](https://github.com/grove/promise-to-proof/blob/main/skills/productivity/slice-contract/SKILL.md) optionally allocates large work into coherent child contributions; it **does not redefine the parent promise**. None is automatically invoked by Proofline, or mandatory for direct delivery.

**A small read-only input adapter, not another contract framework.** For a preplanned request, recover the exact accepted contract content/revision, verifiable approval or explicit user adoption of that exact version, the binding original user/issue/specification source content and revision, material criteria/IDs, constraints, exclusions, remaining decisions or evidence gaps, and any child/parent mapping and prerequisites. Freeze source, accepted-input, and comparison-base identities. A filename, issue label, or model statement is not evidence of approval. Missing original source, unverifiable approval, material contradictions, or unmet prerequisites mean the input is **not ready for accepted delivery**; name the actionable gap rather than inventing a product defect. Avoid requiring P2P runtime, checkpoint, or a particular `.p2p/` layout if the same identities and authority can be established directly.

**Constrain the v0 adapter.** Recognize P2P's current Markdown acceptance contract (source identity, approved contract revision and authorization, intended outcome, stable acceptance-row IDs with source references and expected behavior, boundaries, evidence intent, exclusions, open questions, and applicable parent/prerequisite bindings). Resolve and verify the *original source bytes*, not merely a URL or contract summary. Approval must come from a trusted binding record or explicit user adoption of the exact version; it is not implied by a file or `approved` text. Import only the facts needed for delivery and preserve upstream IDs. Do not recreate P2P approval workflows, historical checkpoint formats, or a general contract parser. Missing or unsupported data is a specific **input-readiness gap**, not a reason to improvise a narrower contract or fail an otherwise valid product implementation. This paragraph sets a v0 compatibility boundary, not a second agreement.

**Precedence and revisions.** The explicit current user mandate governs. A delegated issue/spec revision is binding within its scope; an approved contract expresses, but cannot silently override or omit, its obligations. Later comments and edits are not automatic amendments. Material source/contract conflicts and omitted source promises return to authorized upstream planning rather than becoming silent acceptance revisions. Reasonable non-material implementation choices belong to the coding agent.

**Independent acceptance.** Reviewer and prover consult the authoritative original source *as well as* the accepted direct brief or planned contract. Planned oracles, evidence paths, and `planned` contract rows are **guidance, not observed proof**. The prover independently derives expected behavior and challenges actual outcomes. Preserve P2P requirement IDs when supplied; do not renumber them. An obligation lost in either input path must remain visible to independent acceptance.

**Sliced work stays scoped.** A child contract authorizes its own source-traceable contribution and prerequisites, not completion of the original parent promise. Independently accepting a child never implies parent acceptance. The assembled parent requires separate full review and proof of **the complete original promise on one combined frozen candidate**; Proofline does not own slicing, tracker topology, or child/parent issue publication.

For simple work, proceed once on reasonable non-material assumptions. Ask for an essential decision only when the promised outcome or authority truly depends on it. A missing evidence path is a verification issue, not permission to rewrite the agreement. No mandatory parent issues, planning PRs, or elaborate requirement matrices.

### 4.2 Let the agent implement

The coding agent receives the original source and accepted input (direct brief or approved contract), comparison base, relevant repository conventions/files, known environment and test commands, applicable constraints and action authority, and its ordinary tool access. Provide enough context to avoid needless rediscovery, not an exhaustive repository dump.

**Make the real system easy to observe.** Include a short, task-specific *execution/observation map* from inspected repository facts where useful: relevant entry points, project-native build/test or run commands, fixtures/configuration needed for a meaningful check, the public interface to exercise, where errors/logs appear, and writable disposable scratch. Reuse existing `README`/`AGENTS.md`/project tooling rather than introducing a generated document or mandatory discovery stage. Mark unavailable commands or infrastructure as unknown, not operational. The implementer can use it to self-check; the independent prover may reuse verified environment facts but still derives its own expectations and probes. Do not require a runnable app for documentation-only changes or a browser for non-UI behavior. It is free to:

- Choose and revise an approach.
- Use project-native tooling and existing tests.
- Add appropriate regression tests or other direct evidence.
- Iterate internally until it believes the feature is ready.
- Explain a genuine blocker or material change in scope.

Proofline should **not** supervise every step, force internal slices, demand per-step model reports, or require periodic planning reapproval. On a clean first pass, implementation should require one top-level coding-agent stage dispatch, with the agent free to use its normal internal tools and self-checks. The shared delivery budget still applies. Avoid mixing Proofline records into the product diff. Preserve unrelated user work; use an isolated workspace when needed.

Before saying it is ready—and after material context compaction or a substantial change of approach—the implementer should **re-anchor to the authoritative source and accepted input**. Internally check each material promise and binding scope constraint against the actual work; run the most useful available targeted checks; surface any known incomplete or uncertain criterion in the existing handoff. This is a concise self-check within the implementation stage, **not** a second contract, independent verdict, per-step checklist, or mandatory model call. The original source, not a compacted recollection, remains authoritative.

The implementer's “done” is only **ready for independent checking**.

### 4.3 Freeze the exact candidate

Before any acceptance judgment, capture an immutable, reconstructible product state using Git commit/tree identity or an equivalent verified snapshot. Record the authoritative source-promise identity, accepted input identity (direct brief or approved contract revision), and comparison base alongside it.

The reviewer and prover must see the same bytes, including relevant file modes and relevant binding inputs. They cannot alter the candidate, source promise, accepted input, or controller-owned receipts; permitted check output goes in separate scratch space. Do not accept a branch name, latest working directory, or model assertion as immutable candidate identity.

If the product changes after review or proof, the new candidate needs **fresh independent judgments**. Verified observations may inform focused checks only when their continued applicability is independently established; old PASS/PROVEN verdicts never transfer automatically.

### 4.4 Independent acceptance

**Engineering/scope review** checks the candidate against the authoritative source *and* accepted input: was a material requirement lost in summarization, is the implementation sound for its actual risks, does it preserve relevant existing behavior, and does it avoid material unrequested changes? A **blocking finding** must name the violated promise, observed defect, unauthorized effect, or credible engineering risk, explain why it matters, and point to supporting evidence. Style, subjective preference, unrequested features, and speculative polish are advisory, never automatic blockers. A blocking engineering risk must have a credible mechanism and material consequence, not merely the possibility that some edge case might exist. Unresolved uncertainty about *required* assurance is reported as NOT VERIFIED, not invented as a defect or waved through.

**Change-impact-aware review.** Inspect the actual diff against the frozen comparison base, not just the agent's summary: which public paths, dependent behaviors, data contracts, or existing invariants could the change realistically affect? Challenge likely material regressions and unintended scope effects with targeted evidence. Avoid automatic full-repository dependency analysis, blanket regression suites, or blockers for unrelated pre-existing defects unless they obstruct a promised outcome. The reviewer's job is to find credible consequences of *this* candidate, not to make all nearby code perfect.

**Behavioral proof** actively tries to falsify the promised outcome. Derive the expected observable behaviors from the authoritative source **before relying on** implementer-authored tests, mocks, or explanations; independence of invocations alone cannot prevent shared mistaken assumptions. Probe plausible negative cases, boundaries, errors, and regression paths *proportional to the promise and risk*, preferably through real/public interfaces. For an applicable bug fix, a focused check that fails on the baseline and passes on the candidate is particularly persuasive when safe and feasible. Test relevant persistence, concurrency, authorization, or failure-recovery boundaries when the promise depends on them; do not impose them on unrelated changes. Existing tests remain useful evidence, but rerunning them without checking what they establish is not independent proof. For each material criterion, choose an observation that would distinguish the promised behavior from at least one plausible incorrect result; identify the relevant counterexample or explain why a direct observable result is decisive. If the same evidence would also pass a plausible broken implementation, strengthen the focused probe or report **NOT VERIFIED**. This is an **evidence-quality rule**, not a requirement for one bespoke negative test per row, mutation testing, a universal test quota, or exhaustive edge-case generation. Where direct execution is unavailable or unsafe, name the alternative evidence and its limits; material unsupported outcomes remain NOT VERIFIED. Adversarial testing is not a license to invent requirements or run unbounded exploratory suites.

Within the existing proof report, give **each material acceptance criterion** (preserving existing upstream IDs when supplied) one compact outcome: **SATISFIED** (credible observations), **VIOLATED** (a demonstrated gap), or **NOT VERIFIED** (missing or inconclusive evidence). Include the decisive observation, the plausible failure it discriminates (or why the observation is decisive), command/result or evidence reference, relevant risk boundary, and any material limitation. Aggregate **PROVEN** requires SATISFIED for every material criterion and no contradictory source obligation; test-suite success or model confidence is not an implicit criterion verdict. Do not create a second acceptance document, evidence database, or mandatory test-count quota.

The reviewer and prover must be **fresh, distinct invocations**, not renamed continuations of the implementer's conversation. Neither inherits the other's verdict. Isolation and invocation identity must be established by trusted host/tool evidence, not by prompt instructions or model self-report. Neither role may modify the frozen source, accepted input, or product candidate.

The initial prototype runs **review first** and skips proof when review already establishes a material blocker. Record any resulting false blocking; experiments may justify a different order without silently loosening the assurance standard.

Local acceptance requires both current outcomes:

~~~text
review = PASS
proof  = PROVEN
review.candidate = proof.candidate = frozen candidate
review.input     = proof.input     = frozen accepted input
review.source    = proof.source    = authoritative source identity
all material criteria = SATISFIED with credible independent evidence
required evidence and invocation boundaries = verified
~~~

A missing invocation, unverifiable permission boundary, stale candidate, source/accepted-input mismatch or unapproved contract that omits a material promise, inconclusive material claim, or missing required evidence means **NOT VERIFIED**, never implicit success.

### 4.5 Correct material gaps without creating a recovery industry

Use one **explicit, cumulative end-to-end budget** for implementation, independent acceptance, and corrections—not just a repair-attempt limit. For each run, define a maximum elapsed time and model/host dispatch allowance; track tokens and monetary cost where the provider actually exposes them. Declare which limits the host can enforce and which can only be observed or best-effort bounded; unavailable usage is **unknown**, not zero or a claim of hard enforcement. The budget and consumption persist across resumes and repairs and cannot silently reset. Preserve a **modest, configurable verification reserve** sufficient for one meaningful independent review/proof pass when feasible, so implementation cannot routinely consume the entire allowance and leave success uncheckable. The reserve is a budget allocation within the same episode, not another stage or hard per-stage quota; unused capacity may be redistributed based on actual progress and risk. If independent acceptance cannot fit within enforceable limits, report NOT VERIFIED instead of claiming success. Choose initial values for the supported host/pilot, then tune from real evidence rather than adopting a universal time limit.

**Classify the reason acceptance did not succeed before prescribing another code change.** A demonstrated product defect or material scope violation gets a compact gap report to the **same autonomous implementer**: affected original promise, observed failure, exact reproduction when available, and scope of the finding. Let the agent choose the fix; no complex recovery plan by default. If the candidate may be correct but evidence is insufficient, improve the focused independent check **without changing product code**. Fix a broken verification environment as an environment problem; request a source/authority decision only when essential. Neither missing evidence nor a host failure is evidence that the candidate is defective.

As an initial **soft diagnostic checkpoint**, inspect progress after **two post-verification product-correction rounds**, rather than treating two as an unconditional failure threshold. Continue autonomously only if (a) trusted observations show meaningful movement toward satisfying a material criterion or resolving a real blocker, (b) the existing cumulative time/dispatch limits still allow it, and (c) enough capacity remains for fresh independent acceptance. Useful movement may be a previously failing public-interface probe now passing, a concrete regression repaired, or a demonstrably different falsifiable approach to a still-reproduced defect; model confidence, repeated edits, and passing unrelated tests are not progress. Evidence-only rechecks and environment repairs use the same budget but do not consume a product-correction round. Stop early after repeated non-progress; never automatically extend a hard budget, discard a candidate, or require a new approval while already authorized capacity and demonstrable progress remain. A user-authorized continuation can extend the episode's budget while preserving its prior usage and evidence. This is a policy inside the existing correction loop, not a recovery agent or extra stage.

A changed candidate needs fresh current review and proof; independently established observations may guide focused checks only where still applicable. When the **candidate, source, accepted input, and relevant review inputs are unchanged**, a still-valid engineering PASS may be retained while a verifier remedies an evidence-only gap and produces a fresh proof outcome. Never carry a verdict across changed code or changed assumptions on which it depended. Do not launch generic reset agents, repeat full suites without reason, or split issues simply because they are hard. On exhausted authority, limits, or credible non-progress, preserve the candidate and evidence, report what is and is not verified, and give one concrete next action. Budget exhaustion is **not** proof of a defective candidate; measure it separately from true false blocking.

### 4.6 Deliver honestly

**Local acceptance is not external delivery, and accepted child work does not establish parent delivery.** The v0 prototype stops at an accepted local candidate and concise evidence. A scoped child run reports child-only completion until assembled-parent acceptance covers the complete original outcome. The intended product should accept a delivery target at the initial request: **local acceptance**, **PR created**, or **PR merged**. It must keep these as separate verified facts, not treat a local PASS/PROVEN as permission to publish.

A user may explicitly authorize the relevant remote actions up front. Within that scope, Proofline should complete ordinary publication/CI/merge steps without asking for the same permission repeatedly. Confirm remote results by current readback; honor branch protection, current required checks, permissions, and failures. Uncertain effects are reconciled before retries. No target silently grants deployment or unrelated external writes.

Publication/merge integration belongs **after** the lean local prototype and feasibility evidence, preferably using host-native GitHub workflows rather than an elaborate custom delivery controller. Eventually measure total time and human effort **through the requested delivery target**, not merely until local proof. Report partial completion plainly when a remote target cannot be reached.

## 5. Minimal technical architecture

**Start with one primary agent skill and a tiny amount of deterministic glue, not a general-purpose delivery controller.** The default clean success path should use **three top-level model-backed stage dispatches**: implementer, independent reviewer, independent prover. Native tools and reasoning *inside* a stage do not count as extra Proofline stages, but their actual time and tokens count toward delivery cost. This is an initial simplicity target, not a guarantee about provider-level model calls or a cap on legitimate corrections.

Proposed first implementation:

- A single Proofline skill defines the entry flow and short role instructions for direct requests and accepted contracts, including lightweight source re-anchoring and a task-specific inline execution/observation map when relevant.
- A tiny optional read-only adapter consumes approved source-linked P2P Markdown acceptance contracts without importing P2P's controller, approval workflow, or storage protocol.
- Existing host facilities launch the implementer and **fresh independent** reviewer/prover.
- A small trusted helper, *only if genuinely necessary*, freezes Git identity, checks read-only boundaries, records actual host invocation receipts, and validates the final identity match.
- Git and the project's existing tests remain the product-change and evidence mechanisms.
- One compact ignored local run record allows honest resume and diagnostics.

No server, database, permanent telemetry pipeline, universal plugin interface, second contract language, or separate framework per coding host. Proofline works **without P2P installed**; contract compatibility is an input capability, not a runtime dependency.

### Trusted boundaries

The implementer may change only authorized product workspace content. Reviewer/prover run with candidate, source promise, and accepted input protected from writes and with separately bounded scratch. The sandbox must nevertheless support **real executable checks**: generated files, caches, build output, temporary databases, and test fixtures use disposable writable locations without modifying frozen source. If a test requires an execution copy or overlay, verify its source identity and relevant inputs against the frozen candidate before and after testing; a result from a mutable or different product state cannot establish that candidate. Restrict tool/network access and external side effects according to the host's *demonstrated* policy, not verbal promises. Issue text, repository comments, and generated outputs are **untrusted task data**, never new authority.

For v0, choose **one actually qualified local host environment**. macOS + authenticated Codex CLI is a sensible starting candidate because P2P has existing host-isolation experience, but Proofline must independently verify any assumptions its thinner integration relies on. **Before building the full workflow**, demonstrate a minimal host feasibility spike: two fresh independent verifiers, protected exact source/accepted-input/candidate, separately writable scratch, and trustworthy host-issued receipts, against a correct and a deliberately defective candidate. **Run a real build/test or public-interface probe** that requires normal temporary writes, verify source identity remains intact, and demonstrate that unauthorized network/external writes are prevented or explicitly unavailable. If this requires rebuilding a substantial controller, reconsider the host or design before committing to that infrastructure. If isolation and fresh session identity cannot be established, Proofline may show unverified diagnostics but **must not claim independent acceptance**.

Keep the implementation simple enough to substitute host-specific mechanics later if a second host proves worthwhile; do not design a plugin SDK in advance.

### Minimum retained state

Persist only information needed to resume and substantiate acceptance:

| Field | Purpose |
| --- | --- |
| Authoritative original source/revision + accepted direct brief or approved contract revision/authorization | Prevent silent loss of obligations or adoption of unapproved plans |
| Frozen base and candidate Git identity | Bind all checks to exact code |
| Reviewer result and trustworthy invocation/evidence reference | Establish independent engineering/scope judgment |
| Criterion-level prover outcomes and trustworthy invocation/evidence references | Connect each material promise to independent behavioral observations |
| Remaining material gaps, shared budget/usage, and next action | Resume without repeated work or resetting limits |
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

**Simplicity budget:** the normal clean path should need only the authoritative source/accepted input, one implementer stage, one reviewer, one prover, immutable identities, and a compact outcome. Upstream planning is not a Proofline stage but its real cost must be counted in complete-request comparisons. No mandatory separate planner, contract auditor, risk scorer, recovery worker, or model-backed preflight. Before adding any required agent invocation, persistent store, protocol, approval step, or full-suite repetition, demonstrate a concrete failure that a narrower change cannot address and measure its impact on quality, latency, human intervention, and maintenance burden. Prefer removing redundant steps to optimizing them.

If a real failure requires a larger capability, first show that a narrower change cannot solve it. A one-off exception must not quietly become the default path.

**S6 verification experiment (12 October 2026).** Repeated native false certification
of source-domain restrictions survived the narrower prompt remedy. The optional
`--source-challenges` experiment therefore adds one candidate-blind invocation
before implementation: source and public interface guidance are visible, while
base/candidate code, tests, peer verdicts and the private evaluator are inaccessible.
It freezes executable source-derived expectations outside the product. A positive
proof must cite successful native execution of each frozen probe; reviewers and
provers still independently challenge the complete promise. Unsupported probe
expectations are evidence gaps, never new requirements or permission to modify the
promise. The added dispatch consumes the same episode budget and is retained in
the existing stage ledger. This is a qualification experiment, not a new default
or an established coverage guarantee; comparisons remain gated on native rejection,
positive acceptance, binding, isolation and bounded recovery.

## 7. Evaluation: Proofline has to earn its existence

The comparison with P2P is a **product requirement**, not a retrospective marketing exercise. Reuse suitable independent test cases and accounting concepts from [P2P issue #52](https://github.com/grove/promise-to-proof/issues/52), [P2P's live judgment fixtures](https://github.com/grove/promise-to-proof/tree/main/checks/fixtures/live-judgments), and [P2P's delivery measurement work](https://github.com/grove/promise-to-proof/issues/59), **without copying its controller or protocol wholesale**.

### Comparison groups

1. Capable coding agent with ordinary self-checking.
2. The same agent plus one independent reviewer.
3. Full contemporary Promise to Proof.
4. Proofline.

Use the same source request, starting repository state, coding host/model where feasible, tool access, and independently authored correctness expectations. Run both **raw-request cohorts** (all planning work counts) and **shared-preplanned cohorts** (give every workflow the same independently authorized, source-linked contract). Report *delivery-only* and *original-source-to-delivery* cost separately, including upstream planning time, tokens and observed human attention. Do not count pre-existing plans as free or privilege any one workflow with hidden oracle hints.

### Early measurement and full pilot

Start measuring the **lean prototype immediately** after its first real supported-host success and known-defect rejection, before building sophisticated recovery or publication support. A quick paired smoke comparison against an ordinary coding agent can expose large setup or quality problems even earlier; it does **not** replace the planned four-way evaluation. Make an early, explicitly *directional* four-way comparison using compatible local-only tasks; incomplete features and unexecuted cases must remain visible, not be silently excluded. Do not claim end-to-end superiority from an early prototype that lacks the other groups' recovery/delivery capabilities or excludes upstream planning cost.

For the later complete pilot, predeclare a small corpus with at least: a correct low-risk control, an omitted material obligation in a direct **brief or upstream contract** despite its presence in the original source, omitted promised behavior despite green tests, unrequested scope expansion, weak or hollow regression evidence, a meaningful repair, and an exact-candidate change. Include **multiple genuinely correct but structurally different candidates** for the same promise where alternative architectures are allowed; a verifier that rejects a valid implementation because it differs from the suggested test path has a false-blocking defect. Set aside realistic **held-out tasks** (including relevant repository-native integration paths) before tuning the prompts or rubric, and do not use their private oracle findings to iteratively tailor Proofline. Use recorded repetitions and explicit comparable budgets; do not extrapolate a small sample into statistical superiority.

For each assigned episode, retain independently checked completion quality, false acceptance, false blocking, budget exhaustion, failed/blocked/unexecuted status, total elapsed time **through the authorized target**, stage time and observed long-tail cases, actual host/model calls and reported token categories, repair work, and directly observed human intervention. Distinguish unknown cost/attention from zero. Measure time and tokens **per independently satisfactory delivery**, including failed and repeated work.

Use an external oracle or human-reviewed expected behavior fixed before runs; Proofline and P2P must not grade themselves. **Validate the evaluator itself** with known satisfactory controls including alternative valid implementations, and deliberately defective candidates that its private oracle must catch; if those controls fail, do not use that run for quality conclusions. Keep oracle answers out of coding-agent/verifier contexts. Report median and per-task/tail times (a percentile only when sample size supports it), not just the median. Preserve disagreements and false negatives rather than tuning the benchmark until Proofline wins.

**Verification architecture experiment:** separately compare a single *fresh independent checker* responsible for both engineering and adversarial behavioral judgment against two distinct reviewer/prover invocations, on matched frozen candidates and independent ground truth. This is an experiment, **not** permission to drop either assurance responsibility or weaken the production default. Adopt a combined check only if actual false acceptance, false blocking, and useful-delivery cost support it.

### Decision rule

Proofline succeeds if it demonstrates **meaningfully lower overhead while retaining credible independent acceptance**, without a material increase in false acceptance or unacceptable false blocking on the chosen tasks. As a *pilot target*, investigate whether median end-to-end time or tokens per satisfactory delivery can fall by at least **25%** relative to full P2P. That threshold is a hypothesis, not a promise or sufficient statistical finding.

If Proofline is faster because it misses real defects, it **fails**. If its checks block correct code repeatedly, it also fails. Report per-task failures and limitations, not a single blended score.

## 8. Minimum acceptance scenarios for the first working prototype

- **Direct success:** a straightforward promise is implemented without P2P installed; review and proof pass on one unchanged candidate without extra planning or repair calls.
- **Source re-anchoring:** after a simulated compaction or long implementation, the implementer consults the original promise again and flags a missing material criterion before handoff without a new planning stage.
- **Runnable observation path:** task-relevant existing commands/fixtures allow meaningful interface checks with safe scratch; unavailable dependencies are reported honestly rather than replaced with imaginary green evidence.
- **Approved upstream plan:** an exact source-linked, authorized P2P contract is consumed without repeated planning; stable IDs and requirements survive intact.
- **Unapproved or stale plan:** an unapproved, revised, contradictory, or source-unrecoverable contract cannot silently become the accepted input.
- **Narrow v0 contract adapter:** a current approved P2P Markdown contract preserves source and IDs without installing P2P; a legacy/unsupported format returns a named input-readiness gap without inventing approval or importing the delivery controller.
- **Child versus parent:** a proven child contribution never claims full parent acceptance; the combined parent is independently evaluated.
- **Promise lost in planning:** a direct brief or upstream contract omits an explicit material source requirement; independent acceptance detects the gap rather than accepting the narrower input.
- **Missing behavior:** a supplied green test suite misses a promised case; proof independently probes a relevant counterexample and shows the observable gap.
- **Discriminating evidence:** a hollow check that passes both valid and plausible broken behavior cannot prove the criterion; a stronger focused observation can.
- **Change-impact review:** a realistic regression caused by the candidate's changed behavior is identified, while unrelated pre-existing defects and speculative polish do not become blockers.
- **Scope expansion:** the promised behavior works but a separate product behavior is changed; review flags the material unrequested effect.
- **No perfectionist blocking:** a correct low-risk change with optional style/polish suggestions is not blocked; a separately seeded material engineering risk is blocked with evidence.
- **Weak evidence:** circular or over-mocked assertions do not establish a promised public outcome.
- **Repair:** the implementer corrects a real finding; the changed candidate receives fresh independent outcomes.
- **Evidence-only recovery:** correct, unchanged code initially lacks adequate evidence; a better focused check establishes the outcome without an unnecessary product edit or duplicate still-valid engineering review.
- **Environment failure:** missing build/cache/database scratch or a denied check produces an environment/evidence gap, not a fabricated product defect.
- **Risk-aware behavior:** relevant state, authorization or concurrency boundaries are challenged where the promise requires them, without blanket deep suites for low-risk tasks.
- **Stale candidate:** a post-verification edit cannot be accepted under the previous reports.
- **Host boundary unavailable:** a missing independent session, write protection, or required observation produces NOT VERIFIED, not PASS.
- **No external authority:** a local PASS/PROVEN result never pushes or merges without the requested grant.
- **End-to-end budget:** implementation, review, proof and retries share a cumulative limit; resumption cannot reset it, and exhausted work is preserved with honest status.
- **Unproductive continuation:** a bounded non-progress case exits with preserved work and one actionable next step, not an endless silent loop.
- **Productive continuation:** a third correction with independently observable progress may proceed inside the unchanged cumulative budget and verification reserve, whereas repeated ineffective edits stop early.
- **Independent evaluator controls:** the benchmark oracle accepts the known-good candidate and rejects a deliberately defective one without giving workers expected answers.
- **Valid alternatives and holdout:** independently correct but differently structured candidates pass without imposing an implementation technique; untouched held-out tasks reveal overfitting.
- **Upfront publication authority (later milestone):** a PR/merge target uses explicit standing authority and verifies remote completion without duplicate approval requests.

Test the mechanical behavior deterministically; run the meaningful judgment cases with the **real supported coding host**. Never report mocked stage transport as live evidence.

## 9. Development sequence

### Milestone 0 — Prove the minimal host boundary

With minimal throwaway glue, establish independent fresh invocations, source/accepted-input/candidate write protection, scratch separation, and trusted receipts on the intended host. Exercise one known-correct and one deliberately defective candidate **through actual executable behavior** using disposable writable build/test scratch, with source identity and external-effect restrictions checked.

**Done when:** the actual host boundaries work and can be demonstrated without designing a general-purpose controller. If not, reconsider the host or architectural assumptions before proceeding.

### Milestone A — Lean working path, instrumented from day one

Build the single Proofline entry skill supporting direct requests and the narrow approved P2P Markdown contract input (without a P2P runtime dependency), minimal direct brief, inline task-specific execution map and implementation re-anchoring, exact candidate capture, change-impact-aware review, failure-discriminating proof, shared budget, and compact local-only outcome. Keep the code and instructions small; do not implement every historical P2P edge case.

**Done when:** both input paths reach trustworthy real-host local acceptance with criterion-level evidence; omitted source promises, unapproved contracts, and known behavioral defects are rejected; actual stage/time/usage accounting is available where supported.

### Milestone B — Early head-to-head signal

Run a small, predeclared **directional** four-way comparison on compatible local-only cases before adding complex recovery or publication features. Preserve failures, incomplete functionality, independent oracle judgments, and budget consumption.

**Done when:** there is an honest per-case diagnosis of quality and time overhead, with explicit limits on what the early sample can prove.

### Milestone C — Bounded corrections and target-aware delivery

Add compact actionable feedback and progress-based correction within the cumulative budget and verification reserve, safe recovery from interruptions without duplicated uncertain effects, and the false-green/scope/candidate regression scenarios. Add optional host-native PR/merge execution only under upfront authority, with current remote readback.

**Done when:** a seeded product repair succeeds, an evidence-only gap can be resolved without modifying correct code, stale results cannot pass, resuming cannot evade limits, and authorized remote target handling requires no manual internal-stage coordination.

### Milestone D — Fair full-workflow comparison

Run the complete four-way comparison on raw-request and shared-preplanned input cohorts, accounting separately for upstream planning and delivery, including meaningful repairs, alternative correct implementations, held-out tasks, and comparable delivery targets where supported; publish per-task outcomes, false acceptances, false blocking, long-tail delays, and explicit unknowns. Run a separately controlled one-checker versus two-checker experiment when warranted.

**Done when:** there is defensible evidence about where Proofline is better, worse, or still inconclusive—and why.

### Milestone E — Earned improvements only

Apply the **smallest changes** justified by observed failures or material overhead. Defer multi-host support, rich portability, extra agents, integrations, and new control machinery until evidence shows they earn their cost.

## 10. Open design questions to settle with experiments

1. Can the chosen coding host establish sufficiently independent, write-protected reviewer and prover contexts **without** rebuilding P2P's full controller? Settle feasibility before expanding architecture.
2. Do direct briefs and imported approved P2P plans preserve material source obligations without a new planning/audit stage or more than a tiny read-only adapter?
3. Is review-first gating cheaper overall, or does it create enough false blocking that a different ordering is better?
4. What is the smallest persisted receipt and budget record that makes interruption/resume honest and avoids duplicated external effects or reset limits?
5. What end-to-end budget and correction allowance minimize long-tail delays **without** excessive false blocking?
6. How much defect-detection value is gained by separate reviewer and prover invocations versus one truly independent checker responsible for both? Keep the initial production default until evidence justifies changing it.
7. Can upfront, action-scoped authorization and host-native publication deliver a verified PR or merge without introducing another orchestration framework?
8. Can focused evidence-only remediation and a flexible verification budget reserve improve completion without extra ceremony or unsound review reuse?
9. When does optional upstream acceptance planning improve overall satisfactory delivery enough to justify its full cost?

These are evidence questions. Avoid settling them by designing elaborate abstractions up front.

## 11. Definition of success

The end state is deliberately simple:

**A user states an outcome or supplies a previously authorized, source-grounded contract and delivery target. A capable agent builds the frozen promise with minimal interference and a bounded budget. Independent evidence challenges it against the original source and exact code, establishing success or naming a concrete gap. Only separately authorized external effects occur, and P2P-like overhead is not recreated.**

**Proofline should be easier to use than P2P, simpler to maintain than P2P, and at least as honest about what has—not—been proven.** Its central advantage should be *maximum useful autonomy: less management of the coding agent's process, continuously accessible promises, runnable observations, precise correction feedback, and better independent evidence*.

If the experiments do not support those goals, change the hypothesis before adding more machinery.
