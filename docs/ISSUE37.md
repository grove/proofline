# Issue #37 — real PR check casebook

On 2026-10-14, three **real, user-requested implementation PR heads** in
Proofline were checked retrospectively. One completed native protected checks;
two were unavailable because their directory symlinks are unsupported.
**Zero observed recoveries.** Ordinary tests found a macOS receipt-path problem
in #36; Proofline could not check that candidate. This does not demonstrate
improved delivery correctness or comfortable adoption during implementation.

Recommendation: **fix a specific usability blocker**, in a small separately
approved PR, while keeping `check` optional. Evidence for broader practical
value is **insufficient**. No product behavior changes accompany this casebook.

## Method and retained evidence

The cases are [#12](https://github.com/grove/proofline/issues/12),
[#28](https://github.com/grove/proofline/issues/28), and
[#36](https://github.com/grove/proofline/issues/36), whose implementations were
already merged as PRs #24, #30 and #39. These are requested repository features,
not synthetic benchmark tasks or newly invented work. No coding was replayed.
Original implementer identity/model/effort, session prompt, usage and cost are
not independently authenticated by Git authorship or PR metadata.

Each detached local worktree preserved the exact PR head, file modes and links.
Checks used the **complete issue title, two LF bytes, and exact issue body**,
including its amendments; all three issues had no comments at capture. These
[request snapshots](../evaluation/results/issue37-dogfooding/requests/) are
the task-source record, not a reconstruction of an unavailable agent-session
prompt. No requirement was dropped to accommodate snapshotting or a failing test.

The existing repository-local
[`proofline-check` skill](../skills/proofline-check/SKILL.md) supplied the agent
instructions. The agent selected existing unittest modules by reading the
source and tests, ran them ordinarily, then supplied **identical argv** to
Proofline. There was no new acceptance ceremony, reviewer, telemetry, test
synthesis, dependency installation or live coding-model experiment.

Runner: `c06bd54` (the #39 merge), macOS arm64, Python 3.14.8 and Codex CLI
0.162.1. The successful check qualified its native process boundary as
`OBSERVED`; Linux CI is not that qualification. All source candidates stayed
clean and unchanged. Outputs were new directories outside those candidates.

The [ledger](../evaluation/results/issue37-dogfooding/ledger.json) retains full
commit/tree/source identities, exact invocations, selected results, timings,
readback status and unknowns. The
[evidence archive (~0.5 MB)](../evaluation/results/issue37-dogfooding/evidence.zip)
contains bounded process receipts, original reports/host evidence, the successful
frozen candidate and a small receipt-path diagnostic. It contains no raw agent
transcripts or authentication records. Its SHA-256 is recorded in the ledger.

## Results with the same selected commands

Every case used these two commands, with `MODULE` replaced as shown below:

```text
/opt/homebrew/Cellar/python@3.14/3.14.8_2/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -B -m unittest MODULE -v
/opt/homebrew/Cellar/python@3.14/3.14.8_2/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -B -m unittest tests.test_supported_cli -v
```

| Task / actual candidate | MODULE | Ordinary results | Proofline / readback | Ordinary seconds | Proofline seconds |
| --- | --- | --- | --- | ---: | ---: |
| [#12 / PR #24](https://github.com/grove/proofline/pull/24), `aac3d942` | `tests.test_cli_inputs` | 8 + 4 tests passed | `CHECKS PASSED`, 2/2 bound receipts; same status on readback | 0.81 | 2.30 |
| [#28 / PR #30](https://github.com/grove/proofline/pull/30), `bb15f775` | `tests.test_skill_discovery` | 5 + 5 tests passed | `EXECUTION UNAVAILABLE`; same status on readback, no frozen-candidate/check receipts | 0.91 | 0.16 |
| [#36 / PR #39](https://github.com/grove/proofline/pull/39), `c5cadd8b` | `tests.test_source_oracles` | 10 tests ran with 10 failures including subtests; 5 CLI tests passed | `EXECUTION UNAVAILABLE`; same status on readback, no frozen-candidate/check receipts | 5.90 | 0.36 |

Times are observed process/controller durations, not complete human or economic
cost. The #12 total includes its 0.61-second unavailable nested-sandbox attempt
and 1.70-second protected host retry. #36 ordinary time includes a repeated
2.53-second failing module run to retain diagnostics after the capture script
incorrectly asserted every command would pass. The initial #36 exit/count/time
summaries survive, but its first exact receipts were not saved. The ledger
discloses this capture mistake rather than silently discarding the attempt.
Readback added 0.29 / 0.09 / 0.09 seconds respectively. Worktree setup, diagnostic
outer wall time, agent instruction/selection effort and human time are unknown.

All checking and diagnostic tools made **zero model dispatches**, so additional
checking-model tokens and model charges were zero. The current agent's work,
prior implementation costs, host costs and actual total billing are unknown.

## Per-case value and uncovered requirements

**#12: direct inputs and compatibility.** This multi-file CLI change touches
parsing, managed source capture, tests and instructions. Existing tests exercise
direct/file equivalence, multiline Unicode/CRLF and terminal newlines, literal
argv without shell evaluation, invalid inputs and mutually exclusive options.
Public CLI tests exercise advertised/help behavior and refusal of retired
commands. The real invocation used `--request-stdin` and two repeated
`--command` options; its exact source hash and frozen tree matched the PR tree
`e4138ed9804b1cba3348fc44f6011af73b2223de`.
Proofline added protected, read-only execution, native receipts and readback
identities, **no additional test coverage or detected defect**. Many input tests
mock downstream execution; they do not establish every end-to-end managed-run
behavior, documentation quality, all source/candidate diagnostics, or optional
Intentline planning guidance. These remain incompletely demonstrated.

**#28: discovery and installation.** Existing tests verify one canonical skill,
real shared discovery symlinks, metadata, copied installation, link/migration
guidance and unchanged CLI surface. The actual candidate includes
`.agents/skills/proofline-check` and `.claude/skills/proofline-check`, both
relative aliases to a **directory**. Snapshotting refused them with
`Symlinks must be relative aliases to regular product files outside Git metadata`.
The skill's useful discovery packaging therefore prevents self-checking this
checkout. Neither symlink was removed, dereferenced or excluded to manufacture
a pass. Native runtime integrity, actual Codex/Claude installation and invocation,
and automatic agent uptake were not demonstrated by these selected checks.

**#36: source-faithful future oracles and negative controls.** This four-file
implementation adds source preflight, a future cache oracle, regression controls
and a checklist. Tests cover supported TTL alternatives, explicit ValueError,
meaningful defects, unknown/disputed source evidence, loader suppression and
green/red repository suites. On this macOS host, its ordinary controls reported
`ORACLE UNAVAILABLE` instead of their expected results. A small existing
reference diagnostic showed an available oracle receipt and **passing child
repository suite**, but the child's `sys.executable` was the Homebrew alias
`/opt/homebrew/opt/python@3.14/bin/python3.14`. Validation expected the resolved
Cellar path above and rejected the unequal argv strings. This is a reproduced
platform receipt problem, not evidence that a meaningful cache defect passed.
Proofline stopped earlier on the same directory symlinks as #28, so it neither
noticed this failure nor supplied repair feedback. Git comparison against
`4a92ba0` independently showed only the four new #36 files: previously tracked
frozen studies and the optional check runtime remained unchanged. Whole-request
semantic correctness and actual independent oracle adjudication remain unknown.

All requirement assessments here are by the same inspecting agent, informed by
source and executable observations. There is **no independent whole-request
acceptance assessment**; coverage completeness and real correctness are unknown.
Green selected tests are not all user promises proven.

## Friction, recovery and next step

- **Host qualification:** The first #12 attempt inside the session sandbox had
  `NOT VERIFIED` native protection and correctly returned unavailable. A host
  retry kept Proofline's native protection enabled and passed. No unprotected
  Proofline fallback was used. This adds host-execution coordination for agents.
- **Input/readback:** Full stdin input and repeated commands worked in #12;
  #28 used `--request` and #36 used the existing `--source` form. Unavailable
  feedback identified the blockers; successful `status` checked the frozen
  source, candidate and two native receipts. No stale candidate was observed.
  Readback binds absolute paths and modes: moving archived reports does not
  make them freshly revalidated. Original task directories are retained locally.
- **Discovery/layout:** The skill was available in this repository. Independent
  installation and automatic invocation were not observed. Directory-symlink
  friction was encountered twice on actual PR heads; dirty/untracked candidates
  were not encountered and no artificial probes were added.
- **Recovery:** No candidate yielded an independently supportable **Proofline**
  failed-check observation for this existing agent to repair. #36's ordinary
  test failure and its diagnostic stay recorded; no product fix, new model,
  seeded defect or synthetic repair was introduced. **Zero observed recovery**,
  with usefulness of feedback for bounded repair unmeasured.

Propose two narrow follow-ups, each with tests and separate product-change
approval: make the self-check limitation of discovery symlinks explicit and
resolve supported packaging without weakening snapshot protection; fix
future-cache receipt comparison for equivalent Python executable aliases while
preserving actual child argv. Neither requires a compatibility subsystem.

The unavailable cases are observable usability blocks, not demonstrated false
rejections of correct implementations: independent correctness is unknown.
The passing case has no independently established missed defect, so there is
no identifiable false acceptance. Those concerns remain unmeasured. One repo,
one host and retrospective merged candidates do not establish adoption,
population reliability or coding-agent success-rate improvement. Continue
alongside genuinely requested engineering work; no more live-model experiments
are justified solely to fill this casebook. These task links can inform the
future Luna reasoning-cost comparison, but no model/effort cost comparison was
performed here. Merge still requires explicit approval.

## Casebook validation

Source hashes, archive hash, PR/frozen tree equality, selected argv, report and
receipt hashes, original-path readbacks and local Markdown links were checked.
The full macOS suite ran 251 tests in 163.87 seconds, with **10 existing #36
failure diagnostics and 8 skips**. The same failure was reproduced on unchanged
PR #39 before casebook edits; no production Python was changed. Its bounded
suite output is retained in the archive. All three fixed S0 oracle controls
passed separately. Diff whitespace checks passed. No live coding/correction
model or separate semantic reviewer was invoked.
