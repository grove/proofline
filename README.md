# Proofline

A bounded coding attempt followed by explicit executable checks.

Proofline preserves the original request, works in an isolated Git snapshot,
freezes the candidate, and records the caller-selected command results. **CHECKS
PASSED describes those commands. It does not certify the complete request.**
The source repository stays untouched; the caller decides whether the result
fulfills the promise.

[S6 closed with an abandon/simplify decision](docs/S6-DECISION.md) on 13 October
2026, under the owner's explicit scope revision. Automated full-promise
certification was abandoned after repeated native false acceptances. The original
full comparisons remain incomplete; no efficiency or model-superiority claim is
established. [DESIGN.md](DESIGN.md) defines the revised product and
[IMPLEMENTATION.md](IMPLEMENTATION.md) records the implementation direction.

## Run a request

The supported host is macOS, Python 3.11+ and Codex CLI 0.162.1 with existing
Codex authentication. Native observations used Homebrew Python 3.14.8. The macOS
system Python may be too old; select the interpreter explicitly.

Use a clean Git source repository. Preserve unrelated changes in a separate
committed snapshot rather than resetting them. Save the exact request and a JSON
list of command argument lists outside product changes, for example:

```json
[["/opt/homebrew/bin/python3.14", "-B", "-m", "unittest", "discover", "-s", "tests"]]
```

```sh
/opt/homebrew/bin/python3.14 -B /absolute/path/to/proofline/proofline.py run \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --seconds 900 --stage-seconds 600 --check-seconds 120
```

There is one implementation model dispatch and no automatic reviewer, prover,
repair loop or publication. The configured Codex model preferences are recorded.
All preparation, coding and checks share the episode budget. Each check also has
its own timeout. The commands run against the frozen read-only candidate with
network access denied and temporary writes confined to scratch. Use explicit
executable paths; command arguments are not implicitly parsed by a shell.
Tests requiring writes inside the candidate need a different check command or
observation path. No dependency installation is performed by the host runner.

The output names the isolated candidate and its report. Command failures and
unavailable executions remain distinct. Partial implementation handoffs are
retained without a successful-check claim. No failed run silently restarts.

```sh
/opt/homebrew/bin/python3.14 -B proofline.py status /absolute/path/to/report.json
```

Status checks the frozen inputs, declared commands and successful receipts.
Candidate or source drift invalidates a previously successful check record.
Full source correctness, coverage and human acceptance remain separate facts.

## Retained experiments

| Slice | Evidence status |
| --- | --- |
| S0 | Native host/isolation observations retained; see [host evidence](docs/S0-CODEX-RUNNER.md) |
| S1–S2 | Small direct and adopted-contract demonstrations retained; see [direct delivery](docs/S1-DIRECT-DELIVERY.md) and [contract evidence](docs/S2-LIVE-EVIDENCE.md) |
| S3 | Small four-way comparison retained with its original limits; see [results](docs/S3-COMPARISON.md) |
| S4–S5 | Recovery and authorized disposable-repository publication observations retained; see [recovery](docs/S4-RECOVERY.md) and [publication](docs/S5-PUBLICATION.md) |
| S6 | **Decision closed under revised scope.** Full comparisons incomplete: original 69/120 and follow-up 4/144; see [decision and limits](docs/S6-DECISION.md) |

Earlier finite demonstrations did not establish reliable full-source model
certification. Historical reports and raw receipts are preserved. Original S6
scores stay unchanged, with expanded readback disclosed separately. Cached tokens
remain part of input, unknown measurements remain unknown, and stopped campaigns
are never described as completed comparisons.

The old delivery, contract, recovery and publication code is retained for research
and historical readback. `deliver` and `resume` require `--experimental`; their
model verdicts do not certify full source coverage. Any historical remote effect
still requires its exact separate grant. The current `run` command supports only
local coding and checks, with no push, PR, merge or deployment.

See [historical S6 results](docs/S6-RESULTS.md), [first follow-up](docs/S6-FOLLOWUP.md),
[verification redesign](docs/S6-VERIFICATION-REDESIGN.md),
[text-domain findings](docs/S6-TEXT-QUALIFICATION.md) and
[scope-stopped scalar qualification](docs/S6-SCALAR-QUALIFICATION.md).
Raw transcripts and private evaluator artifacts remain ignored and unavailable
to workers.
