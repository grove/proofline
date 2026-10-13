# Proofline

**Know what passed. Know what still needs checking.**

Proofline is a small, opt-in companion for coding agents. Give it the **original request**, an **existing coding candidate**, and **checks you choose**. It freezes the candidate, runs the commands inside a protected sandbox, and saves evidence you can inspect later—**without another model call**.

> **A passing check is evidence about that check—not proof that every part of a request is complete.**

Proofline keeps the agent in charge of implementation and fixes. It does not add a mandatory planner or AI reviewer, install dependencies, certify requirements, or publish code.

**Jump to:** [Get started](#get-started) · [Results](#understand-the-results) · [Agent skill](#use-with-codex-or-claude-code) · [Managed coding](#optional-managed-coding) · [CLI reference](#cli-reference) · [Safety](#safety-and-scope)

## What can Proofline do?

| | `check` — recommended starting point | `run` — optional managed coding |
| --- | --- | --- |
| Workflow | Existing agent or developer implements; Proofline checks | Proofline starts one Codex implementation turn, then checks |
| Input Git tree | Accepts staged, unstaged and non-ignored untracked changes | Requires a clean repository |
| Model calls | **Zero** | One; at most one additional same-thread correction if opted in |
| Checks | Exactly the selected commands | Exactly the selected commands |
| Source repository mutation | **None** | **None** |
| PR, merge or deploy | **Never** | **Never** |

```text
Original request ──┐
Working candidate ─┼──► Frozen copy ──► Protected checks ──► Native receipts
Selected argv ─────┘                                         + report.json
                                                                   │
                                                                   ▼
                                                       status (revalidate)
```

Proofline captures identities, tests a read-only copy, and reports what happened. The calling agent still owns any corrections, uncovered requirements, and the final handoff.

## Get started

### Requirements

The **supported native execution boundary** is **macOS with Python 3.11+ and Codex CLI 0.162.1** (this exact CLI version is required). You also need a Git repository and the target project's test tools and dependencies already installed.

`check` uses the Codex CLI's **native sandbox only**, **not its model**, so check-only runs require no model authentication. `run` does require an authenticated Codex CLI. Linux CI runs offline regressions, but **Linux and Windows are not supported for native checks**. There is no unprotected fallback.

### 1. Clone Proofline

```sh
git clone https://github.com/grove/proofline.git
cd proofline
python3 -B proofline.py --help
```

Proofline runs from the checkout; you don't need an acceptance file, a separate planning workflow, or an agent skill installation to use the CLI.

### 2. Check an existing change

After your coding agent has implemented a change, select **real checks in that product repository**. Example for a Python project with a `tests/` directory:

```sh
# Run from the Proofline checkout; resolved Python must be an absolute path.
PYTHON="$(python3 -c 'import sys; print(sys.executable)')"

"$PYTHON" -B proofline.py check \
  --repo /absolute/path/to/your-python-project \
  --request 'Reject blank usernames while preserving Unicode support.' \
  --command "$PYTHON -B -m unittest discover -s tests"
```

Replace the paths, request and command with your project-specific values. `--repo` must point to the **Git repository root**. Repeat `--command` to cover more important behavior, for example `"$PYTHON -B cli.py --version"` **if that interface exists in the target project**.

Proofline copies the current tracked and non-ignored untracked work (including ordinary uncommitted changes), **does not modify your source**, and runs the selected commands without another coding model dispatch.

### 3. Keep and inspect the record

The CLI prints a short summary and the path to `report.json`. Copy that **Record:** path to read the evidence again:

```sh
"$PYTHON" -B proofline.py status /absolute/path/to/record/report.json

# Only for an intact check-only record: print the verified original request.
"$PYTHON" -B proofline.py status /absolute/path/to/record/report.json --show-source
```

By default, `check` creates a unique record under the system temporary directory (`proofline-check/<unique-id>`). If you need a durable record, provide `--output /absolute/new/path/outside/product` and preserve the directory. Output paths must be **new** and outside the source repository.

## Understand the results

| Status | Meaning | Suggested next step |
| --- | --- | --- |
| **CHECKS PASSED** | All selected commands succeeded on the frozen candidate | Consider what those checks didn't cover |
| **CHECKS FAILED** | At least one selected command executed and returned nonzero | Inspect the diagnostic before diagnosing a product defect |
| **CHECKS UNAVAILABLE** | At least one command didn't yield usable evidence | Look for missing tools, timeouts, or environment problems |
| **EXECUTION UNAVAILABLE** | A necessary execution boundary or earlier stage couldn't complete | Fix the reported prerequisite or boundary failure |
| **STALE CHECKS** | Frozen source, candidate, commands, or receipts no longer match | Make a fresh record; don't rely on an old pass |

A failed command is not always a code defect. A timeout, missing executable, truncated receipt, or sandbox failure is **unavailable evidence**, not a made-up implementation diagnosis.

`report.json` records the original source SHA-256, frozen candidate commit/tree and snapshot, selected argv, exit codes, elapsed time, and `feedback.checks` entries that point to bounded native stdout/stderr receipts (e.g. `receipts/check-000.json`). Receipts live outside command-writable scratch and the candidate; the terminal shows concise feedback rather than dumping the full logs. `status` detects changed or missing frozen evidence.

**Exit codes:** `0` means `CHECKS PASSED`; `2` means another recorded status; `1` means a CLI/input/readback error. Later edits to your live project do **not** change the old frozen candidate. Run `check` again to evaluate new work.

## Use with Codex or Claude Code

Proofline includes **one optional agent skill**, [`proofline-check`](skills/proofline-check/SKILL.md), for an existing agent to use *after implementing code*. The skill documents check invocation, failure feedback, evidence gaps, and optional advanced paths; it is **not** a mandatory new agent or stage.

There is **one canonical directory**, `skills/proofline-check`, with two checked-in discovery symlinks pointing to it:

| Agent | Path in this checkout | Explicit invocation |
| --- | --- | --- |
| Codex | `.agents/skills/proofline-check` | `$proofline-check` |
| Claude Code | `.claude/skills/proofline-check` | `/proofline-check` |

Those discovery paths work when an agent is **working inside Proofline**. To use the skill while working in a *different* product repository, install it for your chosen agent. User-level symlinks on macOS/Linux:

```sh
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s /absolute/path/to/proofline/skills/proofline-check \
  "$HOME/.agents/skills/proofline-check"
ln -s /absolute/path/to/proofline/skills/proofline-check \
  "$HOME/.claude/skills/proofline-check"
```

Replace `/absolute/path/to/proofline` with your actual checkout. **Install only the agent you need.** Project-specific alternatives are `/absolute/path/to/product/.agents/skills/proofline-check` and `/absolute/path/to/product/.claude/skills/proofline-check`. Avoid unnecessary user/project duplicates. The symlink target must continue to exist; a standalone copy of the canonical folder also works, but the **Proofline CLI checkout remains a separate requirement**.

Installed agents can discover a skill from its description, but automatic invocation is **not** guaranteed. Ask explicitly for `$proofline-check` or `/proofline-check` if you want the agent to use it. The CLI itself works without a skill.

**Previous skill name?** Root [`SKILL.md`](SKILL.md) is just a compatibility pointer—not a second skill or alias. Replace `$proofline` and `/proofline` with the new invocations and **remove or rename** any older user-level `proofline` skill directories. Installation isn't migrated automatically.

## Optional managed coding

If you want Proofline to initiate one bounded coding attempt rather than check existing work, use `run` on a **clean Git source** with an **authenticated Codex CLI**:

```sh
"$PYTHON" -B proofline.py run \
  --repo /absolute/path/to/clean-python-project \
  --request 'Add a --version flag without changing existing CLI behavior.' \
  --command "$PYTHON -B -m unittest discover -s tests" \
  --stage-seconds 600
```

That runs one Codex implementation turn on a separate copy, freezes the result, and checks the selected commands. It adds no AI reviewer, prover, publisher, or external approval.

**Want one bounded correction?** Add `--correct-once` to `run`. Only an *intact, nonzero native check* with a Python `AssertionError` diagnostic qualifies—and **every** selected check must have usable evidence. Missing tools, timeouts, truncated/mismatched receipts, stale candidates, environment-error diagnostics, arbitrary nonzero formats, and advisory promise gaps do **not** trigger a new turn.

If eligible, Proofline resumes the **same implementer thread** with the entire original request and exact failed argv, exit codes and bounded output. It corrects a copy and reruns **all** selected checks, including previously passing compatibility checks. There is at most one correction. First-pass success dispatches only once; interruption, incomplete handoff, or a repeated defect doesn't start another turn.

`--seconds` is a single cumulative budget for setup, implementation, checks, correction and rerun; `--stage-seconds` caps each coding turn. Dispatch slots are journaled before launch; there is **no controller resume or automatic restart** to reset the budget. Initial evidence remains at `initial/report.json`, hash-bound to the final report and rechecked by `status`.

The [native correction control](tests/test_correction_live.py) and [qualification summary](docs/ISSUE15-QUALIFICATION.json) validate this mechanism against a deliberately seeded assertion defect, **not** a general performance advantage on ordinary coding work.

## CLI reference

### Supported commands

| Command | Purpose |
| --- | --- |
| `python3 -B proofline.py check` | Model-free checks against existing work |
| `python3 -B proofline.py run` | One managed implementation and selected checks |
| `python3 -B proofline.py status RECORD` | Revalidate the frozen report (path to `report.json`) |

### Inputs and options

Both `check` and `run` require a `--repo` Git root, **one original-request input**, and **one set of selected checks**:

| Flag | Purpose |
| --- | --- |
| `--request TEXT` | Literal, complete original request, including multiline text if passed |
| `--request-stdin` | Original UTF-8 from stdin, retaining trailing newlines |
| `--source FILE` | Original UTF-8 request bytes from a file |
| `--command 'EXEC ARG…'` | One POSIX-quoted argv; repeat for multiple checks |
| `--checks FILE` | JSON array of argv arrays for complex/exact arguments |
| `--output DIR` | A new output directory |
| `--failure-details FILE` | Optional caller-supplied failed-check annotations |
| `--seconds N` | Cumulative budget (default **900** seconds) |
| `--check-seconds N` | Each selected check's cap (default **120** seconds) |

The three request forms are mutually exclusive; so are repeated `--command` and `--checks`. **Every executable must have an absolute path.** `--command` only tokenizes POSIX quoting into argv: it does **not** run a shell, expand variables, evaluate substitutions, or interpret pipes/redirections. For exact complex values, prefer `--checks`:

```json
[
  ["/opt/homebrew/bin/python3.14", "-B", "-m", "unittest", "discover", "-s", "tests"],
  ["/opt/homebrew/bin/python3.14", "-B", "cli.py", "--version"]
]
```

These are examples, not built-in tests. You must choose valid checks for your project. Duration flags must be finite, positive, and at most 3,600 seconds.

**Mode-specific:** `run` has `--stage-seconds` (default **600**) and `--correct-once`. `check` has `--promises FILE` or `--intentline-export DIR`, with optional `--intentline-links FILE` **only** for the export. `status` has `--show-source` for intact check-only records.

For durable inputs (or exact multiline source), save the request in `request.md` and argv arrays in `checks.json`, or pipe source bytes via `--request-stdin`:

```sh
"$PYTHON" -B proofline.py check \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/request.md \
  --checks /absolute/path/to/checks.json \
  --output /absolute/new/directory/outside/product \
  --seconds 900 --check-seconds 120
```

See `python3 -B proofline.py <command> --help` for all options.

## Optional: connect requirements to check evidence

This is **advisory** and applies only to `check`. Proofline does not invent requirements, tests, expected results, or an independent acceptance verdict.

### Source-linked promises

With `--promises /private/promises.json`, you may map exact lines from the **complete original request** to exact selected command argv. Suppose `request.md` contains exactly:

```text
Reject blank usernames.
Support Unicode usernames.
```

A sample mapping (replace the hash and interpreter path with real values):

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
      "checks": [{"index":0,"argv":["/opt/homebrew/bin/python3.14","-B","-m",
                                   "unittest","discover","-s","tests"]}]
    },
    {
      "id": "R2",
      "statement": "Support Unicode usernames",
      "source_refs": [{"source_id":"S1","line_start":2,"line_end":2,
                       "quote":"Support Unicode usernames."}],
      "checks": []
    }
  ]
}
```

Compute the SHA-256 of the **exact source file bytes**, including its final newline:

```sh
python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' request.md
```

Use `--source` with those bytes; the linked argv must match the actual zero-based selected command *exactly*. Source quote, ID, hash, candidate-tree and argv mismatches are rejected. Unlinked R2 is **NOT DEMONSTRATED**, even if checks pass.

`promise_evidence.requirements` distinguishes **LINKED CHECKS PASSED (limited evidence)**, **CHECK FAILED**, **CHECK UNAVAILABLE**, and **NOT DEMONSTRATED**. A green linked check is **limited evidence**, not proof of the complete requirement; inventory completeness is **always UNKNOWN**. Optional `review.proposals` can record same-agent, source-grounded, **unverified** suggestions for missing tests.

### Intentline handoff (also optional)

Already using [Intentline](https://github.com/grove/intentline)? You can reuse its existing **completed JSON export** of one unamended original request, without importing or installing Intentline into Proofline:

```sh
# Separate Intentline CLI; offline export, no model or test run:
python3 -B -m intentline export \
  --work /private/intentline/work \
  --format json --out /private/intentline/json-export --json

