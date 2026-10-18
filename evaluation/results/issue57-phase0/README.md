# Issue #57 — Phase 0 local Gemma feasibility: NO-GO

**NO-GO for the small A/C pilot under the observed host load.** On
2026-10-16, the already-loaded 32K model coexisted with active swapping and
memory pressure before any evaluation inference. Stop before model dispatch;
this does not establish that the model cannot work on a quieter host.

The owner initially specified M5 Pro / 48 GB. Native inspection instead found
**Apple M1 Pro, MacBookPro18,1, 34,359,738,368 bytes (32 GiB)**; the owner then
explicitly authorized using that host. These findings apply to that machine,
not the originally described M5 Pro. macOS **26.6.2 (25G83)**,
Ollama client/server **0.40.5**, Codex CLI **0.163.0**.

## Observed model and resources

| Item | Observation |
| --- | --- |
| Installed tag | `gemma4:26b-mlx` |
| Exact digest | `f0fc7e0ae4947d382989b1f57db3d098a86b87c5b6e9523b9561ba81a2a64879` |
| Format / quantization / parameters | safetensors / NVFP4 / 26,225,562,962 |
| Template / renderer / parser | `{{ .Prompt }}` / `gemma4` / `gemma4` |
| Advertised capabilities | completion, vision, tools, thinking; not agent qualification |
| Installed sampling defaults | temperature 1, top_k 64, top_p 0.95; thinking true |
| Advertised maximum / runtime allocation | 262,144 / **32,768 tokens** |
| Ollama placement / runner | **100% GPU / MLX** (`ollama ps`) |
| Reported model size / VRAM | **18,272,024,260 bytes each** (`/api/ps`); not total host or peak inference memory |
| Idle pressure samples | raw `kern.memorystatus_vm_pressure_level=2`; `memory_pressure -Q`: **13% free**, all three samples |
| Idle swap used | **33,765.06 → 33,814.12 → 33,795.94 M**, as reported by `sysctl` |
| Swap I/O over 10.187 seconds | **199.406 MiB in / 230.375 MiB out**, from 16,384-byte pages |

Samples span 18:14:00.862–18:14:11.049 UTC. The sampled swap-used maximum
was 33,814.12 M; a peak over an inference run was **not measured**. Cumulative
compression/decompression counters each advanced by about 27.3 GiB in this
interval. Background applications were not controlled; neither the swap
occupancy nor the I/O can be attributed solely to Ollama. GPU utilization,
power, thermal throttling and CPU/GPU layer counts are **UNKNOWN**; the CLI's
placement report is not a utilization measurement.

The 32K allocation was already present when inspection began. **No inference
request, cold load, full-context occupancy test or coding-agent session was
started.** Load latency, first-token latency, prompt/decode tokens per second,
coding throughput and provider usage/cost are **UNKNOWN**, not zero. The
read/edit/test/result-inspection agent smoke is **NOT_EXECUTED**, so native
tool support remains **NOT VERIFIED**. **64K was not attempted**, because the
32K stability prerequisite did not pass. No claim about a required Codex
minimum context follows from these observations.

## Protected boundary observations

The disposable repository and scratch were created under ignored
`.proofline/issue57-phase0-work/`. The checks reused
`checks.host_probe.boundary_fixture`, `permission_profile`, `run_command`,
and `checks.codex_live.command`; no runner, controller or production code was
added. A host-owned Python canary, **not Gemma**, executed inside the existing
Codex worker permission profile, including managed restrictions:

- Product editing, product mode changes and scratch writes succeeded.
- Source/input, Git HEAD and receipt writes were denied; protected snapshots
  remained equal. Only the deliberately writable product canary changed.
- Receipt, oracle, sibling, enclosing-repository and symlink-to-private reads
  were denied. A subprocess private read failed with `PermissionError`.
- A symlink-to-source write and both loopback and external command connections
  were denied. The loopback listener was reachable outside the sandbox first.

A separate native Seatbelt **controller transport canary** allowed outbound
TCP only to `localhost:11434`, with network otherwise denied. It retrieved
`http://127.0.0.1:11434/api/version`; connections to another loopback port and
an external address failed with `EPERM`. This is transport evidence, **not an
agent/controller integration pass**. Worker commands retained network denial.
No private review documents, task solutions, private grader data or sibling
task contents were supplied to a model. No local model inference, model
download/upgrade or external inference fallback occurred. GitHub publication
and documentation lookup were operator activity outside the worker boundary.

Retained diagnostic failures: the first controller probe used unsupported
literal-IP Seatbelt syntax and exited 65 before networking; the corrected
`localhost:11434` probe passed. The standard receipt helper truncated the first
`/api/show` response (duplicated license text); the complete response was
recaptured to a file with its byte count and hash. Neither failure was hidden
or counted as model/tool failure.

## Proposed settings — approval pending

See [proposed-settings.json](proposed-settings.json). Freeze the observed digest,
Ollama/Codex versions, **32,768** runtime and client context, installed sampling
defaults, one local model/request at a time, the existing protected command
profile, and the endpoint-only controller network restriction. A client that
requests a larger context must stop; changing `model_context_window` alone
does not prove the server allocation. The documented client route is
[`--oss --local-provider ollama`](https://learn.chatgpt.com/docs/config-file/config-advanced#oss-mode-local-providers),
but this exact tag's integration has not been exercised.

These are a **proposed Phase 0 retry freeze**, not validated A/C settings or
permission to run experiment arms. First establish a quiet memory baseline;
then allow at most one bounded inference probe and one disposable client smoke,
five minutes total, retaining streamed timings, `/api/ps`, memory/swap samples,
native tool events, the patch and the executed test result. Stop on renewed
pressure, sustained swap activity, context drift, tool-routing or isolation
failure. Defer 64K until 32K passes. The conservative proposed memory thresholds
are new retry stop rules, not a predeclared criterion retroactively applied to
this inspection.

All A/C episodes remain **NOT_EXECUTED**. The completed #52 files and production
behavior are unchanged. A later A/C freeze still needs two fresh requests,
independent acceptance/control review, finite budgets/order and explicit owner
approval after Phase 0 passes. #57 remains open.

## Receipts

- [Host/version receipts](host.json), [model digest](ollama-tags.json),
  [runtime allocation](ollama-ps.json), [idle memory samples](idle-memory.json).
- [Complete model metadata](ollama-show-full.json),
  [metadata recapture receipt](ollama-show-retry.json),
  [original truncated receipt](ollama-show.json), [server version](ollama-version.json).
- [Worker canary source/spec](boundary-canary.json),
  [native worker receipt and snapshots](worker-boundary.json),
  [initial transport failure](controller-network.json),
  [corrected transport receipt](controller-network-retry.json).
- [Machine-readable result](result.json); [artifact hashes](SHA256SUMS.json).

Checks: receipt assertions verified the exact digest and runtime context,
protected snapshot equality, permission-denial results, transport results and
memory arithmetic. These checks establish the reported observations; they do
not establish coding-agent feasibility.
