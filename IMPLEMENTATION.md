# Proofline — Implementation plan

**Status:** Execution roadmap v1 · 12 October 2026 (S0–S2 demonstrated; qualified P2P delivery and fixed 240-second S3 comparison complete; S4 local recovery and S5 authorized remote gates demonstrated)

**Design authority:** [DESIGN.md v0.5](./DESIGN.md) — the product contract and safety boundaries live there.  
**Objective:** Make a capable coding agent deliver the *complete authorized promise*, with independently credible evidence, minimal human coordination, and substantially less wasted work than a heavy controller.

> **Build a thin, trustworthy delivery boundary around an autonomous coding agent. Do not build another coding-agent workflow engine.**

**Current execution:** S0's native boundary and seven fresh Codex invocations
passed on the recorded macOS host: correct and alternative candidates passed,
and both verifiers rejected the seeded whitespace defect. See the
[live evidence and failed experiments](docs/S0-CODEX-RUNNER.md).
S1 also passed two real direct-delivery tasks and live omission/regression
controls; see [S1 evidence](docs/S1-DIRECT-DELIVERY.md). S2's narrow
[contract adapter](docs/S2-CONTRACT-INPUT.md) passed its actual approved-contract
and full negative-control gate; see [S2 evidence](docs/S2-LIVE-EVIDENCE.md).
Milestone A's local gates pass within these recorded boundaries. S3's
[fixed 240-second four-way repeat](docs/S3-COMPARISON.md) completed all 20
assignments. Ordinary agent, agent plus review and Proofline each delivered four
correct positive cases; P2P delivered two, retaining two on-time handoff failures
from mislabeling expected exit-2 probes as passed. All four cohorts correctly
rejected the source omission. P2P's complete native implementation, review and
proof and its input-gap control qualified before the repeat. Proofline completed
the alternative whose prover previously timed out. Earlier 180-second failures,
qualification costs and unknown costs remain visible. The P2P default suite's
pre-existing packaging failure and corrected macOS temporary-path fixture are
documented; its suite is not claimed to pass. These are small CLI observations,
not a statistical advantage claim. S4 demonstrates native product repair, unchanged evidence recovery and separate-process resume, with deterministic budget/progress controls; see [S4 evidence](docs/S4-RECOVERY.md). S5 demonstrates an explicitly authorized real PR/merge with separate-process recovery and exact-tree remote readback on the disposable repository; its protected-CI and transformed-merge limits are recorded in [S5 evidence](docs/S5-PUBLICATION.md). S6 remains deferred. The original
[Linux NO-GO](docs/S0-HOST-FEASIBILITY.md) remains historical evidence.
This status does not change any gate below.

This plan orders engineering work; it is **not** an alternative acceptance agreement and cannot revise the user's promise. The original source and any separately approved acceptance contract remain binding. Where this roadmap and DESIGN.md differ, **DESIGN.md wins** until the product owner authorizes a design change.

## 1. Working rules for implementation

1. **One vertical slice at a time.** Each slice must produce a demonstrable capability and independent observations before the next starts. Internal tasks/files are the implementer's choice; avoid an up-front forest of issues or architectural components.
2. **Maximum useful autonomy.** Provide the source, accepted criteria, relevant repository commands, permitted effects, and expected observable outcomes. Do not prescribe algorithms, file-edit order, intermediate model reports, or speculative refactors.
3. **Protect the promise and candidate mechanically.** Freeze source/contract/base identities before work, then the exact candidate before checking. Reviewer and prover use fresh independent contexts and cannot modify the candidate or binding inputs.
4. **Test correctness, not reassuring narratives.** Use real host invocations for judgment, independently fixed expected behavior, credible public-interface observations, and both known-good and deliberately defective examples. Offline mocks validate mechanics, **not** actual model judgment.
5. **Bound the entire episode.** Track implementation, review, proof, correction, and remote work in one cumulative budget. Enforce what the host can enforce; mark unavailable usage as unknown. Keep verification capacity available.
6. **Prefer reuse to ceremony.** Use Git, project-native commands, host-provided sandboxing, and a single compact ignored run record. No mandatory planner, extra grader, database, multi-host framework, or second acceptance protocol.
7. **Never overclaim.** Local acceptance is not a published PR or merge. A missing isolation guarantee, stale receipt, inconclusive criterion, or unapproved input is **NOT VERIFIED**, not success.
8. **Resolve blockers at the right layer.** Product bugs go to the implementer; weak evidence goes to the verifier; broken tooling goes to the environment; source or authority conflicts go to the owner/upstream planner.

