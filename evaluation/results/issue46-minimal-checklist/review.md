What this change does: It replaces the proposed study architecture with four Schedule requests, a short checklist arm, and a small model-free prerequisite script. It records the first native boundary failure and stops with all eight coding slots unexecuted. It does not establish checklist effectiveness.

Verdict: Publishable as an honest early-stop proposal with this review attached. **STOPPED_NOT_QUALIFIED for live execution.** Do not retry this declaration, authorize coding against this freeze, merge, close #46, or replace PR #47 on the strength of this review.

## Identity and scope

Reviewer: `/root/study_review`, a separate agent in the current Codex session, authorized for this one review. I share the session instructions and filesystem with the organizer. I did not author or edit the study, receive coding-worker outcomes, launch coding models, dispatch a Codex CLI reviewer, run a native preflight, or mutate GitHub. No coding-worker outcomes exist. This is not human review, a blind study, a cost-free review, semantic certification, or independent execution of the native observation. Session review tokens and billing are unknown.

Exact reviewed candidate:

- Repository: `/private/tmp/proofline-issue46-minimal`.
- Branch: `study/46-minimal-checklist`.
- Candidate commit: `4f1dec98b6d7d5544639dfce2b0ccb67df970ccc`.
- Candidate tree: `2e32dc99ae43d8cec7eff0a3d5bbda00fd40128d`.
- Base `origin/main`: `e1ffa583c43c1c52a6f6402a07b23f045317b278`.
- Study: `issue46-minimal-checklist-v1`.
- Input FREEZE.json SHA-256: `b6fc4bf890ae37d7d360d60c21fd15cf71159dc224de2dc0cae66e298c23176f`.

The candidate was clean before and after the offline test. Its diff adds only the minimal-study documentation, inputs, stopped results, prerequisite script, and one test. No production transport/check code or historical study file is changed. That supports preservation of prior evidence in this candidate; I did not inspect or change remote PR #47 or the organizer's original dirty checkout.

## Findings, ordered by severity

### Must fix before publication

None found for publication specifically as an early-stop proposal. The limitations below must remain visible. They do not justify altering the failed freeze or adding infrastructure.

### Blocking for live execution, already disclosed

1. **The exact native layout did not exclude an evaluator fixture** (`evaluation/results/issue46-minimal-checklist/boundary.json`; `checks/host_probe.py:240-305`).
   - What this is: The existing canary requires denied protected writes and denied evaluator reads, usable scratch, denied network, and unchanged inputs. It does not treat process exit 0 as qualification.
   - Problem: The captured stdout reports `actual_oracle: allowed` for the existing public `checks/fixtures/s0/oracle.py`, so the assessment correctly returns `NOT VERIFIED`. Separate private receipt/oracle/other-role canaries were denied. This is not evidence that newly authored private probes leaked, or that every supported host layout fails.
   - Fix: Preserve the stop. A later, separately authorized proposal would need an existing supported layout that demonstrates the required exclusion, then a fresh freeze and review. Do not repair or broaden this declaration.
   - If skipped: A live comparison could expose assessment material or claim a boundary that was never established. The present candidate does neither.

2. **There is no qualified source-to-oracle assessment or executable comparison** (`evaluation/checklist_minimal/README.md:124-174`; `evaluation/results/issue46-minimal-checklist/preflight.json`).
   - What this is: Whole-request success needs source-faithful positive/negative probes, accepted alternative implementations, deliberate omissions, ordinary compatibility checks, and installation checks.
   - Problem: The original suite, reference/alternative/omission controls, writable-worker boundary, typed installation, and model-free catalog readback were not reached. There are no hidden probes or task-specific control outcomes to certify. This review of wording cannot replace them.
   - Fix: Keep `NOT QUALIFIED`, eight `NOT_EXECUTED` slots, and `INCONCLUSIVE`. Any future study needs these prerequisites before new live authorization; this failed declaration ends here.
   - If skipped: A green suite or upstream reference could be mistaken for complete source acceptance. The candidate explicitly rejects that inference.

### Nonblocking limitations for this publication

3. **The corpus is substantially narrower than #46 requested** (`evaluation/checklist_minimal/README.md:11-20`; `requests/issue46.json`).
   - What this is: #46 asks for four fresh, real, substantial requests and prefers natural ongoing work. These are four retrospective changes in one small library, including two tag interfaces and a small typed-package marker change.
   - Problem: They provide useful finite seams but weak task diversity, limited natural documentation obligations, and no evidence of uncontaminated training data. Later base archives already contain earlier Schedule features: next-tag's base contains `until` and `get_jobs`, and typed's base contains all three earlier interfaces. That is normal upstream context, not evidence of worker leakage, but further limits diversity. No coding outcomes were available for outcome-driven selection.
   - Fix: Describe this corpus as a limited proposal rather than a representative fulfillment of the desired substantial-task study. Any broader corpus belongs in a fresh proposal, not a swap or retry of this freeze.
   - If skipped: Even a future eight-cell result could be overstated as evidence about varied whole-request delivery. The current document acknowledges the narrow corpus and makes no such result claim.

4. **Material preparation and review costs are unknown** (`evaluation/results/issue46-minimal-checklist/accounting.json`; `docs/ISSUE46_MINIMAL.md`, Costs, review and next decision).
   - What this is: The measured native preflight took 0.6194139998406172 seconds. Coding dispatches and coding tokens are zero.
   - Problem: That time is not total organizer elapsed time. Checklist authoring/grounding/distribution, organizer and session-review tokens, active human effort, and actual billing are null/UNKNOWN. The stopped result cannot satisfy the originally desired measured checklist-overhead comparison or a dollars-per-correct-delivery analysis.
   - Fix: Keep unknown values unknown and refrain from savings or cost-effectiveness claims. Charge checklist-specific overhead to B and allocate shared overhead equally in any later study.
   - If skipped: Preparation could be presented as free despite the considerable source-selection, archive, documentation, and review work. The candidate's accounting is appropriately frank.

