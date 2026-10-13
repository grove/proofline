---
name: proofline-check
description: After an existing coding agent implements a change, optionally run selected executable checks against a frozen candidate and report observed failures and missing evidence. The check-only mode invokes no models; managed coding and correction are opt-in.
---

Use the [supported local runner](https://github.com/grove/proofline/blob/main/proofline.py) `check` command for existing
agent work: **zero model dispatches**, **macOS**, Python 3.11+ and **Codex CLI
0.162.1** (sandbox only; no model authentication needed). The optional `run`
command needs authentication and a clean Git source for one coding attempt.
Only `run --correct-once` opts in to one follow-up correction on that same
native implementer thread; successful first passes never dispatch another turn.
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
access, dependency installation, AI reviewer/prover, publication,
merge or deployment runs. Linux offline CI does not establish a native macOS
qualification. Existing authorization rules still apply; local checking never
permits external mutations.

**Optional managed correction (#15):** Add `--correct-once` only to `run`.
Require a failed selected executable check with intact bound native evidence
and a Python `AssertionError` diagnostic. Every selected check must be
available; environment errors, arbitrary nonzero exits, timeouts, truncated
logs, stale inputs, caller annotations and advisory promise/Intentline gaps
cannot trigger a turn. Unsupported failure formats remain for the caller.
Proofline resumes the bound original implementer once with the unchanged
full source and exact native observations, copies and freezes a new candidate,
then reruns all selected checks. One `--seconds` budget covers the whole
episode; neither correction nor interruption resets it. The initial report
is retained at `initial/report.json` and checked again by `status`.
Dispatch slots are reserved before launch and an uncertain interrupted slot
cannot be reused. Controller resume is unsupported; never silently start a
new episode. A repeated defect stops with its actual failed/unavailable status,
not another correction or automatic acceptance certification. `check`
continues to dispatch zero models and leaves corrections to the existing agent.

For failed checks, read the bounded CLI **Feedback** summary first; consult
`report.json` -> `feedback.checks` for exact argv, exit status, elapsed
time, candidate/source identity, and `receipts/check-NNN.json` for the native
bounded stdout/stderr. Treat timeouts, missing executables, truncated logs,
sandbox failure and stale evidence as **unavailable**, not implementation
failures. Do not invent a failure's expected/observed behavior.

When the caller already knows a specific expected/observed case, optionally
attach `--failure-details /private/failure-details.json` containing rows
`{"index":0,"outcome_ids":["R2"],"expected":"accepted","observed":"rejected"}`.
The observed text must be present in the host-captured failed-check output;
otherwise it is **not** reported as observed. Expected text and R IDs remain
unverified caller claims; the optional #13 source mapping can validate ID and
command associations, not semantic completeness. No new
AI invocation, workflow, or mandatory metadata file is needed.

**Optional promise mapping (no extra model):** When the same agent or
caller already has a few source-grounded outcomes, provide
`--promises /private/promises.json` only to `check`. The file is a small
JSON object with `schema_version: 1`, `source_sha256` of the **entire
exact original UTF-8 request**, and `requirements` containing unique `R1`,
`R2` ... entries. Each row needs a short `statement`, a `source_refs` list
of `{"source_id":"S1","line_start":1,"line_end":1,"quote":"exact original line"}`,
and `checks` entries of `{"index":0,"argv":[...]}` matching *exactly* the
selected check at that zero-based index; empty `checks` is allowed and means
**NOT DEMONSTRATED**. Optional `kind` is outcome/constraint/exception and
`oracle` is only a **proposed expectation**, never executable proof.
An optional `candidate_tree` pins one specific frozen Git tree; mismatches
fail before native checks. Keep the original source unchanged and never
represent an omitted source clause as approved scope.

To look for overlooked user promises **without another agent**, optionally
reread the *entire original source* and supplied rows/checks once, then add
`review: {"performed":true,"proposals":[...]}`. Each advisory proposal
needs a source-quoted `statement` and `suggested_check` (text only,
never executed). Do not fabricate source quotes, confidence or authority.
If no review occurred, omit it: the default is `performed:false`.
Even if the reviewer found zero gaps, completeness remains **UNKNOWN**.
The new `promise_evidence` report records linked passes (limited evidence),
actual failures, unavailable checks and unlinked/not demonstrated R rows,
plus proposal provenance. Source identity, exact check argv, frozen candidate,
mapping and receipts are checked again by `status`. To display **all** original
request text, call `proofline.py status RECORD --show-source`.
For the exact JSON shape and a concrete example, see [README](https://github.com/grove/proofline/blob/main/README.md).
No Intentline, planning stage, approval, or second AI model is required.

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
That plan is advisory, not proven behavior or permission.
**No Intentline installation, contract adoption, extra approval, or model
stage is required by Proofline**.

For an already-prepared **single original-request Intentline JSON export**,
optionally pass `--intentline-export /private/json-export` to `check`
and `--source /private/json-export/source-S1.txt`. The existing agent still
selects real commands, and can optionally provide `--intentline-links
/private/links.json`, e.g. `{"R1":[{"index":0,"argv":["/absolute/python",
"-m","unittest"]}]}` matching the selected check argv **exactly**. If
links are absent, every imported R is NOT DEMONSTRATED; planning notes
alone never execute or certify a test. `--intentline-export` and
`--promises` are mutually exclusive. Unsupported S2 contexts, amendments,
native bundles or partial/symlinked exports are refused without fallback.
See [README](https://github.com/grove/proofline/blob/main/README.md) and [#23](https://github.com/grove/proofline/issues/23).

Preserve Intentline's proposed oracles, boundaries, evidence gaps, constraints
and exclusions **as advisory data**; do not treat `unapproved` or
`operator_asserted_unverified` markers as authenticated consent, independent
acceptance or permission to publish. Never run exported scripts. No Intentline
Python package is imported by the adapter; ordinary check-only runs work
without it.

The [vNext contract](https://github.com/grove/proofline/blob/main/DESIGN.md) and [open issues](https://github.com/grove/proofline/issues)
retain zero-extra-model check-only use and prioritize useful failure feedback.
New mandatory stages must demonstrate improvements in independently
correct deliveries that justify their latency, cost and blocking risk.