**Ownership:** The user/product owner defines and authorizes promises. P2P `plan-acceptance` may express them as approved contracts; `create-parent-issue` and `slice-contract` are optional upstream organizational tools, not Proofline runtime steps. Proofline owns implementation and independent acceptance. It must not invent new obligations or silently narrow existing ones.

## 2. Delivery sequence and dependency gates

| Slice | Design milestone | Useful increment | Start only after |
| --- | --- | --- | --- |
| **S0 — Host feasibility** | 0 | Real isolated review/proof with trusted receipts | This plan |
| **S1 — Direct local delivery** | A, part 1 | One request → code → frozen candidate → review → proof → local outcome | S0 passes |
| **S2 — Approved contracts** | A, part 2 | Same path accepts an approved source-linked P2P contract | S1 passes |
| **S3 — Early comparison** | B | Honest, directional four-way local-delivery results | S2 passes |
| **S4 — Bounded correction** | C, part 1 | Product repair, evidence-only recovery, durable budget/resume | S3 findings recorded |
| **S5 — Authorized publication** | C, part 2 | Optional PR and merge with remote readback | S4 passes |
| **S6 — Full pilot and simplify** | D–E | Defensible comparison and evidence-based next decision | S5 passes, or compare only supported targets and mark gaps |

**Do not claim DESIGN Milestone A is complete until both S1 and S2 pass.** S1 is intentionally an earlier working increment; S3 happens before expensive recovery or publication engineering. For S6, lack of a comparable delivery target is an explicit limitation, never a reason to silently exclude a cohort.

## 3. Slice definitions and acceptance gates

### S0 — Prove the real host boundary before building the controller

**Build:** On one qualified host (initial candidate: macOS + authenticated Codex CLI), use minimal disposable glue to launch *fresh* reviewer and prover invocations against one known-correct and one deliberately defective Git candidate. Verify isolation in the actual host, not just via role prompts.

**Acceptance — demonstrate all of these with real executions:**

- **H1:** Host-issued invocation evidence distinguishes implementer, reviewer, and prover; the verifiers have fresh contexts and do not inherit implementation conversation, each other's verdict, or private benchmark oracle.
- **H2:** Original source, accepted input, base, candidate bytes/modes, and trusted receipts cannot be modified by verifiers; independently writable temporary build/test output works. An attempted product write is rejected or detected and invalidates acceptance.
- **H3:** At least one real executable/public-interface probe can accept the correct candidate and expose the seeded fault; identity before/after the probe matches the candidate. A mutable execution copy is checked against the frozen snapshot.
- **H4:** Network/external writes are denied or explicitly unavailable under verified host policy. Tests use disposable resources and never depend on unauthorized external effects.
- **H5:** Missing invocation evidence, changed source/candidate, inaccessible required observation, or ineffective isolation cannot produce PASS/PROVEN in a deterministic negative check.

**Artifact:** A short reproducible host-feasibility note with exact host/version, observed commands, capability limits, receipts, failure examples, and a go/no-go decision; retain minimal executable fixtures.

**Stop/pivot:** If secure independent checking requires recreating a substantial P2P-like controller, test another host/boundary or revise the design *before* developing S1. Do not downgrade the meaning of independent acceptance to keep moving.

