[vNext 5/9] Make direct Proofline invocation simple for coding agents

## Why
Today's `run` workflow asks users to prepare a source Markdown file and a JSON list of argv arrays. An existing agent should invoke Proofline without imposing manual ceremony on its user.

## Scope
Design a thin CLI/skill interface over `check` and the optional managed `run` pathway. Allow the agent to pass the full original request and explicitly chosen checks directly or by existing files; keep advanced file-based inputs available. The existing agent—not Proofline—chooses relevant commands, informed by real repository facts.

## Acceptance criteria
- [ ] Document one short, realistic command/skill example for check-only use and an optional example for managed `run`.
- [ ] A direct request requires no P2P issue, Intentline contract, acceptance-planning stage, or second model call.
- [ ] Full original source survives intact (including multiline input) and is recorded in the frozen evidence. No silent summarization or reinterpretation.
- [ ] Command invocation uses a safely parsed argv list with no implicit shell execution, and remains reproducible in receipts.
- [ ] Helpful validation errors describe missing commands, unavailable runtime, and source/candidate limitations without launching models.
- [ ] Tests demonstrate equivalence of direct and existing file inputs and preserve backward compatibility.
- [ ] Update `README.md` and `SKILL.md` with task-oriented, minimal usage.

## Out of scope
Auto-writing acceptance tests, another planning interface, an interactive wizard, or installation of repository dependencies.

## Dependencies / order
After #11 (check-only mode).

---

## Optional Intentline coordination (13 October 2026)

Keep the **no-Intentline** direct `check` UX as the default; no new required `intentline` command, model, config, file ceremony or approval. The same existing agent may **optionally** use Intentline's plan skill or manually source-grounded `R` rows for an important task, then invoke Proofline's ordinary explicit argv checks. Show both workflows in README/SKILL with one short example each, clearly distinguishing the **future** [#23 Intentline consumer](https://github.com/grove/proofline/issues/23) from present capabilities. Preserve the whole original request; planning suggestions must not narrow it. This issue does **not** implement the adapter; the CLI should stay simple even if the adapter never ships. Test direct usage and absence of a peer dependency.
