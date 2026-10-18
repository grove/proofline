# Issue #57 — M5 Pro follow-up

**Basic local coding feasibility PASSED. Full Phase 0 qualification remains
incomplete; NO-GO for the two-task A/C pilot.** Recorded 2026-10-17.

The owner supplied independently verified M5 evidence: Apple M5 Pro, 48 GB
unified memory; Ollama 0.40.5 with `gemma4:26b-mlx`; 32,768 allocated context,
MLX, 100% GPU placement. Ollama's reported model footprint reached approximately
27 GB. Gemma corrected `clamp.py` with a one-line edit;
`python3 -m unittest -q test_clamp` passed all three tests and
`git diff --check` found no issues. The initial calculator smoke also passed.
Telemetry is retained locally at `~/gemma-proofline-telemetry/m5-gemma-live.log`.
Approximately 856 MiB of swap-outs occurred during monitoring. Longer-task
memory stability remains uncertain; the interval and other workloads are not
specified here, so no swapping rate or attribution is inferred.

These M5 observations were supplied as completed evidence, not rerun in this
session. This session exposes the earlier M1 Pro / 32 GB host and cannot access
the M5 telemetry. The [earlier M1 receipts](../issue57-phase0/README.md) remain
unchanged and describe a different host. Their model digest must not be used
as the M5's immutable identity. M5 digest, exact coding-client version/options,
load/first-token latency, coding throughput and peak host memory/swap remain
unverified here.

Existing mechanism inspection at commit
`d614429ab661e8e686ef618db81e33cbca09a28b` found:

- [`local_run.py`](../../../checks/local_run.py) requires macOS, Python 3.11+
  and exactly Codex CLI 0.162.1 for protected checks, even with zero model calls.
  The M5 was reported to have no Codex; a Claude skill does not supply that
  sandbox runtime. On this M1, an actual synthetic check stopped with
  `EXECUTION UNAVAILABLE` because installed Codex is 0.163.0, before checks or
  models ran. No version guard was bypassed.
- [`codex_live.preferences`](../../../checks/codex_live.py) rejects providers
  other than OpenAI. The supported managed path has no verified Ollama/Claude
  adapter. An earlier proposed `--oss --local-provider ollama` command was
  never an integration pass. Do not invoke managed `run` as a local fallback.
- Revalidation of all 15 historical artifact hashes and receipt assertions
  confirmed M1 model-free worker denials for private/oracle/sibling/repository
  reads, symlink/subprocess escape attempts, protected writes and networking,
  while allowing product edits and scratch. These are not M5/Claude receipts.
- The historical Seatbelt controller canary allowed TCP only to
  `localhost:11434` and denied other loopback/external connections. Its
  `(allow default)` policy restricts networking only: it does not isolate the
  controller's filesystem or Claude's direct file tools. A successful metadata
  GET does not prove protected coding-tool routing or absence of hosted fallback.

Before any A/C GO, the M5's actual existing client must demonstrate protected
read/edit/command/test execution with retained receipts: product/scratch access,
private/oracle/sibling denials (including direct client reads), worker network
denial, controller transport limited to local Ollama, and no hosted fallback.
The current supported path does not meet those prerequisites under the
no-Codex-install constraint. Sustained memory suitability at 32K also needs
bounded evidence. Then freeze the M5 digest/client/options, two fresh requests,
independently reviewed private acceptance/controls, finite budgets/order and
stop rules, and obtain explicit owner approval before assignments.

Validation: [verification.json](verification.json) records the prerequisite
failure, historical checks and focused offline regressions. Offline tests do
not qualify live isolation. No model dispatch, A/C assignment, install, 64K
context change, new framework, private-oracle disclosure or #52 rerun occurred.