### S1 — First complete autonomous local delivery (direct request)

**Build:** One user-facing `/proofline` entry point with thin deterministic glue. Accept a direct request, preserve its verbatim authority/source and small source-grounded brief, freeze the comparison base, run one autonomous implementer, freeze its candidate, then independently review and prove it (review first; skip proof on a material review blocker). Return the exact local candidate and human-readable outcome.

**Acceptance:**

- **D1:** A low-risk real repository task succeeds *without P2P installed or a planning agent*. The implementer has a task-specific inline map of relevant commands/entry points and re-anchors to the original promise before handoff.
- **D2:** Both independent judgments refer to the same immutable candidate, original source, accepted-input identity, and base. An edit after checking invalidates the old verdicts.
- **D3:** Review detects a seeded material scope/regression defect but does not block a correct change for optional polish. Proof gives each material criterion SATISFIED, VIOLATED, or NOT VERIFIED with an observation discriminating plausible failure; existing green tests alone are insufficient.
- **D4:** A known-bad candidate, missing promise in the direct brief, hollow check, absent verifier, or missing material evidence cannot be accepted. A known-good structurally different implementation can pass.
- **D5:** One compact ignored record holds identities, per-stage receipts, criterion outcomes, cumulative elapsed/dispatch accounting, available usage, and candidate location. Local success explicitly says **not published/merged**. No remote action occurs.

**Implementation freedom:** Suggested boundaries are entry skill, host invocation, Git identity, acceptance/report validation, and minimal state. They may begin in one small Python package; split code only as real complexity emerges. Prefer existing project tests and host features over custom frameworks.

**Gate:** Run deterministic identity/permission/report tests **and** real-host success/defect judgment tests. Never substitute a mocked model result for a real verifier acceptance claim.

### S2 — Consume approved acceptance plans without replanning

**Build:** Add a narrowly supported **read-only adapter** for the current P2P Markdown contract. Read the exact approved revision and trusted approval binding (or explicit adoption by the user of that exact version); resolve original source bytes and revision, stable criterion IDs, exclusions, parent/child contribution, and prerequisites. Use the **same** S1 implementation/review/proof path.

**Acceptance:**

- **P1:** An actual approved, source-linked P2P contract runs without P2P's controller or runtime installed; criterion IDs and material source promises reach both independent acceptance roles unchanged.
- **P2:** Unapproved, stale, unsupported, contradictory, source-unrecoverable, or prerequisite-incomplete input returns an actionable **input-readiness** outcome, not a fabricated product defect or an invented approval.
- **P3:** If an approved contract or direct brief omits an explicit material original-source promise, the independent checker still detects it. Planned tests and oracles are guidance, not proof.
- **P4:** Acceptance of a child contribution never asserts parent completion; combined-parent acceptance checks the original complete promise against one assembled frozen candidate.

**Gate:** Reuse S1 positive and negative cases for both input paths. Avoid supporting legacy checkpoint/approval formats or general contract grammars without demonstrated need.

### S3 — Measure before building sophisticated recovery

**Build:** Predeclare a small local-only task set and independently fixed answer keys, including correct alternative implementations, missing behavior behind green tests, false scope changes, source-promise omissions, and weak evidence. Compare: (1) ordinary agent, (2) ordinary agent plus independent review, (3) current P2P, and (4) Proofline. Use the same starting source and host/model where feasible.

**Acceptance:**

- **B1:** All assigned tasks have explicit outcomes (accepted correctly, false accepted, false blocked, failed, budget exhausted, or not executed); oracle sanity checks accept known-good alternatives and reject known-bad cases.
- **B2:** Report actual elapsed time, model dispatches/available token costs, reviewer/prover time, human interventions, and time **per independently satisfactory delivery**, including unsuccessful runs. Unknown is never recorded as zero.
- **B3:** Distinguish raw-request from shared-preplanned inputs, upstream planning cost from delivery cost, and supported from unsupported delivery targets. Keep benchmark-only oracle data out of agent and verifier contexts.
- **B4:** Publish the per-case directional findings and largest observed failure/overhead mechanisms without a statistical superiority claim or tuning away inconvenient failures.

