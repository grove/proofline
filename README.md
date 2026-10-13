# Proofline

**A small, optional helper to autonomous coding agents.** Proofline preserves
an original request, freezes an existing working candidate, and executes
caller-selected checks without another model dispatch. It also offers one
optional bounded coding attempt. Passing commands are evidence
**only about those commands**, not proof of every requirement.

## Quick start — let the existing agent check its work

No planning step, acceptance-contract file, or test-configuration file is needed.
After implementing a change, the **same coding agent** chooses relevant,
already-available project checks and calls Proofline directly:

```sh
/opt/homebrew/bin/python3.14 -B proofline.py check \
  --repo /absolute/path/to/product \
  --request 'Reject blank usernames while preserving Unicode and CLI compatibility.' \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests' \
  --command '/opt/homebrew/bin/python3.14 -B cli.py --version'
```

This is an example: choose commands and public interfaces that actually exist
in the target repository. `check` captures the working tree (including ordinary
uncommitted changes), runs exactly those checks and **dispatches zero coding
models**. Its returned report names the frozen candidate and any failed or
unavailable checks, not an automatic assertion that every request was fulfilled.

For a bounded **optional managed coding attempt**, use the same direct inputs:

```sh
/opt/homebrew/bin/python3.14 -B proofline.py run \
  --repo /absolute/path/to/clean-product \
  --request 'Add a --version flag without changing existing CLI behavior.' \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests' \
  --stage-seconds 600
```

`run` requires an authenticated Codex CLI and a clean Git source, and launches
one coding attempt. It does **not** add an AI reviewer, prover, planner or PR
publisher. No extra model is launched by `check`.

`--request` is a single **literal** argument: multiline text and terminal
newlines are preserved if the calling host passes them. For an exact multiline
request without shell quoting, use `--request-stdin` and pipe the original
UTF-8 bytes into standard input instead. `--source FILE` remains supported
for saved original request bytes. These three sources are mutually exclusive.

Repeat `--command` for each executable check. Each value is tokenized with
POSIX quoting into one **argv array**, without executing a shell, expanding
environment variables, interpreting pipes or performing command substitutions.
Every executable must have an **absolute path**. For exact complex argv
(e.g. literal spaces, shell metacharacters or arbitrary arguments), keep using
the existing `--checks FILE` JSON format. The two check-input forms are
mutually exclusive. No extra config or dependency installation is performed.

