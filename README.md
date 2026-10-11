# Proofline

Let capable coding agents solve problems. Preserve the user's complete promise,
then independently review and challenge the exact result.

Proofline is an experiment in reducing delivery overhead while retaining
credible acceptance. [DESIGN.md](DESIGN.md) defines the product;
[IMPLEMENTATION.md](IMPLEMENTATION.md) orders its evidence gates.

## What works now

**Runnable direct local delivery through Codex.** One autonomous implementer
produces an isolated candidate; fresh independent review and behavioral proof
check the same frozen source, brief, comparison base, and candidate. Review runs
first and skips proof on a material blocker. The original repository is preserved.

| Slice | Status |
| --- | --- |
| S0 — Real host boundary | Demonstrated on macOS with seven fresh Codex invocations; correct and alternative implementations pass, seeded defect fails |
| S1 — Direct local delivery | Demonstrated on two small CLI tasks; source omissions and regressions rejected |
| S2 — Approved contracts | Experimental standalone Markdown adapter and input checks; actual approved-contract live qualification pending |
| S3–S6 — Comparison, recovery, publication, pilot | Not started; preceding evidence gates remain binding |

Read the [S0 results and failed experiments](docs/S0-CODEX-RUNNER.md),
[S1 evidence](docs/S1-DIRECT-DELIVERY.md), and
[contract adapter's exact support boundary](docs/S2-CONTRACT-INPUT.md).
These results establish neither broad correctness nor a performance advantage.

## Deliver a direct request

The qualified runtime is **macOS, Codex CLI 0.162.1, Python 3.11+, Git**, with
existing Codex authentication. Live observations used Apple Silicon, Python
3.14.8, and the user's configured model and reasoning effort. Other hosts/CLI
versions need S0 qualification first. There are no third-party Python dependencies.
The macOS system Python may be too old; select a supported interpreter explicitly.

Use a clean Git repository with regular tracked files. Save the original request
verbatim as `source.md` and a small source-grounded `brief.md` outside that
repository's tracked changes. A brief indexes every material promise with stable
IDs; it cannot narrow the source. For example:

```markdown
| ID | Required observable outcome |
| --- | --- |
| D1 | --version prints greet 1.0 and exits successfully without requiring a name. |
| D2 | Existing positional-name greetings, help, and argument errors are preserved. |
| D3 | No new dependencies or external effects. |
```

```sh
python3 -B /absolute/path/to/proofline/proofline.py deliver \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --brief /absolute/path/to/brief.md \
  --map 'Relevant commands, public interfaces, fixtures and environment gaps' \
  --seconds 900 --stage-seconds 240 --verification-reserve 120

python3 -B /absolute/path/to/proofline/proofline.py status /path/to/run/report.json
```

This consumes real model usage. A new ignored `.proofline/delivery/<id>/` directory
contains the candidate, protected role transcripts, and one `report.json` with
identities, observations, dispatches, elapsed time, and available usage. `--output`
selects a new directory; existing runs are never overwritten. Successful `status`
revalidates candidate identity and native receipt evidence before showing the
candidate path and commit. Exit `0` means local acceptance; `2` means a gap,
rejection, exhausted budget, stale evidence, or invalid input.

**LOCAL ACCEPTED means not published or merged.** Inspect the retained candidate
and diff; the tool does not copy changes into your original checkout. There is
no correction, resume, publication, or receipt-import command yet. A timeout or
interruption preserves evidence and any active dispatch. Inspect that record;
do not silently start another episode to reset its budget.

Models run under native permissions with read-only binding inputs and verifier
candidates, separate writable scratch, and protected host receipts. Network,
ambient shell credentials, MCP, plugins, web, delegation, and browser/computer
surfaces are unavailable. The native sandbox must initialize on the host; a
nested sandbox failure is an explicit gap, never a reason to disable isolation.

The initial boundary does not support symlinks, submodules, ignored local
dependencies, or tests that need to modify their source tree. Such tasks need a
qualified build/observation path. Supply exact interpreter/tool paths in the map
when macOS developer-tool discovery is unavailable inside the sandbox.

## Use as a Codex skill

[SKILL.md](SKILL.md) is the single `/proofline` entry point. Keep it with this
repository's scripts. To install a personal skill, link the whole checkout into
your Codex skills directory (choose an unused destination):

```sh
mkdir -p ~/.codex/skills
ln -s /absolute/path/to/proofline ~/.codex/skills/proofline
```

The skill prepares the source and brief in the initiating context, invokes the
runner, and checks the retained outcome. No P2P controller or planning agent is
required. Installation is optional; the CLI works directly.

## Check and qualify

Offline checks need only Python 3.11+ and Git:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B checks/fixtures/s0/test_oracle.py
```

Native qualification on an authenticated authorized host:

```sh
# Diagnostic only: zero model calls, always leaves S0 unqualified (exit 2).
python3 -B checks/host_probe.py
# Actual S0 qualification: seven fresh model calls.
python3 -B checks/s0_live.py --seconds 1500 --stage-seconds 240
# S1 negative judgment controls: four fresh model calls.
python3 -B checks/s1_judgments.py
# Native subprocess/permission regressions, no model calls.
PROOFLINE_NATIVE_TESTS=1 python3 -B -m unittest discover -s tests -v
```

Canaries use disposable files and a controlled local listener. Timeout or refused
connections do not count as network denial. Fixed answer keys stay outside worker
contexts. Raw evidence remains local and ignored by Git. The original PR's
[Linux NO-GO](docs/S0-HOST-FEASIBILITY.md) is retained; it describes that executor,
not all Linux hosts.

## License

[Apache License 2.0](LICENSE).
