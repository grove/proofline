# Four-request shortlist — independent review is still required

**NOT QUALIFIED.** [candidate-cohort.json](candidate-cohort.json) pins four
requests and their exact starting commits/trees. All four are selected for
preparation only. No source inventory below has been approved by a separate
qualified reviewer; no live freeze or coding assignment exists. The complete
issue title/body and discussion are captured together, with the original API
response alongside each Markdown capture. Preserve these bytes, including CRLF.

The bounded search checked Grove's available issue trackers and eleven public
Python projects. Many plausible bugs already had working patches in PRs or
issue comments. In particular, an open issue and an empty upstream PR list do
not establish novelty: jsonschema's interaction limits led contributors to
publish solutions in forks instead. The search evidence and exclusions are
retained with the preparation results. Absolute novelty/training exposure is
UNKNOWN. Do not include evaluator patches, expectations, this checkout, or
search results in worker inputs.

## Click #3362: preserve hyphenated usage tokens

Source: [complete request](replacement-sources/click-usage-hyphens.md),
[upstream](https://github.com/pallets/click/issues/3362).
Base: `2247b35ea1c47c727d7a06e51fa280e12a863ff6`, tree
`6b26180d3cc76de6213a1e998f1eaf821e7f0f3f`.

Draft material obligations:

- The supplied `HelpFormatter(width=65).write_usage` example preserves each
  hyphenated option and its order across wrapping. An alternative layout is
  acceptable; copying exact spaces or line breaks is not a grading requirement.
- The issue explicitly includes default width, direct formatter users, and
  arguments with custom hyphenated metavars. Check both prefix/layout branches
  with tokens that fit the available continuation width.
- Preserve the existing formatter, prefix/indentation and empty-argument
  behavior, public CLI operation, and visible-width/ANSI handling documented in
  the pinned implementation. A failing-before-fix regression is proposed
  verification evidence, not an additional product feature required by this issue.

Draft executable evidence: `fresh_oracles.py:usage_tokens`, the exact control
patches in `fresh-controls/`, and the unchanged original default Click suite.
The controls use either the existing wrapper with a usage-specific setting or
a local wrapper in `write_usage`; neither implementation structure is required.
The defect repairs the first layout only. The suite remains green while the
withheld probe detects splitting in the other layout.

Reviewer decisions: when a single token cannot fit even on a fresh continuation
line, this request does not specify whether exceeding the width or splitting is
preferred. The first draft wrongly conflated that case with avoidable hyphen
splitting; that expectation was rejected, and its failed positive controls are
retained. Assess ANSI, indentation, long-token policy and regression-test
coverage independently. Current probes alone do not cover the whole request.
The upstream discussion restricts autonomous issue/PR publication; this is a
local experiment, with no upstream contribution or contact authorized.

## Click #2992: expose contextual usage in information dictionaries

Source: [complete request](replacement-sources/click-usage-metadata.md),
[upstream](https://github.com/pallets/click/issues/2992). Same Click base/tree.

Draft material obligations:

- Make usage available to documentation generators through the existing
  information-dictionary traversal, derived from the actual contextual
  `get_usage()` result rather than a fixed program name or copied docstring.
- Cover a command, nested groups and leaf commands: the request's workaround
  traverses two levels and preserves their parent command paths.
- Keep existing parameter/help metadata and ordinary parsing/help behavior;
  inspection should remain serializable and should not execute callbacks.
  Document the new field and update source-conflicting exact-shape tests.

`fresh_oracles.py:usage_metadata` is an **unvalidated draft**, not a qualified
grader. It admits either the full `Usage:` heading or the stripped text used in
the issue workaround. No positive/negative controls were executed for it.

Reviewer decisions: the request calls the API `get_info_dict`, while current
Click exposes `to_info_dict`; settle the supported entry points and field
location before freeze. Do not reject a correct alternative merely for placing
the root usage at context rather than command level. The existing
`tests/test_info_dict.py` compares exact dictionaries; adding the requested
field can legitimately require those expectations to change. An unchanged
original suite failure here is not automatically a candidate defect. Assess
aliases, hidden/dynamic commands, custom usage and side effects from current
API behavior; do not invent new requirements from the preferred control design.

## Arrow #1287: document all accepted shift keywords (small control)

Source: [complete request](replacement-sources/arrow-shift-docs.md),
[upstream](https://github.com/arrow-py/arrow/issues/1287).
Base: `2224255c4acc594d734cef0bbc83360452a67983`, tree
`1ec889cbad20c2ede0242e5c662b8af9c1973f30`.

Draft material obligations:

- Put the complete accepted keyword list in user-facing shift documentation,
  so a user need not inspect source. The pinned implementation accepts years,
  months, days, hours, minutes, seconds, microseconds, weeks, quarters and
  weekday, plus the explicit `check_imaginary` parameter.
- Explain relative shifting and weekday behavior accurately; retain existing
  examples and do not advertise singular absolute replacement arguments as
  accepted shift keywords. Preserve runtime behavior and installation.

A docstring rendered by the existing API guide or an accessible guide section
can both be correct. No specific prose, headings, ordering or new test is
required. A separate reviewer must inspect the rendered result and execute any
added examples against the actual candidate. Merely counting keyword strings
would falsely accept unrelated or misleading text. A deliberately incomplete
list (for example omitting quarters/weekday) is a proposed negative control,
**not an independently rejected candidate**. The 1,902 passing original tests
establish dependency health, not documentation completeness. Docs build and
genuine alternative/negative documentation controls remain NOT_EXECUTED.

This is the task where extra process is expected to be unnecessary.

## Arrow #1293: choose a timezone fallback without overwriting explicit zones

Source: [complete request](replacement-sources/arrow-default-timezone.md),
[upstream](https://github.com/arrow-py/arrow/issues/1293). Same Arrow base/tree.

Draft material obligations:

- Provide a documented way to use a chosen fallback timezone for a string
  without a timezone, while preserving a timezone explicitly supplied in that
  string. Explicit UTC must be distinguishable from an unspecified timezone.
- Exercise the original `2025-01-01 00:00-0800`, naive datetime string, and
  `+0000` examples, plus `Z`, positive/fractional offsets and date boundaries.
  Compare instants and offsets, not timezone-object identity.
- Preserve the current `tzinfo=` replacement semantics for existing callers;
  this is a new means of supplying a default, not authority to silently change
  the documented override. Keep malformed-input errors, supported input forms,
  public exports, type declarations and installation coherent with the chosen API.

Reviewer decisions: neither the new API name nor precedence when old override
and new fallback are both supplied is specified. Neither is applicability to
non-string input forms. Accept materially different documented correct APIs;
do not hard-code a new keyword into a hidden grader and then fail alternatives.
Review the full factory/parser behavior before deciding which compatibility
cases are material. Independent executable checks and complete edited-repo
reference/alternative/defective controls are **NOT AUTHORED** pending that
adjudication. This is a bounded implementation candidate, not a qualified task.

## What must happen before freeze

A separate qualified reviewer must independently inventory the complete sources,
adjudicate the decisions above, and assess all controls and genuinely different
correct implementations. Preparation-author notes are not that review. Complete
the remaining three task graders/controls, docs build, and native dependency
exposure checks using the existing snapshot/protected-command machinery.
Reject any task whose obligations or dependencies cannot be qualified; do not
force four by dropping part of a request. The Exmeso tasks stay in the earlier
screen with their original identities and retained build stops.

Reuse `protocol.json` unchanged: A/B/C/D, the same proposed Luna:medium,
permissions and 1,500-second total episode budget, including checklist,
Intentline export, selected checks and repairs inside the agent allowance.
All A tasks precede conditional B/C/D. Fewer than two independently confirmed
material A failures means stop, with every B/C/D slot NOT_EXECUTED. A constructed
defective control is not an ordinary baseline failure. Freeze fresh task/order,
oracle/adapter/control/source hashes, exact host/catalog/runtime/dependencies,
permissions and caps only after qualification. Obtain separate explicit live
authorization tied to those exact bytes; no inference to "test access" now.

Record complete independently satisfactory deliveries, missing/wrong promises,
false acceptances, false blocking, observed selected checks/hints, repairs,
non-overlapping elapsed time and all reported token categories. Include setup,
export, checking and repair overhead; cached input is a subset of input.
Unobserved tokens, human effort and billed costs stay UNKNOWN. Keep all slots
and unavailable/disputed results. No product or mandatory workflow adjustment
is supported by preparation evidence.
