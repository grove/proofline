# Proofline agent skill — compatibility entry

The single maintained agent skill has moved to
[**`proofline-check`**](skills/proofline-check/SKILL.md).
This root `SKILL.md` remains so existing links and readers of the old
root file have a clear migration path; it is **not** a second discoverable
skill or a `proofline` alias.

Install the `proofline-check` skill in a supported agent skills directory,
or use the repository's checked-in Codex and Claude Code discovery links.
For the exact paths and installation steps, see
[Skill installation and migration](README.md#agent-skill-proofline-check).

**Explicit invocation migration:** Codex `$proofline` becomes
`$proofline-check`; Claude Code `/proofline` becomes
`/proofline-check`. Existing user-level installations of the old skill
are not automatically renamed; remove or migrate them manually to avoid
two competing skill definitions.

The standalone Python CLI is unchanged:
`proofline.py check`, `proofline.py run`, and `proofline.py status`
still work without any skill installation.