**Gate:** If a seeded serious defect is falsely accepted, repair the trust boundary before expanding automation. If correct candidates are frequently blocked, investigate evidence quality and review prompts rather than weakening the promise.

### S4 — Make correction useful, bounded, and resumable

**Build:** On a failed current candidate, classify **product defect / insufficient evidence / environment failure / authority or source gap**. Send only actionable reproduction and affected source obligations to the same implementer when product code is wrong. Improve focused verification without changing correct code when evidence is weak. Persist a cumulative budget and enough state to resume honestly.

**Acceptance:**

- **R1:** A seeded incomplete product becomes independently accepted after a targeted repair; a changed candidate gets fresh review and proof. No verdict carries across changed code.
- **R2:** A sound unchanged candidate with weak evidence becomes verified through an evidence-only recheck; retain an engineering PASS only where its exact inputs and applicability are unchanged.
- **R3:** A broken test environment produces an environment/evidence status rather than a claimed product defect.
- **R4:** Real elapsed time and host dispatch limits cover *all* stages across resume, including repairs and verification. Preserve a configurable verification reserve; unavailable usage remains unknown. Exhaustion preserves work with a concrete next action.
- **R5:** Two correction rounds are a **soft progress checkpoint**, not an unconditional stop. A further round is possible within the same budget only with observable progress and enough room for independent checking; repeated non-progress stops early.
- **R6:** Interrupted or uncertain workers/effects are reconciled before redispatch; resume cannot silently duplicate uncertain effects, reset budget, or accept stale artifacts.

**Gate:** Exercise seeded product repair, evidence-only repair, environment failure, non-progress termination, productive third round, and interruption/restart in real and deterministic tests as appropriate. Do not introduce separate recovery agents.

### S5 — Reach the authorized delivery target

**Build:** Add optional user-authorized `PR created` and `PR merged` targets using host-native GitHub/Git facilities. Local acceptance remains available without GitHub. Effect grants must be explicit at the initial request and scoped to the relevant repository and action; independent checking never creates effect authority.

**Acceptance:**

- **G1:** No push, PR, comment, merge, deployment, or external write occurs without matching user authorization. Repeat approval is not demanded when the original grant still covers the action.
- **G2:** After local acceptance, an authorized PR is published and confirmed by **remote readback** of the current head, base, and intended candidate; branch name or a saved success note is not proof.
- **G3:** An authorized merge respects required checks, protections, current remote state, and candidate equivalence. Rebase/squash/conflict/CI changes cannot silently inherit stale verdicts; report a precise partial outcome when equivalence or readback is unavailable.
- **G4:** Retries reconcile uncertain remote effects before retrying; a local-only request remains local.

**Gate:** Validate with safe disposable repositories/fakes for fault injection and at least one real, explicitly authorized remote test before claiming end-to-end support. No deployment scope is implied.

### S6 — Fair full pilot, then improve only what earns its cost

**Build:** Predeclare realistic raw-request and shared-preplanned cohorts, keep held-out tasks away from prompt tuning, and run the four-way comparison through comparable authorized delivery targets. Include repair-heavy and long-tail cases and correct implementations using different approaches. Optionally run a separate one-checker-versus-two-checker experiment; keep the production assurance standard meanwhile.

**Acceptance:**

- **E1:** Independent ground truth and known-good/known-bad evaluator controls are fixed before runs. Every assigned case, failure, false acceptance, false blocking, incomplete target, and unknown cost is visible.
- **E2:** Report paired per-task quality, end-to-end time, calls, cost where available, human attention, long-tail behavior, and *cost per satisfactory delivery*; count planning and rework in the full-request view.
- **E3:** Evaluate the DESIGN.md pilot hypothesis of at least **25%** less median time or tokens against full P2P as a *target to investigate*, **not** a proven benefit or sufficient basis for a quality claim.
- **E4:** Continue, simplify, change host, or abandon the hypothesis based on observed trust and usefulness. Faster false acceptance is failure; chronic false blocking is also failure. Only add stages or infrastructure when a narrower remedy has demonstrably failed.

