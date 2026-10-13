# Proofline

**A small, optional helper to autonomous coding agents.** Proofline preserves
an original request, freezes an existing working candidate, and executes
caller-selected checks without another model dispatch. It also offers one
optional bounded coding attempt. Passing commands are evidence
**only about those commands**, not proof of every requirement.

## Agent skill: `proofline-check`

Proofline provides **one optional agent skill**, named
[`proofline-check`](skills/proofline-check/SKILL.md), for an existing
coding agent to invoke **after implementing code** when it needs to run
selected checks on a frozen candidate, interpret actual failures, and
identify evidence gaps. The same instructions also document optional
Intentline mappings and optional managed `run --correct-once`; they
are **not separate skills or mandatory stages**. The skill does not
automatically start a model, install packages, publish code or grant
permission to modify the user's repository.

The repository keeps **one canonical** `skills/proofline-check/SKILL.md`.
Codex and Claude Code both support symlinked skill folders, so this
checkout contains discovery links to that *same* directory:

| Agent | Checked-in repository discovery path | Explicit invocation |
| --- | --- | --- |
| Codex | `.agents/skills/proofline-check` | `$proofline-check` |
| Claude Code | `.claude/skills/proofline-check` | `/proofline-check` |

These paths make the skill visible **when the agent is working in the
Proofline repository**. For a coding agent working in **another product
repository**, install the skill for that agent instead. With Proofline
already checked out at `/absolute/path/to/proofline`, a user-level
installation on macOS/Linux can be made once using:

```sh
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s /absolute/path/to/proofline/skills/proofline-check "$HOME/.agents/skills/proofline-check"
ln -s /absolute/path/to/proofline/skills/proofline-check "$HOME/.claude/skills/proofline-check"
```

Use **only the agent you need**; both commands are shown for convenience.
To scope it to an individual product repository instead, use
`/absolute/path/to/product/.agents/skills/proofline-check` for Codex or
`/absolute/path/to/product/.claude/skills/proofline-check` for Claude
Code, with the same source directory as the symlink target. Do not use
both user- and project-level copies unnecessarily. The target must
continue to exist; a standalone copy of the canonical skill directory
also works, but its instructions still require an independently
available Proofline checkout for the Python CLI.

Agents may **discover** installed skills by their descriptions and
choose to use them when relevant; automatic invocation is **not
guaranteed**. Explicitly request the skill if desired. Installation
does not make checks mandatory for trivial work. The Python CLI remains
usable without any skill installation.

**Migration from the previous name:** The former root
[`SKILL.md`](SKILL.md) is a compatibility pointer, not a second
discoverable skill or an alias. Previously installed
`$proofline` (Codex) and `/proofline` (Claude Code) invocations
must be changed to `$proofline-check` and `/proofline-check`;
remove or rename any older user-level `proofline` skill folders
yourself. The project and CLI are still named **Proofline**.
No existing skill installation is automatically migrated.