**Optional Intentline-guided workflow (not an integration requirement):**
The existing agent may first use
[Intentline's planning skill](https://github.com/grove/intentline/blob/main/skills/intentline-plan/SKILL.md)
to identify source-grounded `R` requirements and important checks, then use
the ordinary Proofline `check` command above against the **original request**.
That advice is not an independent test result, approval, or replacement for
original source bytes. Automatic consumption of Intentline exports is
**future work in [#23](https://github.com/grove/proofline/issues/23)**;
the CLI does not require or import Intentline.

## Actionable, receipt-grounded feedback

Both \`check\` (zero model calls) and optional managed \`run\` print a **short**
summary of the selected commands. Failing commands show their exact argv
(in the structured report), native exit status, elapsed time, and a bounded
stderr/stdout excerpt with a concrete next action. An unavailable sandbox,
timeout, truncated output, stale evidence or missing executable is **not**
reported as a product defect. Successful commands give one short summary,
not another AI reviewer pass.

\`report.json\` includes \`feedback.checks\` with the exact selected argv,
exit code, elapsed seconds, frozen source SHA-256, candidate commit/tree,
snapshot identity and \`receipts/check-NNN.json#stdout\` / \`#stderr\` references.
The native host receipts are also retained as separate bounded/redacted files
**outside the command-writable scratch and the candidate**. \`status\` validates
their hashes and the frozen inputs; changed or missing evidence becomes
\`STALE CHECKS\`. Full bounded receipts are available on disk; the terminal
does not dump them by default.

If a checker already provides a specific failure example, a caller can attach
**optional** \`--failure-details /private/failure-details.json\`:

\`\`\`json
[
  {
    "index": 0,
    "outcome_ids": ["R2"],
    "expected": "Unicode username accepted",
    "observed": "Unicode rejected"
  }
]
\`\`\`

Indexes are zero-based and correspond to the selected commands. The
\`expected\` field is **caller-supplied, not an independently established
oracle**; the \`observed\` text is displayed only if it literally occurs in
the bounded native stdout/stderr of a failed check. An unsupported or forged
observation is withheld rather than presented as fact. An \`R2\` label is
advisory until optional [#13](https://github.com/grove/proofline/issues/13)
source-to-evidence mapping exists. No unlisted requirement is deemed covered,
and no failed or missing evidence triggers an AI correction by itself.

This file is optional. Ordinary \`--command\` or \`--checks\` invocations
still work unchanged, without Intentline, an acceptance plan, or extra
model dispatches. Live macOS/Codex sandbox qualification is distinct from
offline CI.

## Currently supported

The supported commands are `proofline.py check`, `run` and `status`.
On the qualified **macOS** host (Python 3.11+, Codex CLI **0.162.1**),
`check` uses only the CLI's native sandbox: **zero model dispatches**, no
model settings or authentication needed. `run` optionally dispatches **one**
coding attempt and needs existing authentication and a clean Git source.
Neither mode runs automatic reviewers, provers, corrections, PRs, merges or
deployments. Both leave the source repository untouched.

For longer-lived or automated workflows, the existing **file-based**
interface remains supported: save the exact UTF-8 original request in `source.md`
outside product changes and selected argv arrays in `checks.json`:

```json
[["/opt/homebrew/bin/python3.14", "-B", "-m", "unittest", "discover", "-s", "tests"]]
```

```sh
/opt/homebrew/bin/python3.14 -B proofline.py check \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --output /absolute/path/outside/product/check-record \
  --seconds 900 --check-seconds 120
```

```sh
/opt/homebrew/bin/python3.14 -B proofline.py status /absolute/path/to/report.json
```

`check` selects **current working bytes** of tracked files (including staged
and unstaged work) plus non-ignored untracked files. Deleted tracked files are
omitted; ignored untracked files, Git metadata and empty directories are not
copied. Tracked files remain included even if an ignore rule matches them.
Regular file bytes and modes, and safe relative symlinks to files inside the
snapshot, are preserved. Submodules, nested repositories, directory or escaping
symlinks, FIFOs, sockets and devices are unsupported and rejected when selected;
ignored untracked files remain excluded. Linux and Windows have no supported
execution boundary. There is **no unprotected fallback**.

Pause edits while the candidate is copied; two reads detect changes during
capture and refuse a mixed snapshot. `check` never resets, stashes, commits in,
or writes to the source. Its isolated copy gets its own local Git identity.
The output directory must be new and outside the source repository; by default
it is under the system temporary directory (`proofline-check/<unique-id>`).
Retain that directory if evidence must survive temporary-file cleanup.
The original request bytes, selected file manifest, candidate identity and exact
command arrays are bound to the report and separate host evidence. `status`
detects changed or missing frozen inputs and evidence. Later live-source edits
do not change the old frozen candidate; checking new work requires a new run.

For optional managed coding, use `run` with the same arguments plus
`--stage-seconds 600`. It still requires a clean source repository. The total
`--seconds` budget counts capture, boundary preflight and command execution;
`--check-seconds` caps each selected command. A timeout or unavailable tool
produces unavailable evidence, while an executed nonzero command produces a
failure. No checks run until the native boundary canaries pass.

Checks run against a **frozen, read-only candidate** under native protection,
without network access or writes to product files. No dependency installation
takes place; checks requiring in-tree writes need a different observation path.
A bounded report records exact argv, native execution receipts, usage when
available, a candidate identity, and distinct `CHECKS PASSED`,
`CHECKS FAILED`, `CHECKS UNAVAILABLE`, `EXECUTION UNAVAILABLE` and
`STALE CHECKS` observations. `status` detects candidate/source/check drift
after an apparent success. Partial or unavailable implementation handoffs do
not become successful check claims.

**User journey:** An existing coding agent implements a CLI option, supplies
the complete original request plus selected CLI and regression checks, and
calls `check`. Proofline freezes that work and returns command evidence without
launching another model. The same agent owns any fixes and the final handoff,
including requirements not demonstrated by the selected checks.

The supported runtime keeps separate small modules for CLI, Git snapshots
(`checks/candidate_snapshot.py`), one coding attempt, native checks,
and exact receipt readback. Historical host diagnostics remain available
for offline security testing, not as an extra acceptance stage. Successful
Linux CI does **not** establish a qualified live macOS/Codex boundary.

## Agent-first scope

The existing agent owns planning, implementation, self-tests and repairs;
Proofline owns frozen identities, bounded checks, receipts and truthful
feedback. Direct tasks require neither P2P nor Intentline. Already-authorized
contracts may inform later optional evidence mapping without replanning or
silently narrowing the original request. Local checking never authorizes push,
PR, merge or deployment. New mandatory stages must earn their latency and
blocking risk through improved *independently correct deliveries*.

See [DESIGN.md](DESIGN.md) for the small product contract and
[IMPLEMENTATION.md](IMPLEMENTATION.md) for the issue-aligned sequence.

## Research retained without active runtime weight

On 13 October 2026, S6 closed with an [abandon/simplify decision](docs/S6-DECISION.md)
after repeated false acceptances. The original full pilot remained incomplete;
**no superiority to an ordinary agent, or Luna/Sol advantage, was established**.
A later [six-task bounded comparison](docs/BOUNDED-COMPARISON.md) found no extra
correctness benefit from mandatory review in that small sample.
The [frozen v1 live ordinary-agent baseline](evaluation/results/live-v1-20261013/README.md)
then observed six independently correct deliveries in six assigned tasks, with
finite-check and small-sample limits recorded alongside the native receipts.

Historical S0–S6 experiments, documents, fixtures, experimental `deliver`
and `resume` implementation, and dependent tests were removed from the
**active** code path. Their complete original versions remain in Git history,
indexed in [the research archive](docs/RESEARCH-ARCHIVE.md). Raw local ignored
`.proofline/` records, where present, were never tracked in Git. The supported
runtime has **no** remote-mutation or full-promise acceptance command.
