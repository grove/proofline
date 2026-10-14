# Minimal checklist comparison for #46

Question: does a concise acceptance checklist help Luna:medium deliver more of
an original request than ordinary Luna:medium?

This replaces the proposed architecture, not PR #47 or its evidence. The new
branch starts at main `e1ffa58`; #47's branch, dirty local work, archived failures
and NOT QUALIFIED review remain intact. No file under `evaluation/checklist/`
or any historical study is changed. No production code changes are needed.

## Four fresh requests

The corpus consists of four real, retrospective requests from
[Schedule](https://github.com/dbader/schedule), a small Python library. They were
selected by request and executable seam, before any coding-worker outcomes.
They have not been used in Proofline's exposed #16/#32/#34/#38 cohorts or #47.
Their public historical solutions could exist in model training data; this is
not a claim of uncontaminated or representative tasks. Two tasks involve tags
in the same library; the installation task is small. These are limitations on
inference, not extra observations to pool with past studies.

`requests/*.json` retains the fetched original title, body and URL. Each matching
`.md` is exactly `title + "\n\n" + body`, including CRLF and trailing spaces in
GitHub's body. Every worker must receive that entire unchanged file. Issue #46's
original request is also retained. Comments and solution PRs are not worker
inputs. `protocol.json` fixes commits, tree IDs, order and limits. The source
archives retain all tracked files and modes from each base and upstream
reference commit; reference archives are organizer-only controls, never seeds.
The archives include Schedule's license.

## B's entire additional input

Each bracket cites an exact substring of that task's original body. Both arms
receive the full request, identical base bytes and the same ordinary test
command. B receives only its task's following checklist in addition to the
common guidance. These checklists do not prescribe implementation or expose
private test inputs. Source examples already appear in the original request.

**Deadline** ([PR #195](https://github.com/dbader/schedule/pull/195)):

- Provide `Job.until` so a job executes until the supplied time has passed.
  ["Add Job.until function which will execute a job until a certain time is"]
- Check that the scheduled job stops executing after that time.
  ["passed."]

Ambiguity: the request does not specify deadline argument types, string formats,
exact exception classes, equality at the deadline, or documentation. Do not
require the upstream implementation's choices as promises. A documented usable
deadline form is sufficient; exact boundary equality remains disputed.

**Retrieve jobs** ([PR #419](https://github.com/dbader/schedule/pull/419)):

- Enable obtaining matching Job instances by tag as an iterable.
  ["retrieve an `iterable` of `Job` instances"]
- Keep their other tags available for reporting.
  ["log/report on the other tags that have been attached"]
- Check a job with multiple tags and retrieval by a manufactured GUID tag.
  ["multiple `tags` on each `Job`"; "manufactured guids"]
- Consider the request's stated alternative: returning removed jobs from
  `Scheduler.clear(...)`.
  ["The alternative would be to have the `Scheduler.clear(...)` return the list of jobs that it had removed."]

Ambiguity: the original author explicitly offers two interfaces. An independent
assessor must accept either source-faithful route, including its documented
removal semantics. Do not require a list when an iterable is promised, identical
ordering, copied lists, or a new logging subsystem.

**Next run by tag** ([issue #175](https://github.com/dbader/schedule/issues/175)):

- Allow `schedule.next_run(tag)` to look up the next run for that tag.
  ["e.g. schedule.next_run(tag)"]
- Return next-run information for matching jobs.
  ["returns the next run information for the given tag parameter."]
- Return `None` when the tagged item is absent or canceled.
  ["This could also be used to see if the item is scheduled already or it was canceled."]

Ambiguity: preserving untagged `next_run()` is ordinary base compatibility;
`Scheduler.get_next_run` is not a separately promised public spelling. For
multiple matches use the base API's earliest-next-run meaning, subject to
independent review. Do not invent error classes for invalid tag types.

**Typed installation** ([issue #473](https://github.com/dbader/schedule/issues/473)):

- Add the `py.typed` marker so the package is recognized as typed.
  ["add a `py.typed` file to make mypy not complain about missing stubs."]
- Verify the marker survives a package build/installation and importing
  `schedule` no longer produces the reported missing-stubs diagnostic.
  ["with `import schedule` on line 15"; "Skipping analyzing \"schedule\": found module but no type hints or library stubs"]

Ambiguity: this does not require reworking the type hints, one specific packaging
configuration, mypy version, complete type correctness of the caller's project,
or new user documentation. Mere presence of a marker in the checkout does not
establish installation behavior.

## Equal execution and independent assessment

Use existing `checks.coding_attempt.run` once per slot, on a clean isolated seed,
with exact full source, common guidance, `gpt-6-luna` and `medium`. For B append
only the frozen task checklist to guidance. Use the same existing catalog and
native command construction for both arms; freeze their exact runtime identities
before any approved dispatch. Fresh ephemeral threads, no network, no skills,
planner, model reviewer, feedback repair, privileged tests, retries or commits.
The entire enclosing repository, reference archives, other assignments and
assessment inputs remain outside the worker's read allowlist. `project_doc_max_bytes=0`
is already set by the supported transport; ordinary code/docs/public tests are
readable. Checklist construction does not alter the original source.

One initial attempt per slot: 900 seconds including normal self-checks; 1200
seconds total including capture, executable checks and independent assessment;
9600 seconds maximum over all eight slots. Serial balanced order is fixed in
`protocol.json`: A/B, B/A, A/B, B/A. Unused time is not transferred between cells.
All checklist preparation/review/distribution overhead is recorded separately
and charged to B in end-to-end comparisons, not silently deducted from only A
or treated as free. Include shared setup/assessment costs in both arms by equal
allocation; also show actual sequential wall time and incremental B overhead.

After a handoff, freeze the candidate and use supported `proofline.py check`
with the unchanged request and explicit native commands. This is one native
sandbox executing Python/tests directly; neither product nor test launches
another Codex CLI. Use `status` to revalidate frozen source/candidate and host
receipts. Checks are observations, not acceptance certification. Never count
self-reported completion or a green repository suite as whole-request success.

The final assessor must be independent of both coding workers. Before live
spending, independently review source obligations/allowed alternatives and
freeze disjoint probes with reference, genuine alternative and deliberate
omission controls. Reuse existing source preflight and native receipts;
no new grading engine. Do not merely run upstream added tests: those encode
unsupported deadline formats, implementation details and exact interfaces.
For each completed candidate, use the same reviewed assessment for both arms:
read the entire request and candidate; observe positive/negative behavior,
base compatibility and integration at the finite seams; inspect user-facing
assembly, including real typed-package installation. Keep documentary
observations separate from executable evidence. Where a request is ambiguous,
record DISPUTED/UNKNOWN, not a defect or inferred success.

Record every slot as NOT_EXECUTED, UNAVAILABLE, independently correct delivery,
confirmed source defect, correct but unnecessarily blocked, or DISPUTED/UNKNOWN.
An unavailable attempt is not proven wrong. A source omission despite a green
original suite is reported separately. Stop at the first access/isolation,
missing prerequisite, truncated evidence, runtime/input drift, timeout or budget
failure. Preserve all eight slots. No retry, resume, task substitution, expanded
permissions or runner repairs within this declaration.

## Bounded model-free preflight and authorization

The preflight cap is **120 seconds**. First verify frozen inputs/runtime, then
run the existing native read-only boundary canary and an unchanged original
repository test suite on a frozen base. Stop on the first prerequisite failure;
only if it passes proceed to controls, writable-role qualification, packaging
and model-free catalog readback, within the same cap. No model access is claimed
from a canary or catalog listing. No dependency installation, dependency shim,
new sandbox configuration or unprotected fallback is allowed.

`preflight.py` performs only the prerequisite slice and deliberately has no
live execution entry point. Reproduce once into a **new** output directory:

```sh
/opt/homebrew/bin/python3.14 -B -m evaluation.checklist_minimal.preflight \
  /private/tmp/checklist46-preflight-new
```

A prerequisite stop ends this declaration. The remaining controls and complete
source-to-oracle qualification are not presumed to have passed. A fresh
proposal and review are necessary if the environment changes. The current PR
may record that authorized model-free early stop; it does not answer efficacy.

Live expenditure requires both an independent review of the exact final freeze
and fresh explicit user authorization binding that freeze, host, Luna:medium,
eight single attempts and the time/compute cap. #38 approvals do not apply.
An independent review agent in this session was separately authorized; no paid
Codex CLI reviewer/authoring/model calls are authorized. Review is not spending
approval. The user authorizes PR creation only: do not merge, close #46 or run
live coding cells. A NOT QUALIFIED declaration is never offered for live approval.

## Accounting and interpretation

Preserve raw coding events and host receipts, elapsed coding/self-check/evaluator
and audit times, native turns/tool executions, input/cached/output tokens.
Use existing native-event accounting; uncached = input minus cached, never
input plus cached. Include abandoned attempts and preparation failures.
Record separately checklist authoring/grounding, independent review and
distribution elapsed time, model tokens and active human effort. Session-level
organizer/reviewer token usage, billed dollars or human effort that are not
observable remain **UNKNOWN**, not zero. Non-live preparation still has a cost.
Do not claim cost effectiveness when a material cost is unknown. Billing remains
UNKNOWN without actual billing; price sensitivity is separate from billed cost.

Report all eight assigned slots, per-task paired complete-delivery outcomes and
full resources per independently correct delivery, including B's preparation
cost. Four tasks/one attempt cannot establish broad superiority. Missing cells,
all-correct arms or too few defects mean INCONCLUSIVE. State keep/simplify/reject/
inconclusive for this checklist only. A fidelity improvement with greater total
cost must be reported as such. Do not attribute value to Intentline or adopt a
new default from this tiny study.