## 4. Shared implementation guardrails

**Candidate and state:** Preserve unrelated user changes with a dedicated workspace where necessary. Bind source/accepted-input/base/candidate to reconstructible identities; include relevant file modes and source bytes, not movable branch names. Run tests in isolated writable scratch or a verified execution copy. Store a *single* minimal run record outside product changes, with references to evidence and trusted invocation receipts. Invalid or incomplete records must fail closed.

**Verifier responsibilities:** Review independently inspects source, accepted input, and diff for credible engineering, scope, and regression failures. Proof independently derives observable expectations *before* trusting implementer tests, then challenges material criteria through suitable seams and meaningful counterexamples. Reviewer and prover remain fresh, distinct stages; review-first is the v0 ordering. No blanket deep test suite or arbitrary count of tests.

**Observation and honest results:** A clean success path targets **one implementer + one reviewer + one prover stage dispatch**. Internal agent actions still count toward actual cost. Display in everyday language: confirmed outcome, failed/unknown criteria, exact candidate location, whether publication/merge was verified, and one useful next action. Retain raw evidence without making it the normal user experience.

**No speculative framework:** Start with a single skill and the smallest Python/Git glue demonstrated necessary by S0. Avoid hard-coded multiprovider abstractions, generic contract languages, event sourcing, extra acceptance stores, routine re-planning, mandatory retrospectives, and independent agents that merely rephrase another agent's conclusions.

## 5. Testing strategy: evidence by layer

| Layer | What it establishes | What it cannot establish |
| --- | --- | --- |
| Deterministic/unit tests | Git identity checks, parsing failure paths, permission gates, verdict aggregation, budget persistence, state reconciliation | Model quality or honest independent proof |
| Real-host integration | Fresh invocation boundaries, writable scratch, protected candidate, host receipts, actual executable observations | Correctness of every future product change |
| Independently scored judgment fixtures | Detection of deliberately broken behavior, acceptance of valid alternatives, false blocking/acceptance | Statistical advantage over P2P |
| Four-way task pilot | Relative success, latency, token/cost and human effort, including failures | Universal superiority outside sampled hosts/tasks |

For every new failure mode, add the **smallest reproducible regression test** at the appropriate layer. Do not allow a mock-only green suite to certify real independent acceptance.

## 6. Agent handoff and decision policy

At the start of each slice, provide a short task handoff, **not another lengthy plan**:

- The slice ID and relevant DESIGN.md sections; this plan's existing observable exit criteria.
- Exact source/contract revision, frozen repository base, and permitted actions.
- Relevant run/test commands and environment affordances, with unknowns labeled.
- Known fixture/oracle boundaries and the agreed episode budget.
- One instruction: **implement the smallest complete slice, demonstrate its criteria, and report honest unresolved gaps.**

An implementation agent may choose modules, algorithms, tests, internal sub-tasks, and refactors inside scope. It must not alter acceptance criteria to make its work pass. A material change to product scope or required authority returns to the product owner/upstream acceptance planning; an ordinary technical choice does not.

**At every slice boundary**, record only: what ran on the real host, the observable pass/fail evidence, open material gaps, consumed budget/cost if available, and whether the next dependency gate is satisfied. If it is not, correct the named issue or pivot; do not merely declare the slice complete. Avoid creating issue hierarchies or approval ceremonies for these records.

**First action:** Implement **S0** on the chosen supported host. Run the two real candidates through independent review/proof, verify isolation and execution scratch, capture trusted receipts, and decide whether the host boundary is viable. No broader Proofline implementation should precede that evidence.
