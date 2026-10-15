# Phase 2: executable qualification, with review gates still closed

[Observed controls, stops and evidence](../results/issue52-phase2/README.md).
This implements the model-free portion of the phase-1 worksheet. **The cohort
is NOT QUALIFIED for live execution.** No study worker, additional model reviewer,
model inference or expenditure was invoked. There is no `execute` command.

## Artifacts and scope

- `phase2.json` pins the four historical source blobs, actual base and reference
  commits/trees, pre-change test command, local alternative/defective patches and
  finite control caps. The phase-1 declaration and all 16 slots stay unchanged.
- `oracles.py` contains finite behavioral probes authored before worker attempts,
  independently of any worker-generated tests. The probes cover receipt identity
  and tampering, unsupported annotations, absent/truncated/timeout evidence,
  mapping source/ID/argv/candidate rejection, linked/unlinked outcomes, untrusted
  exports, explicit links, and source-linked advisory next actions.
- `qualify.py` binds those probes to exact draft source clauses using the existing
  `source_preflight` checks. Its **structural** QUALIFIED result never grants
  semantic qualification: complete source audit and independent review stay
  PENDING. It reuses #38 snapshot/history capture and the protected #34 command
  invocation; it neither grades whole-source delivery nor dispatches workers.
- `native.py` reuses #16's worker/grader canaries and real producer/export/import/
  check/readback control, plus the existing no-turn model-catalog client. The
  supported original single-S1 schema-1 revision-1 round trip was observed.

Controls start from the pinned implementation commit, replace its tests with
**exact pre-change tests**, apply an exact-anchor patch, and freeze the actual
resulting tree. Reference solution tests never become the ordinary suite.
Alternative controls are independently authored *local equivalent rewrites*,
not independent whole-product solutions or human replication. The finite probe
interface follows existing project APIs and is not a universal implementation
oracle. An independent reviewer must decide whether these controls sufficiently
exercise permissible alternatives and all material source obligations.

The omission control changes only how an unlinked requirement is classified.
Its complete original 109-test suite passes (7 pre-existing opt-in skips), while
withheld mapping probes reject its false passing-evidence claim. This qualifies
a deliberately constructed green-suite omission, **not a naturally occurring
worker failure or an assistance benefit**.

## Reproduce without inference

Use the supported macOS host, installed Python and Codex 0.162.1. Fresh output
directories are required; stopped directories cannot resume or be overwritten.
Keep the checkout and private evidence outside `/private/tmp`: this host's native
minimal profile allows reads there. Canaries must reject any exposed layout.

```sh
/opt/homebrew/bin/python3.14 -B -m unittest tests.test_issue52 -v
/opt/homebrew/bin/python3.14 -B -m evaluation.issue52.qualify controls \
  --native --green-suite --output "$PWD/.proofline/issue52-fresh-controls"
/opt/homebrew/bin/python3.14 -B -m evaluation.issue52.native \
  --output "$PWD/.proofline/issue52-fresh-host"
```

Native qualification must run from host execution. Offline fixture development
may omit `--native`; that mode runs only these trusted, bundled controls and is
not native qualification or permission to grade arbitrary candidate code.

Original archival tests need reachable historical Git objects. The existing
history-preserving capture adapter retains them in the private suite copy.
A retained `sitecustomize.py` sets Python's `os.defpath` to the installed Git
rather than Apple's discovery shim. Exact suite argv/cwd, that environmental
adjustment, actual exit/output and protected outer receipts are retained.
No product/test bytes or historical expectations are patched to obtain a pass.

## Remaining gates

Complete independent source inventory/entailment/ambiguity adjudication,
control-alternative fitness review and task feasibility review. These public
historical solutions are exposed replays, not unseen tasks. Prefer a new cohort,
or explicitly accept that limitation **before** the final live freeze. Reject
source-conflicting expectations rather than assigning candidate defects.

Only then prepare the final live protocol/model/host/tool/budget/arm-order freeze
and obtain explicit bounded spending approval tied to it. Phase 2 receipts are
not that approval. The A-first two-confirmed-failure gate remains unchanged;
all B/C/D cells must remain NOT_EXECUTED if it does not pass. No additional
reviewer, controller, schema, product feature, mandatory gate or merge authority
is introduced.
