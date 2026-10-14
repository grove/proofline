# Acceptance checklist — issue 14

The complete original request controls. This index does not replace it or certify quality. Implementation choices not prescribed by the request remain open.

- C1: Give exact argv, exit status, elapsed time, bounded output references and candidate/source identity for each check. [Source](../requests/issue-14.md#L10).
- C2: Show supplied expected/observed values only where applicable; do not invent expectations. [Source](../requests/issue-14.md#L11).
- C3: Separate failed checks, missing evidence, boundary/environment unavailability, timeouts and stale receipts. [Source](../requests/issue-14.md#L12).
- C4: Give concise actionable guidance while retaining raw logs separately. [Source](../requests/issue-14.md#L13).
- C5: Keep successful results short and model-free. [Source](../requests/issue-14.md#L14).
- C6: Test passes/failures, missing/truncated output, timeouts, mutation attempts, bad metadata and status readback. [Source](../requests/issue-14.md#L15).
- C7: Support optional source IDs, distinguishing actual failures from untested promises and proposed behavior; ordinary feedback stays usable without a mapping. [Source](../requests/issue-14.md#L27).
- C8: Add no reviewer, mandatory analysis bundle, automatic diagnosis claims or correction. [Source](../requests/issue-14.md#L18).

Ambiguities: no particular new helper/module names, new option spellings, exception classes or documentation wording are prescribed beyond the original request. Existing compatibility promises still apply.
