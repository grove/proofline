# Safe directory aliases (#42)

Qualified locally on 2026-10-14: macOS 26.6.2 arm64, Python 3.14.8,
Codex CLI 0.162.1. Linux CI is a separate observation.

The frozen candidate retains `.agents/skills/proofline-check` and
`.claude/skills/proofline-check` as Git mode `120000` links with the literal
target `../../skills/proofline-check`. There remains one canonical skill.
Working capture preserves symlink permission bits as well as targets;
Git capture preserves the exact original blobs and Git modes.

Qualification is deliberately narrow: direct relative file or directory
aliases to selected in-tree contents, with no intermediate symlink hops.
Each literal component is inspected without following links, before `..`
can cancel it. Directory targets cannot contain aliases, including cycles
back to an ancestor. Absolute/external targets, Git metadata in any case,
dangling links, special targets and nesting are refused. Discovery and
readback do not descend into directory aliases.

Project installation links to another checkout remain unsupported snapshot
inputs. User-level installations outside the product checkout are not
captured. A directory target excluded by snapshot selection cannot qualify.
No skill was installed, sandbox permissions broadened or models dispatched.

The full-checkout qualification exposed Git automatic maintenance starting
background packing after an isolated commit. A new `.git/objects/pack/tmp_pack_*`
correctly invalidated the native preflight. Snapshot commits now disable
automatic GC/maintenance for that invocation; source configuration is untouched.
A forced low-threshold packing regression passes and fails with the old commit
invocation. No unstable snapshot was accepted.

The #32 archival tests now compare runtime digests to their exact published
source archives rather than the evolving supported CLI. Every archived digest,
freeze, score and receipt remains unchanged; the original runtime's drift
guards still refuse rerunning it with today's changed source.

## Observed checks

- Normal host repository suite: 265 tests, OK (nine opt-in/platform skips),
  including the Git-dependent snapshot, source-oracle and CLI-input regressions.
- Native CLI regression on a clean fixture with the real two-link skill layout:
  `CHECKS PASSED`, `OBSERVED` boundary, zero model dispatches, unchanged source,
  candidate-bound receipt and successful CLI `status` readback. Writes, unlink
  and chmod through aliases were denied; a writable scratch link could neither
  write the candidate nor read the live source.
- Existing native CLI dirty-worktree/write/network control: passed.
- Clean isolated copy of the full Proofline checkout: `CHECKS PASSED` for 28
  existing tests in `tests.test_skill_discovery`, `tests.test_feedback`,
  `tests.test_promise_evidence` and `tests.test_runtime_boundaries`. Both literal
  links, canonical bytes, Git identities and selected entries were retained.
  Live working contents/status and the entire clean source snapshot were
  unchanged. Native receipts bind the selected argv to this candidate, with
  zero model dispatches and successful CLI `status` readback.
- Fixed behavioral oracle controls: three tests passed.

Initial native controls inside the session sandbox were unavailable. Host retries
kept Proofline's native sandbox enabled. A protected attempt to run Git-dependent
snapshot/CLI-input suites was `CHECKS UNAVAILABLE`: `/usr/bin/git` could not
find Xcode developer tools within the minimum read profile. Those suites run
in the normal host suite; the passing native selection above requires no
permission expansion. These are unavailable execution observations, not product
failures or full-request certification.

Local full-checkout evidence is retained at
`/private/tmp/proofline-issue42-4nvtk77y/check/report.json`:

| Identity | Value |
| --- | --- |
| Candidate tree (before this observation document) | `57f171a7d10db5028e1e58f52b2781b4b0ff85e3` |
| Native selected-check receipt SHA-256 | `332162f0df69375d788a2140eb346908ebcd3be0e6209fc625e20d27f742ad75` |
| Separate host evidence SHA-256 | `13c369a0ac27d4b3649524dd2ae118488d0a688b5812a7aa4252601bb8e9a74a` |

The source file in that episode retains the user request and complete issue
text. The exact check argv uses the resolved Homebrew Cellar interpreter.
To reproduce on a clean checkout, retain the original request in `--source`
and choose a new output directory outside that checkout:

```sh
/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests -v
PROOFLINE_NATIVE_TESTS=1 /opt/homebrew/bin/python3.14 -B -m unittest \
  tests.test_check_only.CheckOnlyTests.test_native_clean_skill_aliases_keep_read_and_write_boundaries \
  tests.test_check_only.CheckOnlyTests.test_native_cli_denies_source_writes_candidate_writes_and_network -v
/opt/homebrew/bin/python3.14 -B proofline.py check \
  --repo /absolute/clean-proofline --source /absolute/original-request.txt \
  --command '/opt/homebrew/bin/python3.14 -B -m unittest tests.test_skill_discovery tests.test_feedback tests.test_promise_evidence tests.test_runtime_boundaries -v' \
  --output /absolute/new-output --seconds 180 --check-seconds 90
/opt/homebrew/bin/python3.14 -B proofline.py status /absolute/new-output/report.json
```
