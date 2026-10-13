# S6 ISO source acquisition and further UTC readback

12 October 2026. **S6 remains incomplete.** This is independent source readback,
not a completed native verifier qualification or framework/model comparison.
It follows [source-contract calibration](S6-SOURCE-CONTRACTS.md),
[interface qualification](S6-SOURCE-EVIDENCE.md),
[verification redesign](S6-VERIFICATION-REDESIGN.md),
[first follow-up](S6-FOLLOWUP.md), and [historical results](S6-RESULTS.md).
All earlier reports, failed trials and stopped declarations remain unchanged.

## Source availability and independent expectations

The user supplied the [ISO 8601-1:2019 preview](https://cdn.standards.iteh.ai/samples/70907/5e8d00e639cf4f849462bd63062f4cd8/ISO-8601-1-2019.pdf).
It contains 13 PDF pages and ends at printed page 5. Clause 3.1.1.24 directly
permits second 60 for an inserted UTC leap second. The contents list the detailed
date/time grammar in clause 5, on printed pages 19–27; those pages are absent.
The preview therefore confirms the prior counterexample but does not supply a
complete specification for replacement positive controls.

The independently located [2022 amendment](https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf)
contains the replacement text for clause 5.3.1.4: the lowest included hour,
minute or second can have a decimal fraction, with lower components omitted.
Expected conversions follow exact unit arithmetic: half an hour is 30 minutes,
half a minute is 30 seconds. Subsecond truncation follows conversion, preserving
the represented instant to the requested whole-second precision. The actual
end-of-2016 leap second is independently established by
[IERS Bulletin C 52](https://datacenter.iers.org/data/16/bulletinc-052.txt).
The existing public offset semantics determine equivalent local representations.
No expectation is computed using the candidate or Python's ISO parser.

## Frozen native readback

The new single-use audit is `.proofline/s6/iso-clauses-readback-v1/`.
Its manifest SHA-256 is
`d33fee019114eff02b6b1b072a9696a9d351ed0556b8970787059fb6d2fe99df`.
The original source and frozen UTC candidates from source-contract cases 5 and 8
were copied without modifications. Case 5 is the historically accepted defective
candidate; case 8 was formerly declared a positive reference and was already
independently shown defective. Both are negative controls for this readback.
Runtime files, archived copies and expected observations were frozen before
execution. Neither a new positive implementation nor a new task promise was
introduced. The original corpus and its acceptance population remain unchanged.

Nine added inputs cover leap-second identity, positive/negative/non-hour offset
representations of that instant, fractional hours with dot/comma, basic/extended
fractional minutes, and conversion before subsecond truncation. Both candidates
violated all nine expected behaviors through **both** public entry points:
36 reproduced mismatches. Eight existing CLI/version/error observations passed.
The defects are rejection of source-valid inputs, including the formerly positive
reference's fractional-unit narrowing. These are product observations, not new
verifier false acceptances or false rejections.

All 44 native process probes were available, with no timeout. They totaled 5.999
known process seconds; audit wall time was 6.276 seconds. Candidate/input snapshots
and runtime hashes remained intact. Native execution used the existing macOS,
Codex CLI 0.162.1 and Homebrew Python 3.14.8 boundary, read-only inputs, disposable
scratch, and network denial. Host execution initialized the nested sandbox;
isolation was retained.

Zero provider model dispatches occurred; dispatched model tokens are zero for
this audit. Initiating-agent costs, operator attention, source preparation and
dollar cost remain unknown. The user supplied a source link as study-level help;
there were no task-worker deliveries from which to estimate human intervention,
reliability, throughput or cost per independently correct delivery.

## Implementation, validation and decision

`checks/s6_iso_audit.py` reuses the native CLI/library evaluator and preserves
the full process receipts and immutable fixtures in ignored operator evidence.
A focused arithmetic test independently checks fractional-unit expectations;
it passed. Native readback established the candidate defects. Production code
did not change in this step; the prior full native suite's 174 passes and two
platform skips remains its validation. The full suite was not repeated for the
standalone audit addition.

The decision remains **redesign**. Patching only leap seconds would still leave
known source-domain defects. A complete applicable interpretation needs the
remaining base-standard rules, including clauses 4–5, together with the available
amendment, before replacement positive and structurally different UTC controls
can be qualified. The preview must not be represented as the full standard,
and the promise must not be narrowed to Python's parser or the audited examples.
Neither stopped qualification is resumed. All pending model judgments, production
recovery experiments and required matched comparisons remain unexecuted; no new
comparison campaign was declared. Obtaining the complete specification removes
one blocker, but does not guarantee that native trust qualification will pass.

Retained operator evidence includes `manifest.json`, `report.json`, the runtime
archive, native log, CLI/library receipts, resource ledger and hashed evidence
index. Private evaluator artifacts remain ignored and outside worker/verifier
inputs. No push, PR, merge, deployment or purchase occurred.
