# Live S0 Codex runner

`checks/s0_live.py` continues PR #1's diagnostic workbench with the actual
Codex invocations required by H1–H5. It is deliberately limited to S0 fixtures.
It does not implement arbitrary repository requests, import positive verdicts,
publish, merge, or claim that later roadmap slices are finished.

## Run

Requirements: macOS, Python 3.11+, Git, an installed Codex CLI on PATH, and
existing Codex authentication. The implementation was exercised with Codex
0.162.1 and Homebrew Python 3.14. The macOS system `python3` can be older than 3.11;
select a supported interpreter explicitly.

```sh
/opt/homebrew/bin/python3.14 -B checks/s0_live.py
```

The default cumulative experiment budget is 1,200 seconds; each stage gets at
most 180 seconds and never more than the remaining budget. Override with
`--seconds` and `--stage-seconds`. Seven fresh model invocations are assigned:
one implementer, then separate reviewer/prover invocations for each of the
correct, alternative-correct, and defective controls. S0 deliberately runs the
prover on the defective control even when review rejects it: this tests both
judgments, unlike S1's intended review-first delivery gate.

The process must be able to apply Codex's native sandbox. A nested restrictive
sandbox can prevent `sandbox-exec` from initializing; that is a NO-GO, not a
successful isolation check. Run on an authorized normal host without disabling
Codex's own sandbox. The runner neither edits authentication nor changes global
configuration. It carries forward only the configured model and reasoning
preference, leaving credentials in Codex's store.

Every experiment creates a new ignored `.proofline/live/<id>/` directory.
`--output` selects another new directory. Existing runs are never overwritten.
Exit `0` means the fixed S0 experiment's observations matched; `2` means NO-GO
or invalid arguments; `1` means the new record could not be created. A process
interruption leaves the active dispatch visible; there is no resume or receipt
import command. Inspect interrupted work before starting a new experiment.

## Boundary and evidence

- A native diagnostic runs before models. Authentication, writable scratch,
  protected source/input/candidate/Git metadata, private reads, file modes, and
  loopback network denial must be observed. A timeout or connection refusal is
  not proof of denied networking.
- Each role uses fresh `codex --no-daemon exec --ephemeral --json`, never a fork
  or resumed session. User config and exec rules are not loaded; managed
  restrictions remain applicable. Shells do not inherit ambient credentials or
  login profiles. Apps, plugins, MCP config, web search, hooks, memories,
  delegation, browser, and computer-use surfaces are disabled.
- A native permission profile permits reads of one neutral fixture and runtime
  files, writes to one role's scratch, and denies private evidence access. On
  Apple Silicon Homebrew hosts, `/opt/homebrew` is a **read-only runtime root**:
  framework Python and Codex helper launchers traverse installation symlinks.
  User home, sibling fixture trees, the actual private oracle, and previous
  role transcripts are not runtime roots. The implementer additionally writes
  its disposable product, with Git metadata protected.
- Reviewer and prover execute the fixed canary as a standalone tool command.
  Only its matching host command receipt and actual JSON stdout count. Agent
  prose describing a denial does not count. The loopback positive control stays
  open throughout that role's invocation.
- Source, brief, candidate bytes/modes, and Git metadata are checked before and
  after verification. Each role receives an independently reconstructed neutral
  path with matching source/input/base/commit/tree identities. Paths do not
  change the binding identity. Neither role sees the other's scratch or verdict.
- Host JSONL, stderr, prompt hash, process outcome, unique thread ID, usage when
  supplied, exact command observations, and structured criterion results remain
  under host control. A final model message cannot manufacture a host receipt.
  Missing, changed, failed, oversized, unsupported, or ambiguous event streams
  prevent acceptance. Unknown usage stays unknown.
- Exact command-text references resolve to the latest completed execution of
  that command. A repeated or refined probe does not invalidate its new receipt;
  an explicit host item ID can reference an earlier execution. All executions
  remain in the raw log. Abbreviated or invented commands never match.
- The oracle's fixed expectations stay outside worker contexts. Both correct
  implementations must pass; the seeded defect must be rejected with a U1
  violation despite green existing tests. The live implementer's product is
  scored through a sandboxed execution callback, never imported by the oracle.