Source: [Codex skill locations](https://learn.chatgpt.com/docs/build-skills)
and [Claude Code skill locations](https://code.claude.com/docs/en/skills).

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

For one optional correction by that **same implementer**, add `--correct-once`
to `run`. First-pass success still uses just one dispatch. Only an intact,
nonzero native check with a Python `AssertionError` diagnostic qualifies;
every selected check must have usable evidence. Timeouts, missing tools,
truncated or mismatched receipts, stale candidates, environment-error
diagnostics, advisory requirements and untested promises never trigger it.
Other failure formats are reported for the caller to handle; Proofline does
not infer a product defect from an arbitrary nonzero exit.

The correction resumes the original native thread with the **entire original
request**, exact failed argv, exit codes and bounded stdout/stderr. It edits
a separate copy of the failed candidate, freezes it, and reruns **all** selected
checks, including compatibility checks that previously passed. `--seconds`
is one cumulative episode budget for setup, coding, checks, correction and
rerun; `--stage-seconds` caps each coding turn within that budget. There is
at most one correction, even if the defect repeats or the handoff is incomplete.
No reviewer, prover, supervisor, Intentline dependency or acceptance verdict
is introduced.

`report.json` records `correction.enabled`, `correction.attempted`, bound worker
thread and dispatch count. Dispatch slots are journaled before launch; an
interrupted launch conservatively consumes its slot. Initial candidate/check
evidence remains at `initial/report.json`, hash-bound to the final report.
Old passing checks never carry forward to an altered candidate. `status`
revalidates both candidates, source, commands and receipts; drift makes the
final evidence stale. Interrupted episodes remain unavailable and cannot
reuse their output directory. There is **no controller resume or automatic
restart** to reset the budget or repeat a dispatch; a new explicitly requested
episode uses a new output directory.

The opt-in [native control](tests/test_correction_live.py) deliberately retains
a seeded assertion defect on its first handoff, then tests same-thread
correction, native boundaries and rerun. It is a mechanism qualification,
not a measurement of improvement on ordinary coding tasks.
The [13 October 2026 qualification summary](docs/ISSUE15-QUALIFICATION.json)
records both native boundaries, the failed assertion, same-thread identities,
corrected check results and exact runtime hashes; raw evidence remains at its
recorded local path. Reproduce it on the supported authenticated host with:

```sh
PROOFLINE_CORRECTION_LIVE=1 /opt/homebrew/bin/python3.14 -B -m unittest tests.test_correction_live -v
```

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
original source bytes. If a **completed Intentline JSON export** already exists,
Proofline can consume it optionally using `--intentline-export` (see below).
The CLI never installs or imports Intentline.

## Actionable, receipt-grounded feedback

Both `check` (zero model calls) and optional managed `run` print a **short**
summary of the selected commands. Failing commands show their exact argv
(in the structured report), native exit status, elapsed time, and a bounded
stderr/stdout excerpt with a concrete next action. An unavailable sandbox,
timeout, truncated output, stale evidence or missing executable is **not**
reported as a product defect. Successful commands give one short summary,
not another AI reviewer pass.

`report.json` includes `feedback.checks` with the exact selected argv,
exit code, elapsed seconds, frozen source SHA-256, candidate commit/tree,
snapshot identity and `receipts/check-NNN.json#stdout` / `#stderr` references.
The native host receipts are also retained as separate bounded/redacted files
**outside the command-writable scratch and the candidate**. `status` validates
their hashes and the frozen inputs; changed or missing evidence becomes
`STALE CHECKS`. Full bounded receipts are available on disk; the terminal
does not dump them by default.

If a checker already provides a specific failure example, a caller can attach
**optional** `--failure-details /private/failure-details.json`:

```json
[
  {
    "index": 0,
    "outcome_ids": ["R2"],
    "expected": "Unicode username accepted",
    "observed": "Unicode rejected"
  }
]
```

Indexes are zero-based and correspond to the selected commands. The
`expected` field is **caller-supplied, not an independently established
oracle**; the `observed` text is displayed only if it literally occurs in
the bounded native stdout/stderr of a failed check. An unsupported or forged
observation is withheld rather than presented as fact. An `R2` label without
an optional `--promises` mapping remains unverified advice; with a mapping,
its exact command association is validated but a green check still does not
prove the requirement in full. No unlisted requirement is deemed covered,
and no failed or missing evidence triggers an AI correction without the
explicit managed `run --correct-once` option and qualifying native diagnostics.

This file is optional. Ordinary `--command` or `--checks` invocations
still work unchanged, without Intentline, an acceptance plan, or extra
model dispatches. Live macOS/Codex sandbox qualification is distinct from
offline CI.

## Optional source-linked promise evidence

Existing `check` works exactly as before with **no planning or metadata**.
For a complex request, the same existing coding agent can *optionally* reread
the **full original request**, write a small source-linked JSON mapping,
and pass `--promises /private/promises.json` to `proofline.py check`.
Proofline does **not** extract requirements or generate tests on its own.
A user can also author the file directly.

For example, if `request.md` contains **exactly** these two lines:

```text
Reject blank usernames.
Support Unicode usernames.
```

An advisory mapping can be:

```json
{
  "schema_version": 1,
  "source_sha256": "REPLACE_WITH_SHA256_OF_EXACT_UTF8_REQUEST_BYTES",
  "requirements": [
    {
      "id": "R1",
      "statement": "Reject blank usernames",
      "source_refs": [{"source_id":"S1","line_start":1,"line_end":1,
                       "quote":"Reject blank usernames."}],
      "checks": [{"index":0,"argv":["/opt/homebrew/bin/python3.14","-B",
                                  "-m","unittest","discover","-s","tests"]}]
    },
    {
      "id": "R2",
      "statement": "Accept valid Unicode usernames",
      "source_refs": [{"source_id":"S1","line_start":2,"line_end":2,
                       "quote":"Support Unicode usernames."}],
      "oracle": "A valid José username should be accepted (unverified suggestion)",
      "checks": []
    }
  ]
}
```

Compute the SHA-256 from the *exact* original request file bytes
(`python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' request.md`)
and replace the placeholder. `--source /absolute/path/request.md` must refer
to the same bytes. A referenced check has a **zero-based** index and its
**exact selected argv array**; the example command must actually be among the
`--command` or `--checks` arguments. An unlinked requirement (`checks: []`)
is **NOT DEMONSTRATED**, even when every project test is green. An unmatched
source quote, changed request hash, wrong command, duplicated R ID,
unsupported field, or optionally pinned wrong `candidate_tree` is rejected.

```sh
/opt/homebrew/bin/python3.14 -B proofline.py check \
  --repo /absolute/path/to/product \
  --source /absolute/path/request.md \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests' \
  --promises /private/promises.json
```

`report.json` then contains `promise_evidence.requirements` with precise
check/receipt links and one of **LINKED CHECKS PASSED (limited evidence)**,
**CHECK FAILED**, **CHECK UNAVAILABLE**, or **NOT DEMONSTRATED**. An untested
promise is not a product failure. Green commands do not prove a linked
requirement in full. Requirement inventory completeness is **always UNKNOWN**,
including when the caller lists only a subset of the original request.
The original is retained verbatim in `inputs/source.md`; to view its full
verified content explicitly, use `proofline.py status RECORD --show-source`.
`status` detects stale source, mapping, candidate, exact check argv and
native evidence, and withdraws previous linked-pass claims.

**Optional same-agent gap review:** The *existing* agent may reread every
original source line and all supplied rows/checks, then add:

```json
"review": {
  "performed": true,
  "proposals": [{
    "statement": "Unicode behavior has no targeted test",
    "source_refs": [{"source_id":"S1","line_start":2,"line_end":2,
                     "quote":"Support Unicode usernames."}],
    "suggested_check": "Add a Unicode acceptance example with a separately expected result"
  }]
}
```

This is an optional additional **top-level key** in the example JSON (not a
standalone JSON file), and is *self-reported, unverified advice*. No completeness
claim, independent audit, approval, test invention, shell execution or model
dispatch follows from it. If no such review is performed, Proofline records
that fact rather than silently asserting coverage. Only `S1` (the exact
original request) is supported by this direct mapping; the optional
[Intentline adapter #23](https://github.com/grove/proofline/issues/23)
now provides a separate, explicit read-only JSON import for one unamended
request. Intentline remains **optional**, and no original promise may be
amended by any convenience mapping.

## Optional Intentline → Proofline handoff

When an existing agent (or human) has already used
[Intentline](https://github.com/grove/intentline) to prepare an acceptance
agreement, **reuse its existing JSON export** instead of retyping source-linked
requirements. This is entirely optional; the simple `check` command above
does not change or gain any new prerequisite.

Export once with Intentline's existing offline CLI (this runs no tests or
models):

```sh
python3 -B -m intentline export \
  --work /private/intentline/work \
  --format json --out /private/intentline/json-export --json
```

Then an existing coding agent checks its implementation, supplying the *exact
original request bytes* from the export and its own selected executable test
commands:

```sh
/opt/homebrew/bin/python3.14 -B proofline.py check \
  --repo /absolute/path/to/product \
  --source /private/intentline/json-export/source-S1.txt \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests' \
  --intentline-export /private/intentline/json-export
```

The adapter **does not infer which tests cover the agreement**. With no explicit
links, **every imported R requirement is NOT DEMONSTRATED**, even if all
selected commands happen to pass. For known checks, provide the optional
`--intentline-links /private/links.json` input:

```json
{
  "R1": [
    {"index":0, "argv":["/opt/homebrew/bin/python3.14","-B",
                       "-m","unittest","discover","-s","tests"]}
  ]
}
```

This is an explicit exact-argv link to the *first selected* check, not a
claim the command fully proves R1. Other requirements remain unlinked.
Both link files and export paths are read as **untrusted data**, never
executed. `--intentline-export` and direct `--promises` are mutually
exclusive; `--intentline-links` is valid only with the export.

**Supported narrow format:** a *complete* `export --format json` with
canonical `export-manifest.json`, `contract.json`,
`source-manifest.json`, and `source-S1.txt`, for a **single original
request, initial acceptance contract revision 1/schema 1**. The adapter
validates every manifest-listed byte hash, contract ID/revision, original
source snapshot SHA-256 and byte-for-byte equality with the supplied Proofline
request, exact source quotes and selected argv links. It refuses partial,
tampered, noncanonical, symlinked or unexpected files. Amended contracts,
S2/project-context/multiple-source exports, native scripts, successor bundles,
and unresolved decisions are **explicitly unsupported**; no silent flattening
or historical `deliver` fallback occurs. Producer filesystem paths are
provenance labels, never dereferenced by Proofline.

The `promise_evidence` report includes Intentline's R IDs, source quotes,
boundaries, interface/seam, caller-proposed oracles, `planned_evidence`,
per-R evidence-gap reasons, constraints and out-of-scope exclusions, plus
export/contract/source hashes. All are **proposed guidance**. `CHECKS PASSED`
remains about selected commands only, and overall requirement completeness is
always **UNKNOWN**. The export's `unapproved` or
`operator_asserted_unverified` status is reported faithfully; neither
status nor file hashes establish external user approval, permission to
dispatch models, push/merge/deploy authorization, or independent correctness.

Proofline freezes a protected copy of the validated export outside the
candidate and check-writable scratch, so `status` can detect stale/tampered
evidence without reopening the producer's work directory. No additional
model invocation or approval stage is introduced. Offline regression tests
do not replace live macOS/Codex sandbox qualification. Intentline's
[documentation handoff #36](https://github.com/grove/intentline/issues/36)
tracks replacing obsolete historical Proofline integration instructions.

## Currently supported

The supported commands are `proofline.py check`, `run` and `status`.
On the qualified **macOS** host (Python 3.11+, Codex CLI **0.162.1**),
`check` uses only the CLI's native sandbox: **zero model dispatches**, no
model settings or authentication needed. `run` optionally dispatches **one**
coding attempt and needs existing authentication and a clean Git source.
Managed `run --correct-once` optionally permits one same-thread correction
after a qualifying native assertion failure. Neither mode runs automatic
reviewers, provers, PRs, merges or deployments. Both leave the source repository
untouched.

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