# Run from Proofline checkout with the original exported source:
"$PYTHON" -B proofline.py check \
  --repo /absolute/path/to/product \
  --source /private/intentline/json-export/source-S1.txt \
  --command "$PYTHON -B -m unittest discover -s tests" \
  --intentline-export /private/intentline/json-export
```

Imported requirements begin **NOT DEMONSTRATED**. If you know which chosen check relates to an R ID, `--intentline-links /private/links.json` may contain exact links, for example:

```json
{
  "R1": [{"index":0,"argv":["/opt/homebrew/bin/python3.14","-B","-m",
                             "unittest","discover","-s","tests"]}]
}
```

Replace the example Python path with the **exact path** actually used by `--command`. The adapter accepts only a canonical, complete, initial revision 1/schema 1 **single-S1** export, validating manifest hashes, contract, source bytes, quotes and check links. It rejects partial, amended, multi-source, noncanonical, tampered or symlinked exports. Exported data is never executed. Intentline's oracles, constraints, boundaries and `unapproved`/`operator_asserted_unverified` labels remain *advisory*, never external approval or push permission. `--promises` and `--intentline-export` are mutually exclusive. See [issue #23](https://github.com/grove/proofline/issues/23).

### Caller-supplied failure details

If a checker already produced a specific case, optionally attach `--failure-details /private/failure-details.json`:

```json
[
  {"index":0,"outcome_ids":["R2"],
   "expected":"Unicode username accepted",
   "observed":"Unicode rejected"}
]
```

`expected` is not an independently verified oracle. `observed` appears only if it literally occurs in bounded stdout/stderr of the **failed native check**. R IDs without validated mapping links remain unverified labels. This annotation does not invoke an AI correction.

## Safety and scope

- **Source is untouched.** `check` doesn't reset, stash, stage, commit or write to your repo; `run` also uses an isolated copy.
- **Snapshots are explicit.** Tracked files include staged and unstaged work; non-ignored untracked files are included, tracked deletions omitted. Ignored untracked files, Git metadata and empty directories aren't copied. Regular file modes and safe relative file symlinks are preserved. Submodules, nested repos, directory or escaping symlinks and special files are unsupported.
- **Avoid mixed captures.** Proofline checks for changes while copying; pause edits until the candidate freezes.
- **Checks cannot write product files or use the network.** If a test needs in-tree writes, choose another observation strategy; Proofline installs no dependencies.
- **Native isolation is mandatory.** Missing/unqualified native boundaries produce unavailable evidence; offline Linux CI does not establish live macOS safety.
- **Remote actions are out of scope.** No local check, promise map or Intentline export grants permission for PRs, pushes, merges or deployment. The supported CLI has no publisher or full-promise certification command.

## Contributing and background

Contributions are welcome—particularly improvements to helpful failures, native sandbox integrity, tests, and documentation. [DESIGN.md](DESIGN.md) explains the intentionally lightweight contract, [IMPLEMENTATION.md](IMPLEMENTATION.md) the core boundaries, and the [issue tracker](https://github.com/grove/proofline/issues) the current work.

Run deterministic/offline regressions from the Proofline checkout:

```sh
python3 -B -m unittest discover -s tests -v
```

[GitHub Actions](.github/workflows/checks.yml) runs offline checks across Python versions on Linux; that isn't live macOS/Codex qualification. On the qualified authenticated host, you can reproduce the deliberately seeded correction control:

```sh
PROOFLINE_CORRECTION_LIVE=1 /opt/homebrew/bin/python3.14 -B -m unittest tests.test_correction_live -v
```

Proofline's lean design follows the [S6 abandon/simplify decision](docs/S6-DECISION.md) after repeated false acceptances and an incomplete full pilot. A [small bounded comparison](docs/BOUNDED-COMPARISON.md) found no extra correctness benefit from mandatory review in that sample. The [ordinary-agent baseline](evaluation/results/live-v1-20261013/README.md) and [research archive](docs/RESEARCH-ARCHIVE.md) retain important evidence and limitations; retired `deliver` and `resume` experiments remain in Git history, not the supported runtime. No universal delivery advantage is claimed.

The [issue #16 matched delivery study](evaluation/results/matched-v5-20261013/README.md) observed all sixteen assignments across four fresh tasks with untested obligations and stale-oracle cases. Every arm delivered 4/4 finite-correct products. Planning-only and combined used 72.9% and 89.1% more episode time than ordinary coding, with no observed delivery benefit. Checks, planning and mapping remain optional. Four tasks cannot establish general superiority; [earlier stopped studies](docs/ISSUE16-V5.md) retain their failures, missing slots and costs separately.

**License:** [Apache 2.0](LICENSE).

---

**Build with your favorite agent. Check what matters. Keep the evidence—and the final decision—in your hands.**
