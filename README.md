# Proofline

Let capable coding agents solve problems. Preserve the user's complete promise,
then independently review and challenge the exact result.

Proofline is an experiment in reducing delivery overhead while retaining
credible acceptance. The [design](DESIGN.md) defines the product;
the [implementation roadmap](IMPLEMENTATION.md) orders the evidence gates.

## Current implementation

**S0 host-feasibility workbench; not yet a delivery tool.** The repository now
contains executable fixtures, an independent fixture oracle, a native host
diagnostic, and deterministic failure-path tests. The current executor cannot
initialize Codex's sandbox. See the [observed host-feasibility result](docs/S0-HOST-FEASIBILITY.md).

| Capability | Status |
| --- | --- |
| Frozen source/input and disposable Git base/candidate fixtures | Implemented |
| Known-good, alternative-good and seeded-defect oracle controls | Implemented; ordinary tests deliberately miss the seeded defect |
| Codex version/authentication and native permission diagnostics | Implemented; records observed errors and unknowns |
| Fresh model review/proof with trusted, protected invocation receipts | Not yet qualified or implemented as a live runner |
| S1 direct delivery, S2 accepted contracts, comparison, correction and publication | Not started; depend on a demonstrated S0 pass |

No command in this increment implements a user request or declares a product
ACCEPTED, PASS or PROVEN. Diagnostic process receipts are **not** model invocation
receipts. A successful preflight would still need the real S0 judgment experiment.

## Run the checks

Requirements: Python **3.11 or later** and Git. There are no third-party Python
dependencies, and the deterministic tests do not need Codex, P2P, credentials or
network access.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B checks/fixtures/s0/test_oracle.py
```

The oracle exercises each fixture's actual command-line interface. The baseline
and seeded defect must fail its behavioral expectations; both correct variants
must match. The fixtures' existing tests are intentionally green on all variants.
This establishes evaluator controls, not model judgment quality or full product
acceptance. [Fixture details and limitations](checks/fixtures/s0/README.md).

## Diagnose a prospective host

Use an existing installed Codex CLI:

```sh
python3 -B checks/host_probe.py
# Or select an explicit executable:
python3 -B checks/host_probe.py --codex /absolute/path/to/codex
```

The command creates a new ignored `.proofline/s0/<run>/` directory containing
frozen fixture repositories and one `report.json`. It preserves existing runs.
Use `--output <new-directory>` to select a different location and `--timeout 15`
to bound each native diagnostic process.

It checks executable fixture behavior, records source/input hashes and Git
identities, observes CLI version and authentication status, and attempts native
sandbox canaries against **disposable** source, candidate, Git metadata and
receipt files. It checks separately writable scratch, denied reads of private
canaries, file-mode protection and network denial against a local loopback
control. Source/receipt changes invalidate the mechanical observation. A
connection refusal or timeout is not treated as proof of network denial.

The diagnostic invokes no models and changes no authentication or persistent
Codex configuration. It uses a temporary named permission profile passed on the
command line and honors managed restrictions. It does not probe arbitrary remote
services. Its native-process checks cannot establish the tool, MCP, or context
boundaries of a future model invocation.

Exit codes:

| Code | Meaning |
| --- | --- |
| `2` | S0 remains **NOT VERIFIED / NO-GO**. This is the expected diagnostic result, even if mechanical canaries succeed. Argument errors also use argparse's code `2`. |
| `1` | A new run directory/record could not be created. |

The report retains zero model dispatches, an empty model-receipt list, and
unknown model usage. It has no option to import a verdict or convert offline
results into live qualification. Raw records remain local and are ignored by Git.

## Next implementation gate

Finish **S0** on a working authenticated Codex host. Demonstrate fresh independent
reviewer/prover contexts, protected source/input/base/candidate and receipts,
usable build/test scratch, denied unauthorized effects, and correct-versus-defect
judgments with real invocation evidence. Qualify a minimal host-native launch
configuration before building the S1 delivery path.

The current failure is specific to this executor's unavailable `/proc` paths;
it is not a finding that Linux cannot work. The design's proposed macOS host is
also a candidate, not an already qualified implementation.

## License

[Apache License 2.0](LICENSE).
