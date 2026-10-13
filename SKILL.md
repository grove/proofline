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

Preserve the user's **entire original request** in a file outside product
changes. Select relevant project-native executable checks and store each
exact argv list in `checks.json`, also outside product changes. Do not
fabricate expectations, silently narrow requested behavior, or modify
unrelated user work. `check` copies current tracked bytes plus non-ignored
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
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --output /absolute/path/outside/product/check-record \
  --seconds 900 --check-seconds 120
```

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

The [vNext contract](DESIGN.md) and [open issues](https://github.com/grove/proofline/issues)
retain zero-extra-model check-only use and prioritize useful failure feedback.
New mandatory stages must demonstrate improvements in independently
correct deliveries that justify their latency, cost and blocking risk.
