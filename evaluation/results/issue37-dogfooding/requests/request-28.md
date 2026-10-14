Rename Proofline agent skill to proofline-check

## Why
Intentline's existing skills use the `<project>-<action>` convention (`intentline-plan`, `intentline-audit`, `intentline-slice`), while Proofline's single skill currently declares `name: proofline` in its root `SKILL.md`. Renaming that skill to **`proofline-check`** makes its purpose clearer and makes explicit invocation consistent across the two projects.

## Scope
Rename **the skill**, not the Proofline project, Python package, or CLI. Keep **one** Proofline skill covering check-only verification, evidence/feedback, optional Intentline input, and optional managed `run`. Prioritize agent-friendly discoverability, correct installation guidance, and minimal change.

## Acceptance criteria
- [ ] Change the canonical skill's frontmatter to `name: proofline-check` with a concise trigger-focused description: use after an existing coding agent implements a change to execute selected tests against the frozen candidate and report actual failures / missing evidence; mention that it is optional and model-free in `check` mode.
- [ ] Determine and document the supported skill installation/discovery path for at least Codex and Claude Code. If a standard `skills/proofline-check/SKILL.md` directory is needed, provide it without silently breaking the existing root `SKILL.md` entry or creating two independently maintained divergent instructions. Preserve relative documentation/code links under the chosen layout.
- [ ] Update README, skill instructions, examples, and any current references that invoke or install the skill under its old name. Distinguish **automatic discovery when installed** from guaranteed automatic invocation (not guaranteed).
- [ ] Preserve the existing `proofline.py check`, `run`, and `status` commands, direct/file source inputs, optional Intentline integration, zero-extra-model check-only behavior, receipt integrity, and safety boundaries. Do **not** rename the CLI to `proofline-check`.
- [ ] Test/validate skill metadata, single canonical definition or explicit compatibility alias (if needed), relative link resolution, supported install packaging, and documentation consistency. If an old explicit skill invocation is no longer supported, document the migration clearly rather than claiming unverified compatibility.
- [ ] Confirm no new mandatory planning, reviewer/prover, authorization, or model-dispatch stage was introduced.

## Out of scope
Splitting Proofline into multiple skills merely for symmetry, changing Intentline skill names, merging repositories, altering check execution semantics, or making skill discovery mandatory for direct CLI use.

## Notes
Current skill: [root SKILL.md](https://github.com/grove/proofline/blob/main/SKILL.md). Intentline comparison: [intentline-plan](https://github.com/grove/intentline/blob/main/skills/intentline-plan/SKILL.md). This is a naming/documentation/discoverability improvement, **not** an independently demonstrated correctness improvement.