The report includes actual argv and native evidence. It is a local diagnostic
record, not a signature against a hostile machine owner. The Codex binary and
host controller are trusted components; the result is scoped to the recorded
host/version/configuration and these small fixtures. It is not a security audit,
a benchmark, universal correctness, or an assurance about other toolchains.

The host interface follows the official [non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode),
[permission profiles](https://learn.chatgpt.com/docs/permissions), and
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
Permission profiles are beta; unrecognized behavior must fail closed rather
than silently falling back to a broader sandbox.

## Regression checks

```sh
python3 -B -m unittest discover -s tests -v
python3 -B checks/fixtures/s0/test_oracle.py
# On an authorized macOS host, also exercise the real native boundary:
PROOFLINE_NATIVE_TESTS=1 python3 -B -m unittest discover -s tests -p test_codex_live.py -v
```

Offline tests establish mechanics, not live judgment. They cover receipt loss
and tampering, duplicate/failed sessions, unexpected tool surfaces, omitted or
contradictory criteria, stale bindings, fabricated command references, timeout,
changed source, unavailable hosts, and run preservation. The opt-in native
regression checks subprocess execution and denied source/receipt writes without
using a model. Live experiment findings and S0 gate status are recorded below.

## Observed macOS qualification — 11 October 2026 (Oslo)

**S0 GO on the recorded host.** Run `02323875ba104087aaa4cba79d33a833`
completed in 414.586 seconds using Codex 0.162.1, macOS 26.6.2 / Darwin 25.6.0
arm64, Python 3.14.8, and the existing configured `gpt-6-luna` / `high` preference.
Its seven distinct native thread IDs and exact argv are retained locally in
`.proofline/live/02323875ba104087aaa4cba79d33a833/report.json`.

| Candidate | Review | Proof | Fixed oracle |
| --- | --- | --- | --- |
| Live implementer output | Not assigned (S0 implementation receipt only) | Not assigned | All 19 observations matched inside the native sandbox |
| Correct control | PASS | PROVEN, U1–U4 satisfied | Accept |
| Alternative correct control | PASS | PROVEN, U1–U4 satisfied | Accept |
| Seeded whitespace defect | FAIL | FAIL, U1 violated | Reject |

All six verifier invocations independently ran the canary, including an attempted
read of the actual oracle. Private reads and source/input/product/Git/receipt
writes were denied; scratch writes worked; loopback networking was denied;
source and candidate identities remained unchanged. The fixed-candidate pairs
shared source/input/base/commit/tree bindings, with separate neutral locations
and no shared scratch, reports, or conversation.

H1–H4 are demonstrated by those live observations. H5 is covered by the
fail-closed transport and report regressions, plus real failed experiments below.
The full native test run passed 36 tests with two Linux-specific tests skipped;
the three independent oracle-control tests passed. This opens S1's dependency
gate; it does not establish S1, Milestone A, or a performance advantage.

The successful experiment reported 905,361 input tokens (783,360 cached), 28,058 output tokens,
and 8,747 reasoning output tokens. These are host-reported categories; cached input
is a subset, and reasoning output is not added again to output. Monetary cost
and human-attention cost were not measured.

### Failed development experiments remain visible

| Local run prefix | Model stages | Elapsed seconds | Why it remained NO-GO |
| --- | ---: | ---: | --- |
| `970d737c` | 1 | 54.9 | Missing runtime aliases; abbreviated evidence references |
| `6b1fb203` | 1 | 61.6 | Runtime helper paths; a cited command was only part of a compound invocation |
| `f2afefcd` | 3 | 149.9 | A literal tab was changed to a backslash escape in a citation |
| `c1e40070` | 1 | 95.5 | Codex's UTF-8 argument parser rejected the fixed POSIX byte-argument case |
| `fb9256ba` | 3 | 189.8 | The resolver rejected a valid repeated probe command |

These five failed experiments consumed nine additional stage dispatches. They
are development observations, not a four-way benchmark. None was converted into
a success or silently omitted. Runtime read paths, standalone evidence guidance,
an ASCII-safe argv trampoline inside the sandbox, and latest-completed-command
resolution fixed the demonstrated problems. The trampoline preserves the source
promise and oracle cases unchanged. Initial standalone native diagnostics and
implementation work are additional development cost outside these run totals.
