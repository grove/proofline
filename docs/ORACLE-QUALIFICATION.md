# Future source-faithful oracle checklist (#36)

This applies to **new** evaluations only. The published #16/#32 cohorts and
[#34 v1 freeze](../evaluation/recovery/FREEZE.json), scores, approvals, grader,
requests, and results are immutable. The #34 cache grade remains **disputed**;
none of these controls regrade a historical candidate, reopen its spending
approval, or authorize another model comparison.

## Author/reviewer checklist (before any model dispatch)

1. **Pin the original bytes.** Freeze the complete request and oracle script
   SHA-256, unique study ID, and source/seed identities. Do not infer source
   intent from a later candidate, a grader assertion, or a passing test.
2. **Enumerate all material assertions independently of the declaration.**
   Include each expected output, exception/class policy, compatibility
   requirement, negative case, and grouped case label. Match this *complete*
   inventory to the actual oracle and runner; missing or invented items block.
3. **Cite a unique exact source clause** for each claim, or record a separately
   authored interpretation with its written reference, rationale, and independent
   adjudicator. A reviewer must judge *entailment*, not merely substring
   presence. Tooling cannot verify reviewer identity or semantic entailment.
4. **Record genuine ambiguity and acceptable alternatives.** For input
   validation without a promised exception class, do **not** demand only
   ValueError. The cache control allows exactly ValueError or TypeError,
   requires rejection before the loader on hit and miss, and rejects arbitrary
   errors. If the source explicitly says ValueError, require it. If a claim
   would exclude another plausible correct implementation, broaden the
   source-supported acceptance or flag **NOT QUALIFIED**.
5. **Record unknowns and disputes as blockers**, not candidate failures.
   Source mismatch, oracle drift, missing case coverage, missing independent
   adjudication, an invalid receipt, or unclear original requirements stop
   **before** live spending. Obtain independent written adjudication or revise
   the *new* declaration, never retroactively modify old results.
6. **Exercise offline controls before authorization.** A source-faithful
   reference and meaningful alternative must pass; deliberately defective
   implementations must fail. Add both positive and negative disagreement
   tests and verify repository-test status with one passing and one
   intentionally failing original suite. Check actual child argv, product
   working directory, return code, stdout/stderr, timeout, and retained receipt.
7. **Review and approve a separate future freeze** only after preflight and
   controls are green. Never treat a passing finite oracle, green repository
   suite, or textual source-citation check as proof of full correctness.

## Narrow executable demonstrator

- [Source/oracle preflight](../evaluation/source_preflight.py) checks an
  independently supplied case inventory, exact request and oracle hashes,
  exact clauses, ambiguity/alternatives and separate supported adjudication.
  It returns **NOT QUALIFIED** rather than a candidate score for missing,
  disputed, unknown or unsupported expectations. Every future evaluator must
  call this check **before** dispatch, not after observing candidates.
  The example future_cache.preflight(declaration) needs no candidate and must
  return QUALIFIED before any future runner may start a model.
- [Future-only cache oracle](../evaluation/future_cache.py) runs the source
  qualification *before* executing any oracle. It enforces two narrowly
  meaningful invalid-TTL exception choices only when no class is specified,
  while retaining no-loader, cache-expiry and non-aliasing checks. The
  separate repository-test child runs from the **snapshotted product root**
  (python -B -m unittest discover -s tests). Its actual argv, cwd,
  exit code, stdout/stderr, timeout and status (PASSED, FAILED, UNAVAILABLE)
  survive in the repository test receipt; these results are separate from
  behavioral cases and never silently become false acceptances. The child
  invokes the resolved Python executable; its literal argv must exactly match
  the outer grader's pinned interpreter and expected options. Alias strings
  are never treated as equivalent during receipt validation. See the
  [macOS alias regression results (#41)](ISSUE41.md).
- [Regression controls](../tests/test_source_oracles.py) exercise reference,
  TypeError alternative, source-prescribed ValueError, cache defects,
  arbitrary exceptions, early loader calls, deliberately red repository
  tests, missing/unknown/disputed evidence and mismatched declaration hashes.

Run without model calls or native Codex dependencies:

    python -B -m unittest tests.test_source_oracles -v

This is a small authored control, **not** a semantic proof, a new live study,
an oracle-synthesis framework, or independent human review. Before new
live evaluation, an actual independent reviewer must attest the declaration
and the chosen assertion inventory. Proofline's optional model-free check
command is unchanged.
