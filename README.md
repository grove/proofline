# Proofline

**A small, optional helper to autonomous coding agents.** Proofline preserves
an original request, runs one bounded local coding attempt, freezes its
candidate, and executes caller-selected checks. Passing commands are evidence
**only about those commands**, not proof of every requirement.

## Currently supported

The only supported commands are `proofline.py run` and `proofline.py status`.
On the qualified **macOS** host (Python 3.11+, Codex CLI **0.162.1**, existing
authentication), `run` dispatches **one** coding attempt. It does **not**
run automatic reviewers, provers, corrections, PRs, merges or deployments.
It requires a clean Git source repository and does not alter that repository.

Save the exact original user request in `source.md`, outside the product
changes. Choose relevant executable checks with **absolute executable paths**
and store their exact argument arrays in `checks.json`:

```json
[["/opt/homebrew/bin/python3.14", "-B", "-m", "unittest", "discover", "-s", "tests"]]
```

```sh
/opt/homebrew/bin/python3.14 -B proofline.py run \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --seconds 900 --stage-seconds 600 --check-seconds 120
```

```sh
/opt/homebrew/bin/python3.14 -B proofline.py status /absolute/path/to/report.json
```

Checks run against a **frozen, read-only candidate** under native protection,
without network access or writes to product files. No dependency installation
takes place; checks requiring in-tree writes need a different observation path.
A bounded report records exact argv, native execution receipts, usage when
available, a candidate identity, and distinct `CHECKS PASSED`,
`CHECKS FAILED`, `CHECKS UNAVAILABLE`, `EXECUTION UNAVAILABLE` and
`STALE CHECKS` observations. `status` detects candidate/source/check drift
after an apparent success. Partial or unavailable implementation handoffs do
not become successful check claims.

**User journey (current):** A user requests a new CLI option without breaking
existing behavior. The caller supplies the full source and selected CLI plus
regression checks; Proofline codes once and runs those commands on its frozen
candidate. The handoff says exactly which commands passed, notes any untested
requirements, and confirms **no PR or merge occurred**.

The supported runtime keeps separate small modules for CLI, Git snapshots
(`checks/candidate_snapshot.py`), one coding attempt, native checks,
and exact receipt readback. Historical host diagnostics remain available
for offline security testing, not as an extra acceptance stage. Successful
Linux CI does **not** establish a qualified live macOS/Codex boundary.

## Planned vNext: help existing agents, don't supervise them

[Issue #11](https://github.com/grove/proofline/issues/11) proposes model-free
**check-only** use: an existing coding agent writes the code, gives Proofline
its candidate and the original promise, and gets concise check evidence without
a second model dispatch. **The `check` command does not exist yet.** The
existing agent owns planning, implementation, self-tests and repairs; Proofline
owns frozen identities, bounded checks, receipts and truthful feedback.

**Proposed journey (not implemented):** The existing agent implements username
validation, calls the future check-only mode, and reports "These validation
commands passed; Unicode compatibility is not demonstrated by the selected
checks." A failed check goes back to the same agent to correct. No second AI
reviewer or automatic publisher intervenes.

Direct tasks should not require P2P or Intentline. Already-authorized contracts
may be reused in later optional evidence mapping without replanning or silently
narrowing the source. Local checking never authorizes push, PR, merge or
deployment. New mandatory workflow stages must earn their latency and blocking
risk through improved *independently correct deliveries*.

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
