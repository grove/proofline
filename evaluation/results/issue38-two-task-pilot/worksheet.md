# Four-slot grading worksheet

All four authorized slots are now consumed. The prompts preserve the exact task
inputs; this worksheet does not authorize a retry or a new campaign.

Use only the supplied four prompts, in the protocol order. Start each attempt in
an empty context and its own clean baseline checkout. Select `gpt-6-luna` and the
specified effort in the same host. Run serially, with about 900 seconds per
attempt, no retries, external reviewer, extra planner, correction turn or paid
fallback. Keep worker self-repairs within the original attempt in its totals.

Do not open this report, its probes, controls, or another candidate in a worker.
A runner/operator may use `checks.coding_attempt.run` as in this pilot; do not
reuse a completed slot. If manual host setup differs from the observed host,
record it and keep those results as a separate run.

| Slot | Prompt | Model/effort |
| --- | --- | --- |
| 1 | `prompts/01-dotenv-medium.txt` | GPT-6 Luna / medium |
| 2 | `prompts/02-dotenv-high.txt` | GPT-6 Luna / high |
| 3 | `prompts/03-humanize-high.txt` | GPT-6 Luna / high |
| 4 | `prompts/04-humanize-medium.txt` | GPT-6 Luna / medium |

Each prompt contains the entire original request. The corresponding
`*-base.tar.gz` contains the exact tracked starting files; `protocol.json`
records original commit/tree identities. No later solution/history is needed.
Verify hashes against `input-hashes.json` before handing out inputs. Supply the
same Python/test dependencies and native permissions to both efforts. Where
pytest is available, use the ordinary commands in `acceptance.md`; otherwise
record UNAVAILABLE rather than fabricate a passing suite. Humanize normally
needs a build/install to produce `_version.py`; record any setup consistently.

Record for each slot:

- Actual model and effort configuration; exact backend identity if exposed,
  otherwise UNKNOWN. Host/CLI/Python and dependency differences.
- Start/end timestamps and elapsed seconds including all self-testing and
  self-repairs; preparation and independent grading separately.
- Initial base commit/tree, final tree, binary-capable patch, all new files and
  file modes, SHA-256 hashes, and final handoff text.
- Exact test commands, cwd when observable, exit status, output summary,
  intermediate failures, and unavailable checks.
- Model turns/tool calls and input/output/cached tokens when observed. Cached
  tokens are part of input, not additional input. Actual charges UNKNOWN unless
  a real charge is exposed; do not substitute a price estimate.
- Human interventions and remaining issues. No intervention may supply a fix or
  hidden expectation to one worker. Mark an invalid comparison if that occurs.

After freezing each terminal candidate, run the relevant `probe_*.py` through
`evaluation.recovery.grader.invoke(candidate, probe_text, new_directory)` on the
supported native host with its protected read-only candidate. The shim supplies
candidate root as `sys.path[0]`. Keep actual command/cwd/status/output and the
native receipt. Do not run untrusted candidate code in an unprotected process.
Also review the final diff and worker tests against the complete source request.
Probes are finite samples; their pass alone is not whole-task certification.

Choose exactly one assessment and explain supporting evidence:

- Independently supported correct delivery (within stated verification scope).
- Confirmed material defect (exact source clause and reproduced counterexample).
- Incomplete or unavailable verification (which requirement/evidence is missing).
- Disputed or ambiguous expectation (keep judgment pending).

A source-valid alternative passes even when it differs from a control patch.
A missing dependency or altered interpreter receipt is an execution limitation,
not automatically a model defect. If human judgment is needed, retain the diff,
source clause and competing interpretations; record PENDING.

Only compare complete valid pairs. Report every assigned slot, including failed
or unexecuted slots. Choose MEDIUM PREFERRED, HIGH PREFERRED, NO CLEAR DIFFERENCE,
or INCONCLUSIVE using actual correctness and entire-attempt resources. Two tasks
do not support statistical significance or a product-wide routing change.
