Qualify source-faithful behavioral oracles before further live studies

## Why

Merged [PR #35](https://github.com/grove/proofline/pull/35) / [#34](https://github.com/grove/proofline/issues/34) found that the hidden cache oracle required `ValueError` for an invalid TTL while the **original request specified no exception class**; Luna raised `TypeError`. The candidate was improperly labeled `FALSE_ACCEPTANCE` by the frozen grader. A second issue caused the grader's ancillary repository-test flag to say tests failed because a subprocess lacked the product import path. The original study was correctly preserved instead of silently regraded.

Before another costly model comparison, ensure a grader cannot turn an *unpromised implementation choice* or broken test execution into a measured model failure.

## Small scope

- [ ] Add a **source-to-oracle preflight** for **new/future** evaluation declarations: each material expected output, exception, compatibility behavior and negative case must point to an exact original-source clause or a documented, independently adjudicated interpretation. Record acceptable alternatives and genuine ambiguities. If an expectation is unsupported or disputed, flag the declaration **NOT QUALIFIED** *before* model dispatch; never count the disputed case as a real defect.
- [ ] Add a regression for the specific `cache-expiry` problem: both meaningful invalid-TTL rejections must be accepted **when the request does not prescribe an exception class**; a request explicitly requiring `ValueError` may still require it. Preserve separately whatever other constraints the source *does* demand (e.g. no loader call). Do not broaden acceptance to arbitrary exceptions.
- [ ] Fix the **future-study** repository-test subprocess working-directory/import-path handling so that a green original test suite is recorded as green, and an intentionally failing suite is recorded as failing. Preserve actual argv, status and receipt.
- [ ] Re-run small reference, independently plausible alternative, and deliberately defective controls to ensure that relaxing an unjustified expectation doesn't make genuinely defective code pass. Include positive and negative regression tests for source/oracle disagreements, unknown evidence and the import-path defect.
- [ ] Keep original requests and grading expectations of [#34's frozen v1](https://github.com/grove/proofline/blob/main/evaluation/recovery/FREEZE.json), [#32](https://github.com/grove/proofline/issues/32) and [#16](https://github.com/grove/proofline/issues/16) **byte-for-byte intact**. The old disputed result stays reported as disputed; never change historical scores, retroactively declare success, or re-run an old approval.
- [ ] Document a **short, reusable review checklist** for future oracle authors. It may use human/independent adjudication; do not add a mandatory model reviewer, general oracle-synthesis service or new framework.

## Acceptance

A future study can demonstrate offline that (1) ambiguous source obligations are either correctly supported across permitted implementations or rejected before live spending, (2) meaningful defects still fail, and (3) repository-test status is correct for both passing and failing controls. Use **zero live coding-model calls**. Changes should be narrow and should not modify Proofline's optional model-free `check` behavior.

## Non-goals

No new benchmark corpus, no live model evaluation, no universal semantic proof, no dependency or permission expansion. Keep implementation and test artifacts compact. Open a PR; **do not merge without explicit approval**.

**Priority:** First, before any new medium/high or recovery evaluation.