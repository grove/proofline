# Proofline

**A small, optional helper to autonomous coding agents.** Proofline preserves
an original request, freezes an existing working candidate, and executes
caller-selected checks without another model dispatch. It also offers one
optional bounded coding attempt. Passing commands are evidence
**only about those commands**, not proof of every requirement.

## Currently supported

The supported commands are `proofline.py check`, `run` and `status`.
On the qualified **macOS** host (Python 3.11+, Codex CLI **0.162.1**),
`check` uses only the CLI's native sandbox: **zero model dispatches**, no
model settings or authentication needed. `run` optionally dispatches **one**
coding attempt and needs existing authentication and a clean Git source.
Neither mode runs automatic reviewers, provers, corrections, PRs, merges or
deployments. Both leave the source repository untouched.

Save the exact original user request in `source.md`, outside the product
changes. Choose relevant executable checks with **absolute executable paths**
and store their exact argument arrays in `checks.json`:

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
