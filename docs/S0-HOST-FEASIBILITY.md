# S0 host feasibility — current executor

**Decision: NO-GO for live S0 on this executor; host NOT QUALIFIED.**

This is an initial feasibility finding, not a completed Proofline implementation.
The governing requirements are [DESIGN.md, Milestone 0](../DESIGN.md#milestone-0--prove-the-minimal-host-boundary)
and [IMPLEMENTATION.md, S0](../IMPLEMENTATION.md#s0--prove-the-real-host-boundary-before-building-the-controller).
S1 must wait for a demonstrated real-host S0 pass.

## Observed host and commands

Observed on 10 October 2026 UTC (11 October in Europe/Oslo), inside the current
restricted execution environment. The working directory was
`/workspace/scratch/ee1f9f972a66`. The CLI was addressed by absolute path because it
was not on the shell's PATH.

| Command | Exit | Relevant output |
| --- | ---: | --- |
| `uname -a` | 0 | `Linux a88c2b563bff 6.18.44 #1 SMP Sat Sep 26 20:02:31 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux` |
| `/opt/codex/bin/codex --version` | 0 | `codex-cli 0.159.2` |
| `/opt/codex/bin/codex --help` | 0 | Advertises noninteractive `exec`, sandbox controls and approval policy. |
| `/opt/codex/bin/codex exec --help` | 0 | Advertises fresh execution separately from `resume`/`fork`, `--ephemeral`, `--ignore-user-config`, `--json` and `--output-schema`. |
| `/opt/codex/bin/codex login status` | 1 | `Error loading configuration: no /proc/self/exe available. Is /proc mounted?` |
| `/opt/codex/bin/codex sandbox -- /usr/bin/true` | 1 | `Error: no /proc/self/exe available. Is /proc mounted?` |
| `bwrap --version` | 0 | `bubblewrap 0.9.0` |
| `bwrap --ro-bind / / --unshare-net --die-with-parent /usr/bin/true` | 1 | `bwrap: Can't read /proc/sys/kernel/overflowuid: No such file or directory` |
| `unshare --user --map-root-user --mount /usr/bin/true` | 1 | `unshare: cannot open /proc/self/uid_map: No such file or directory` |

Codex commands also emitted this initialization warning, including commands that
successfully displayed help or their version:

```text
WARNING: proceeding, even though we could not create PATH aliases: no /proc/self/exe available. Is /proc mounted?
```

Direct existence checks found `/proc`, `/proc/self/exe`, `/proc/self/status` and
`/sys/kernel/security/lsm` absent. Read-only syscall queries reported seccomp mode
`2`, `no_new_privs=1`, and a Landlock ABI query returned `-1` with errno `38`
(`ENOSYS`). These observations describe this executor; they do not establish a
verifier-specific policy or show that Linux generally cannot support Proofline.

**Authentication is unknown:** `login status` failed during initialization before
it could report authentication. No credentials were inspected, no configuration
or authentication was changed, and no model invocation or external write was
performed for these probes.

## S0 acceptance status

| Criterion | Status | Evidence or missing observation |
| --- | --- | --- |
| **H1 — fresh independent invocations and host receipts** | NOT VERIFIED | No implementer, reviewer or prover model invocation ran. No live invocation receipts were obtained. CLI help is not evidence of actual context isolation. |
| **H2 — protected inputs/candidate/receipts and writable scratch** | NOT VERIFIED | Native sandbox initialization failed. No verifier write denial or protected build/test execution was demonstrated. |
| **H3 — accept correct behavior and expose the seeded fault** | NOT VERIFIED | No real reviewer/prover judgment ran on either candidate. Fixture and oracle checks must be reported separately as offline evidence. |
| **H4 — denied or unavailable unauthorized external effects** | NOT VERIFIED | The outer executor is restricted, but the required verifier-specific tool/network boundary was not demonstrated. Sandbox startup failure is not a successful network-denial test. |
| **H5 — fail closed when required evidence is missing** | OFFLINE NEGATIVE CHECKS DEMONSTRATED; LIVE GATE OPEN | The diagnostic returns NOT VERIFIED on missing native evidence, and tests reject incomplete/mutated canaries. Fabricated positive transport messages cannot qualify S0. Live invocation/report failure cases still await the real runner; these checks do not establish H1–H4. |

There is no live PASS/PROVEN outcome or independent acceptance in this note.
No S1 implementation should begin on the strength of offline fixtures or the
presence of a Codex binary.

## Executed diagnostic and fixture controls

The implemented reproducible capability command is:

```sh
python3 -B checks/host_probe.py --codex /opt/codex/bin/codex
```

The accompanying deterministic test command is:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B checks/fixtures/s0/test_oracle.py
```

The diagnostic ran at **2026-10-10 22:25 UTC** with Python **3.12.14**. It exited
`2`, recorded **NOT VERIFIED / NO-GO**, kept authentication **unknown**, and
captured native sandbox exit `1` with the `/proc/self/exe` initialization error.
It retained **zero model dispatches**, **no model receipts**, and **unknown model
usage**. This is a diagnostic outcome, not a live acceptance result.

The deterministic suite contains **23 tests**. On this executor, **22 pass and
one is explicitly skipped** because readable Linux `/proc` process state is
unavailable. Descendant cleanup is therefore not claimed as verified here.
The three fixture-control tests pass. Both correct implementations match all
**19 POSIX public-interface observations**, while baseline/seeded-defect controls
fail the promised blank-name behavior despite green ordinary tests. The oracle
includes a POSIX undecodable-byte argument case found during independent code
review; both good controls now preserve that value through valid JSON.

The run preserves reconstructible fixture identities:

| Item | Recorded identity |
| --- | --- |
| Original source SHA-256 | `679ea432572c0f3f9c577ac749eb7dbbb7ffb93fe7b315367eaac34d88729802` |
| Accepted input SHA-256 | `f901d5e86760bd104b011f66f0d24dd555ebb5b66fb28b9404ec0d90a336d1ff` |
| Common Git comparison base | `838a00539c7046197604505d3383e0975fa4128c` |
| Correct candidate | `c09e5d25a842d470f6c20235342ff47067068ce0` |
| Alternative correct candidate | `d00329870bf62115cf77cf561487fb3218aa8751` |
| Defective candidate | `e292eb9e5d851a453c12c364b1fb311f9b51beb7` |

All three frozen input trees were unchanged by the offline oracle. These commits
live in newly created disposable fixture repositories, not in Proofline's own
history. The ignored run record also contains candidate tree hashes, full
per-observation results and bounded native-process output. Git publication of
the workbench does not change the S0 NO-GO decision.

The fixture oracle is a separate offline control: it checks known-correct,
structurally different correct, and deliberately defective implementations
against fixed behavior. Even a passing oracle establishes only that the fixture
can distinguish those cases. Keep the oracle and candidate answer labels out of
the reviewer/prover contexts during the live spike.

## Concrete next host action

Run the small S0 spike on a normal authenticated Codex CLI host, starting with the
design's proposed macOS environment or a Linux environment whose native sandbox
can initialize. Re-run the version/authentication/native-sandbox checks there
before dispatching any model. Do not alter or bypass this executor's restrictions
to turn this finding into a success.

Prefer the CLI's native permission controls. The diagnostic uses a temporary
named permissions profile passed via CLI arguments: minimal/runtime and fixture
reads, one writable scratch directory, denied private-canary access, and command
network access disabled. It includes managed requirements and does not change
persistent configuration. This follows the CLI's installed help and the official
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The profile has **not** been qualified here because native initialization fails.
The exact effective read allowlist, available tools/MCPs, context isolation and
receipt protection must still be established on the chosen host. Command network
restrictions alone do not restrict model-accessible apps, MCPs or web search.

With minimal disposable glue, launch fresh independent reviewer and prover
invocations against protected source, accepted input, base and candidate. Capture
host-issued identities and process evidence outside verifier write access.
Demonstrate rejected product/receipt writes, permitted disposable build output,
denied unauthorized external effects, stable candidate identities, correct-case
acceptance and seeded-defect rejection. Exercise the H5 failure cases. Record the
actual commands, receipts, limits and results before changing this NO-GO decision.

If those controls require a substantial new controller, follow S0's stop/pivot
rule and reconsider the host before expanding Proofline.
