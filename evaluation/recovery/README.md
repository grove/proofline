# Issue #34: fresh recovery comparison

This is a six-task, 24-slot native study declaration, separate from #16 and #32.
Preparation and qualification invoke zero models. A live result is required
before claiming recovery or making an evidence-based keep/remove decision.

The corpus contains small, representative **synthetic Python repositories**,
not a random sample of production issues. Five tasks need changes across modules:
configuration overlays, injected HTTP retries, expiring cache actions, atomic
JSON Lines export, and safe ZIP extraction. Column selection is the control.
Each complete request, starting file set, existing test, probe, hidden assertion,
control and runtime identity is frozen before dispatch.

| Arm | Initial implementation | After capture |
| --- | --- | --- |
| A | Luna:high, ordinary self-testing | Independent hidden grading |
| B | Luna:high | Ordinary protected probes; one eligible same-thread Luna correction |
| C | Luna:high | Same probes through optional model-free Proofline; same correction opportunity |
| D | Luna:high | C, with Sol:high diagnosis only for a qualified public assertion defect |

Every initial worker receives the same original task and product bytes, without
the additional probes. Hidden scripts, controls and independent grades are never
feedback. D has no planner and dispatches no Sol on green or unqualified checks.
An advisory diagnosis cannot authorize repair.

**Spending gate:** Execute and independently grade all six A slots first. Fewer
than two defective A candidates stops the study as a correctness ceiling pilot;
all 18 other cells remain `NOT_EXECUTED`. Otherwise execute every remaining cell,
including tasks whose baseline was correct. The six remaining arm orders use all
permutations, balancing each B/C/D arm twice in every position. One repetition,
serial execution, no retries or task selection after observing outcomes.

The exact configurations are `gpt-6-luna:high` and `gpt-6.1-sol:high` on macOS
26.6.2/arm64, Python 3.14.8 and Codex CLI 0.162.1. Every assignment has **1,200
total seconds**, including native isolation, capture, probes, diagnosis,
correction and grading. A may spend up to 1,000 seconds on its ordinary attempt;
B/C/D each get up to 600 initial seconds and the same 180-second correction
limit. D may spend up to 120 seconds on diagnosis within the same total budget.
The maximum is **48 native turns and 28,800 seconds (8 hours)** for primary
assignments; the baseline gate caps an early-stop run at six turns and 7,200
seconds. These are upper bounds, not a dollar quote or predicted run time.

## Reproduce on the frozen host

Run from the Proofline root using the declared Python. Offline tests work in CI:

```sh
/opt/homebrew/bin/python3.14 -B -m unittest tests.test_recovery -v
/opt/homebrew/bin/python3.14 -B -m evaluation.recovery.study prepare
/opt/homebrew/bin/python3.14 -B -m evaluation.recovery.study qualify
```

Native qualification must run from host execution, not inside another sandbox.
It validates fresh worker/reader isolation, all 24 controls, and B/C agreement on
all six correct/defective probe pairs. The previously completed #32 **staged**
same-thread handoff qualifies transport machinery only; it contributes no new
natural recovery observation and spends no new inference.

After explicit user spending approval, store the exact user authorization in
`.proofline/issue34-recovery-v1/approval.json`, with this declaration's
`study_id`, `freeze_sha256`, `max_native_dispatches: 48` and `max_seconds: 28800`.
Prior #32 approvals are rejected. Then:

```sh
/opt/homebrew/bin/python3.14 -B -m evaluation.recovery.study execute
/opt/homebrew/bin/python3.14 -B -m evaluation.recovery.study report
```

The adapter reuses native Codex coding, capture, receipt-bound check and supported
same-thread correction APIs. B calls only the native command protection API; it
does not call Proofline check/feedback or use its eligibility policy. Qualification
checks both mechanisms against identical frozen argv and the same assertion
failure policy. Production correction policy and normal workflows are unchanged.

Every slot is retained. Native failure, unavailable checks/grading, frozen-input
drift, budget exhaustion or an uncertain interrupted dispatch stops the campaign
with an incomplete result; a stopped campaign cannot resume or reuse a slot.
Report initial/final grades separately and retain the exact initial/final trees,
receipts, public coverage gaps, false acceptances/blocks and failed attempts.

## Interpretation and accounting

A–B measures the probe/feedback/repair package. B–C measures the delivery mechanism
given the same probes. C–D measures conditionally invoked Sol, with the same single
repair opportunity. All contrasts are conditional on the predeclared baseline
gate and six fixed tasks. Paired delivery changes and exact sign tests are
descriptive; this small sample does not establish population reliability.

Literal hidden expectations and public assertions were derived from original
requests before any live candidate. Per task, correct and algorithmically
alternative controls must pass both; a public-probe defect must fail both; a
coverage-gap defect must pass public probes and fail hidden grading. **All 24
controls pass the original repository tests.** Oracle authorship is single-agent;
alternatives share some validation. This is independent execution against a
finite oracle, not independent human replication or exhaustive correctness.

Full assignment elapsed time includes all native checking/grading overhead.
Report preparation and native probe qualification separately, so probes are not
treated as free. Report each model's input, cached input, output, uncached input,
native turns, tools and seconds. Resumed-thread usage is differenced from
cumulative session totals; cached input is a subset of input, never added again.
Observed billing, authoring tokens/dollars and active human time remain unknown
unless independently observable. No price assumption is an observed charge.

PR publication is authorized by the implementation request; merging is not.