5. **The prerequisite script's 120-second value is not a hard whole-process deadline** (`evaluation/checklist_minimal/preflight.py:18-70`).
   - What this is: `remaining()` bounds the version, canary, and test invocation when called. Input hashing, archive extraction, snapshots, and Git preparation run between those calls; existing Git helpers have their own timeouts.
   - Problem: On a slow future invocation those intervening operations can consume or exceed the remaining campaign time before the next check. Startup imports also precede the measured interval. This is a static limit of the script, not an observed timeout or budget failure: the recorded invocation stopped well below 120 seconds.
   - Fix: Do not call this script a hard watchdog or use its recipe to retry the stopped freeze. Preserve this artifact; any future bounded proposal must account for preparation inside its actual execution limit without adding infrastructure to salvage this one.
   - If skipped: A future run could exceed the advertised wall limit before it records exhaustion. It does not invalidate the observed 0.619414-second stop.

## Source obligations, alternatives, and fairness

I read all four complete request Markdown files and their retained JSON bodies, not just the checklists. Each quoted source fragment occurs in its supplied request. All four Markdown files exactly equal the retained title, two LF characters, and original body bytes, including CRLF and trailing spaces. This checks preservation against the fetched records; I did not independently refetch GitHub text or authenticate its collection history.

- Deadline: `Job.until` and stopping after the supplied time follow the two-line request. Argument types, string formats, exception classes, equality at the deadline, and new documentation are unspecified. The README's “documented usable deadline form” should be read as an example of sufficient usable evidence, not a new documentation obligation. An undocumented but otherwise source-faithful candidate must not be marked defective solely on that wording.
- Retrieve: Returning matching Job instances with their other tags is supported. Returning removed jobs from `Scheduler.clear(...)` is explicitly offered as an alternative and must remain acceptable. A separate logging subsystem, exact order, a copied list, or identical upstream interface design is not promised. Multiple tags and GUIDs are source examples, not hidden oracle values.
- Next tag: The source spells `schedule.next_run(tag)` and its example supports `None` for absent/canceled jobs. The base API uses the earliest next run across jobs, so extending that meaning to matching jobs is reasonable compatibility guidance; unsupported exact invalid-tag errors and the new `Scheduler.get_next_run` spelling cannot become mandatory source defects.
- Typed: A `py.typed` marker must reach the installed package so the reported missing-stubs problem is addressed. A checkout-only empty file is insufficient evidence. The request does not mandate a packaging implementation, mypy version, or a completely type-correct caller project. No installation or diagnostic behavior was executed here.

The planned A/B inputs, base bytes, Luna:medium setting, ordinary tests, one-attempt policy, 900-second coding limit, and 1200-second assignment limit match. A/B, B/A, A/B, B/A is balanced serial ordering. Checklist preparation is expressly allocated to B and unused time is not transferred. These are reasonable design declarations; the actual worker prompts, catalog, private controls, writable roles, and assessor operation remain unqualified. Full original requests control both arms, and ambiguity must remain DISPUTED/UNKNOWN rather than become invented defects.

The intervention is appropriately small: no new live runner, planner, router, nested model launch, correction loop, dependency, or production CLI change. Most of the 868 added text lines and eight archives are provenance/reporting overhead rather than intervention logic. That overhead is real and unmeasured, not evidence that the proposal is cheap. Stopping now is the lean correct outcome; further engineering would contradict the authorized stop.

## Model-free verification performed

- Verified all 24 input hashes in FREEZE.json and all four result-artifact hashes in hashes.json.
- Recomputed the Python and Codex binary hashes; both match the recorded runtime hashes. I did not execute Codex.
- Reconstructed Git object trees from all eight tar archives, including names, blob contents, executable modes, and symlinks. All match the declared base/reference trees. This does not separately authenticate upstream commit ancestry.
- Checked ZIP CRCs, its 83 member names, and exact equality of captured preflight/boundary JSON and source bytes with the published artifacts. No unsafe absolute/traversal member names appeared.
- Scanned captured ZIP bytes for common credential-token patterns; no hits appeared. The fixture Git metadata uses a synthetic identity. Published paths reveal temporary checkout layout, not retrieved credentials; this scan is not a general secret-discovery guarantee.
- Read the existing snapshot, canary assessment, native command receipt, coding-attempt, live command construction, and recovery invoke paths. No model path is called by this preflight, and failed boundary assessment precedes original tests.
- Ran `/opt/homebrew/bin/python3.14 -B -m unittest tests.test_checklist_minimal_preflight -v`: one test passed. It uses an offline boundary double and asserts that original tests are not invoked and all eight slots remain unexecuted. It is not native boundary qualification.

The captured native receipt is internally consistent with the published stop: exit 0, complete small stdout, denied protected writes, allowed scratch, denied network with an outside-sandbox loopback control, unchanged inputs, and the one disqualifying oracle-fixture read. Rechecking artifact integrity is not independently reproducing the observation or certifying semantic acceptance.

Verdict: Ship this exact stopped proposal with the review as publication evidence; keep #46 open and PR #47 preserved. Live-execution verdict: **NOT QUALIFIED**. Checklist-value recommendation: **INCONCLUSIVE**.

Not checked: No native retry, worker launch, source-control qualification, original Schedule test suite, package installation, catalog access, remote PR state, or billing. No study files were edited.
Risk: No efficacy or total-cost result exists; this review cannot authorize spending, merge, or semantic certification.
