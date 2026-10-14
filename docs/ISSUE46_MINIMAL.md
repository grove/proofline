# #46: simplified experiment, model-free early stop

**INCONCLUSIVE — STOPPED NOT QUALIFIED.** No live coding models ran. All eight
assigned slots remain NOT_EXECUTED. This is the authorized bounded preflight
stop, not a checklist-effectiveness result or a completed matched comparison.

The [small proposal](../evaluation/checklist_minimal/README.md) compares ordinary
Luna:medium with the same Luna:medium plus a source-grounded checklist. It
selects four fresh Schedule requests at exact base commits, retains original
request bytes, uses a balanced eight-cell order and equal 900-second coding /
1200-second assignment limits, and charges checklist preparation to its arm.
There is no new live runner, mandatory planning stage, nested Codex launch,
router, correction loop, production CLI change or dependency installation.

The branch starts from main `e1ffa58`, using a separate local clone because the
original checkout contains uncommitted #47 work and read-only Git metadata.
[PR #47](https://github.com/grove/proofline/pull/47), its branch, the original
working tree and its failed qualification evidence remain untouched. Historical
cohorts are not reused or pooled. This PR relates to #46 and does not close it.

## What the preflight actually observed

The declaration froze before the one native preflight. Its input freeze is
`b6fc4bf890ae37d7d360d60c21fd15cf71159dc224de2dc0cae66e298c23176f`.
The cap was 120 seconds; measured preflight duration was **0.619414 seconds**.
The supported Codex CLI 0.162.1 launched a Python canary directly, under the
existing native permission profile with managed configuration included.
The native process returned exit 0 with complete bounded stdout, but that alone
was insufficient for qualification:

- Writes to original source, guidance, candidate, candidate Git metadata and
  the separate receipt directory were denied; mode changes were denied.
- Scratch writes were allowed and network access was denied, with a successful
  outside-sandbox loopback control.
- Separate private receipt/oracle/other-role canaries were unreadable.
- **The actual oracle fixture read was allowed**:
  `/private/tmp/proofline-issue46-minimal/checks/fixtures/s0/oracle.py`.
- Original inputs and private canary contents remained unchanged.

Thus the reused `host.assess_canary` returned NOT VERIFIED. The temporary
checkout layout did not establish exclusion of evaluator material outside the
allowed inputs. This is an observation about this exact layout/profile, not
proof that every supported host layout fails or that coding would be incorrect.
The exact reason that path remained readable was not diagnosed. No broader
permissions, denied-path changes, alternate layout, patched runner or retry
were attempted. Per the requested stop rule, infrastructure work stopped.

The unchanged repository tests were **not reached**. Neither were reference /
alternative / omission controls, typed-package installation, writable-worker
qualification, source-to-oracle adjudication or catalog readback. Preliminary
non-native import inspection also found `mock` and Python 3.14 `setuptools`
unavailable; this is a secondary unresolved prerequisite, not an observed
repository-suite or packaging failure. No dependency shim was introduced.

[Preflight and all-slot ledger](../evaluation/results/issue46-minimal-checklist/preflight.json)
· [Exact native boundary receipt](../evaluation/results/issue46-minimal-checklist/boundary.json)
· [Complete captured preflight files](../evaluation/results/issue46-minimal-checklist/preflight-evidence.zip)
· [Artifact hashes](../evaluation/results/issue46-minimal-checklist/hashes.json).
The new regression test checks that a failed canary prevents subsequent tests
and preserves all eight unexecuted slots; it is an offline transport double,
not additional native qualification.

## Costs, review and next decision

[Accounting](../evaluation/results/issue46-minimal-checklist/accounting.json)
records zero coding-model/CLI-reviewer dispatches and zero coding tokens. The
0.619414 seconds is the measured preflight only. Full organizer elapsed time,
checklist authoring/grounding/distribution effort, session organizer tokens,
active human effort and actual billed dollars are UNKNOWN. The separately
user-authorized session review is not a free paid-model substitute: its tokens
and billing are likewise UNKNOWN. No dollars-per-correct-delivery calculation
or end-to-end savings claim is possible, and unknown preparation costs must
never be reported as zero. Shared preparation would be allocated equally;
checklist-specific costs would all be charged to B in any later study.

[Independent review](../evaluation/results/issue46-minimal-checklist/review.md)
by the explicitly authorized `/root/study_review` session agent supports
publication as an honest early-stop proposal, **not live execution**. It reviewed
candidate `4f1dec9` and the exact input freeze above. The final additions attach
that review and disclose its findings; frozen study inputs and receipts are
unchanged. This is not human certification, independent native reproduction or
a qualified source oracle.

The review also identifies a static timing limit: the script checks remaining
time before native commands, but hashing, archive extraction, snapshots, Git
preparation and startup imports are not covered by a whole-process watchdog.
The measured stop occurred well inside the declared 120-second budget; do not
represent the script as a hard deadline or use this recipe to retry the freeze.
The historical single-library cohort also falls short of #46's intended breadth
and substantial/ongoing work. These limits belong in any future selection
review. For deadline acceptance, an undocumented but source-faithful usable
interface is not a defect: the original request did not promise new docs.

Recommendation: **INCONCLUSIVE on checklist value; retain the simpler design
as a proposal only.** There are no implementation outcomes to compare. Do not
add infrastructure to salvage this declaration. A later attempt would need an
existing supported layout that actually excludes private assessment inputs,
working original tests/packaging tools, independently source-qualified controls,
and a fresh freeze/review. None are established by this PR.

Do not request live spending authorization for the failed freeze. If a later
proposal qualifies, obtain new explicit authorization for that exact freeze,
Luna:medium, host and eight-attempt budget before any live expenditure. The
present authorization permits PR creation and the one session review agent;
it permits neither live coding experiments nor merging nor closing #46.
