---
name: proofline
description: Model-free checks on an existing frozen working candidate, or one optional coding attempt, without universal correctness certification.
---

Use the [supported local runner](proofline.py) `check` command for existing
agent work: **zero model dispatches**, **macOS**, Python 3.11+ and **Codex CLI
0.162.1** (sandbox only; no model authentication needed). The optional `run`
command needs authentication and a clean Git source for one coding attempt.
Historical `deliver` and `resume` are unsupported. Direct requests need no
P2P/Intentline workflow.

Use the simplest form first: preserve the user's **entire original
request** in `--request` (verbatim text) or `--request-stdin` (exact UTF-8
bytes including terminal newlines) and provide one explicit project-native
`--command` per relevant check. Neither a saved request file nor
`checks.json` is required. For durable/complex inputs, the original
`--source FILE` and `--checks FILE` interfaces still work unchanged.
Each `--command` is POSIX-quoted **argv**, not a shell invocation; no
expansion, glob, pipe or command substitution runs. Provide an absolute
executable path and quote arguments accurately; use `--checks` JSON for
difficult argv. Source and check input forms are each mutually exclusive.

Do not fabricate expected results, silently narrow requested behavior,
or modify unrelated user work. `check` copies current tracked bytes plus non-ignored
untracked files, preserves regular file modes and safe relative file symlinks,
and omits tracked deletions. Pause edits during capture; changes detected across
two reads invalidate the snapshot. Ignored untracked files, Git metadata and
empty directories are excluded. Submodules, nested repositories, directory or
escaping symlinks, FIFOs, sockets and devices have no supported observation path.
There is no unprotected fallback on unsupported files or platforms. The source
repository stays untouched, including its index, dirty and untracked work.

```sh
/opt/homebrew/bin/python3.14 -B /absolute/path/to/proofline/proofline.py check \
  --repo /absolute/path/to/product \
  --request 'Reject whitespace-only usernames; preserve Unicode and CLI behavior.' \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests'
```

No new model is dispatched for this existing-agent check. For a managed one-agent
attempt on a **clean** source repository, `run` accepts the same direct inputs:

```sh
/opt/homebrew/bin/python3.14 -B /absolute/path/to/proofline/proofline.py run \
  --repo /absolute/path/to/clean-product \
  --request 'Add --version while preserving CLI output.' \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests' \
  --stage-seconds 600
```

For multiline source from a command-capable host, use `--request-stdin`
with a pipe that preserves exact UTF-8 bytes; avoid trimming or summarizing
the request.

The output must be a new directory outside the source repository (default:
system temporary directory, `proofline-check/<unique-id>`). Preserve it for
later evidence readback. `check` never resets, stashes or commits in the source;
only its isolated copy receives a Git identity. For managed coding, use `run`
with the same arguments and `--stage-seconds 600` on a clean source.

The coding agent owns strategy, self-checks and repairs. Proofline runs the
caller-selected commands against its frozen, read-only candidate under native
protection. The source, selected files, command arrays and separate host receipts
are bound to the report. All time counts toward the episode budget. No network
access, dependency installation, AI reviewer/prover, correction, publication,
merge or deployment runs. Linux offline CI does not establish a native macOS
qualification. Existing authorization rules still apply; local checking never
permits external mutations.

Use `proofline.py status <report.json>` to revalidate the frozen inputs and receipts.
New live-source edits require a new `check`; an old record refers to its old snapshot.
Report the exact candidate, actual named check results and uncovered
requirements. `CHECKS PASSED` means only that listed commands exited
successfully. Distinguish `CHECKS FAILED`, `CHECKS UNAVAILABLE`,
`EXECUTION UNAVAILABLE`, and `STALE CHECKS`. Never call checks
full-promise certification or claim a PR/merge occurred.

**Optional Intentline guidance:** For complex requests, this same existing
agent may use [Intentline's plan skill](https://github.com/grove/intentline/blob/main/skills/intentline-plan/SKILL.md)
to identify proposed `R` outcomes, edge cases, and candidate checks, then call
Proofline `check` against the unchanged original request and chosen argv.
That plan is advisory, not proven behavior or permission. **No Intentline
installation, contract adoption, extra approval, or model stage is required**.
The optional export adapter is **not yet implemented**; see
[#23](https://github.com/grove/proofline/issues/23).

The [vNext contract](DESIGN.md) and [open issues](https://github.com/grove/proofline/issues)
retain zero-extra-model check-only use and prioritize useful failure feedback.
New mandatory stages must demonstrate improvements in independently
correct deliveries that justify their latency, cost and blocking risk.
