[vNext 4/9] Add check-only mode for an existing coding agent

## Why
The supported `proofline.py run` starts a new Codex coding attempt. An already-running coding agent should be able to invoke Proofline's useful mechanical checks **without a second model dispatch**. This is vNext's key functional milestone.

## Scope
Introduce `proofline.py check` as a local, model-free mode accepting an existing repository/candidate, the original source request and explicit executable checks. Choose a documented, safe way to snapshot even a dirty working tree, including relevant untracked files, without deleting or modifying user work. Execute checks against an isolated frozen candidate, not a mutable live worktree. Reuse qualified sandbox, receipt, time-budget and integrity mechanisms where possible.

## Acceptance criteria
- [ ] A coding agent can submit an existing candidate without Proofline launching Codex or any other model (assert zero model dispatches).
- [ ] The source repository remains byte-for-byte untouched, including dirty and untracked work; no reset, stash, auto-commit, or unapproved publication.
- [ ] The selected candidate, original request and exact command argument lists are bound to the record. Status detects changed or missing evidence and does not reuse stale checks.
- [ ] Selected checks run on the frozen candidate in the native protected boundary with explicit budgets and without granting network access or external effects.
- [ ] Failures, unavailable executions, and completed passes are distinct. `CHECKS PASSED` is scoped to the actual commands, never full-promise certification.
- [ ] Deterministic tests cover dirty worktrees, untracked files, freeze/receipt tampering, failed/unavailable checks, zero model dispatch, and source preservation.
- [ ] Clearly disclose any initially unsupported platforms or file types; no silent fallback to unprotected checks.

## Out of scope
No correction agent, new reviewer/prover, risk scorer, PR/merge, or automatic generation of acceptance tests.

## Dependencies / order
After #8 and the extraction boundary in #10. Prioritize this before the other functional features.