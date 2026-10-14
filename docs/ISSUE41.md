# Homebrew interpreter receipt regression (#41)

Observed on 2026-10-14 on the supported macOS 26.6.2 arm64 / Python 3.14.8
host, with Codex CLI 0.162.1. These are local macOS observations, separate
from Linux CI. No coding models were invoked by these checks.

At baseline `9c9d894` (including #39), the oracle launched its repository-test
child with the Homebrew alias:

    /opt/homebrew/opt/python@3.14/bin/python3.14

The parent required the resolved executable:

    /opt/homebrew/Cellar/python@3.14/3.14.8_2/Frameworks/Python.framework/Versions/3.14/bin/python3.14

The strings differed even when the child succeeded. Running the source-oracle
suite reproduced all ten reported failures: valid and defective controls
became `ORACLE UNAVAILABLE` rather than their expected verdicts.

The future-only child now **executes and records the canonical path**, and
validation compares its literal argv to the outer grader's already selected
`PYTHON` identity. It does not re-resolve a potentially changed caller alias
or accept an arbitrary alias after execution. The child still uses the
snapshotted product root and retains exit status, stdout/stderr, timeout,
truncation and command evidence separately from behavioral correctness.

Reproduce from the checkout, deliberately using the affected Homebrew alias:

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B -m unittest tests.test_source_oracles -v
/opt/homebrew/opt/python@3.14/bin/python3.14 -B -m unittest discover -s tests -v
PROOFLINE_NATIVE_TESTS=1 /opt/homebrew/opt/python@3.14/bin/python3.14 -B -m unittest tests.test_codex_live.LiveTransportTests.test_oracle_executes_generated_product_inside_read_only_native_boundary -v
```

| Local observation | Before | After |
| --- | --- | --- |
| Source-oracle suite | 10 tests, 10 failures | 14 tests, all passed |
| Normal repository suite | Not rerun at baseline | 255 tests, OK (8 opt-in/platform tests skipped) |
| Fixed behavioral oracle controls | Not rerun at baseline | 3 tests, all passed |
| Reference / TypeError alternative | `ORACLE UNAVAILABLE` | `PASSED`; original suite `PASSED` |
| Deliberate cache defects | `ORACLE UNAVAILABLE` | `FAILED`; original suite `PASSED` |
| Intentionally red original suite | `ORACLE UNAVAILABLE` | Behavioral `PASSED`; original suite `FAILED`, stderr retained |
| Relative/absolute executable aliases; Homebrew alias/Cellar launches | Missing focused controls | Canonical recorded child argv, passing suites |
| Literal alias, unrelated executable, changed link, altered argv/cwd/evidence | Missing focused controls | `ORACLE UNAVAILABLE`, no product verdict |
| Consistent timeout receipt | Missing focused control | Behavioral `PASSED`; original suite `UNAVAILABLE`, partial stdout/stderr retained |
| Existing native read-only oracle regression | Not rerun at baseline | Passed on host |

A separate model-free `future_cache.grade(..., trusted=False)` smoke check
used an authored reference fixture, the existing candidate snapshot and native
Codex sandbox. It returned behavioral `PASSED`, repository tests `PASSED`,
`inputs_unchanged: true` and `model_dispatches: 0`. Its child receipt recorded
the exact Cellar executable above followed by
`-B -m unittest discover -s tests`, the snapshotted product cwd, exit code 0,
empty stdout, the passing unittest report in stderr, and false timeout and
truncation flags.

The session sandbox initially refused the existing nested native sandbox with
`sandbox-exec: sandbox_apply: Operation not permitted`; the host retry passed
with native protection enabled. No unprotected fallback was used.

Published #16, #32 and #34 study bytes, scores and receipts are unchanged.
These finite controls do not regrade them or establish whole-product correctness.
