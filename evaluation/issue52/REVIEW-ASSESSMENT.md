# Assessment of the 16 historical source/oracle questions

This is a preparation-author assessment, **not independent semantic review**.
All 16 original questions in `source-review-packet.json` remain unapproved.
None establishes a naturally occurring worker failure or a product defect.
Current product regressions and generic native controls cannot retroactively
establish complete correctness of a historical task-specific candidate.

| Question | Evidence available now | Decision still needed |
| --- | --- | --- |
| F1 managed run output | `proofline.py` routes run/check results through shared feedback formatting; `tests/test_local_run.py` supplies simulated runs | A real managed-run task-specific record is not observed here; do not dispatch a model for this preparation |
| F2 frozen identities | Supported native round trip retains actual candidate commit/tree, source/export hashes and selected argv | Assess binding on the historical #14 subject candidate; placeholder helper tests alone are insufficient |
| F3 status re-read | New public `status --show-source` readback succeeds on the intact native check; `test_feedback.py` covers missing/tampered receipts | Native tamper/readback on the historical #14 candidate is still absent |
| F4 linked failures | `feedback_annotations` and `test_promise_evidence.py` cover R/command-link conflicts and actual failure annotations | Verify the complete native R-linked failure path on the subject implementation; no model or Intentline requirement should be invented |
| M1 complete source | CLI has hash-checked `--show-source`; fresh native readback includes the complete source | Assess task-specific preservation/display without requiring it in every concise default handoff |
| M2 same-agent proposals | `test_unverified_review_can_propose_omitted_clauses_without_certifying` exercises the optional data; no worker was run | A worker declining this optional step is not automatically incorrect; actual proposal usefulness is unmeasured |
| M3 green Unicode omission | Phase 2 `SOURCE` explicitly says `Accept Unicode names`; `mapping_outcomes` leaves that row unlinked. Its defective control falsely promotes the row while 109 original tests pass. Current `test_green_suite_does_not_convert_unlinked_unicode_into_coverage` is additional evidence | The earlier question overstates the mismatch: this is an unlinked-Unicode reporting control. It still is not a naturally occurring Unicode coding failure or whole-request oracle; adjudicate adequacy independently |
| M4 forged/stale readback | `mapping_validation`, `test_frozen_mapping_readback_detects_tampering_or_removed_inputs`, and native role canaries cover separate components | Full native task-specific mutation/candidate-swap coverage remains incomplete |
| I1 valid unsupported lineage | Current `test_revision_successor_context_and_origin_traversal_are_rejected` changes revisions and rehashes source/context data via `changed()` | These are useful existing tests, not all present in Phase 2's finite adapter probes; independently decide supported/unsupported boundaries rather than exact error spelling |
| I2 forged authority | Current `test_operator_assertions_remain_unverified_and_other_approval_claims_refused` tests operator assertions and fabricated approval | No hashes or labels authenticate external consent; assess all imported paths and authority effects on the historical candidate |
| I3 gaps/candidate/paths | Current adapter tests cover lost gap reasons and malicious paths/symlinks; promise readback tests cover candidate changes | The combined task-specific public CLI/native path is not fully exercised by those separate helpers |
| I4 actual round trip | A fresh supported-binary producer/export/import/check/readback works with exact candidate/source identities | It uses the existing #16 fixture, not independent whole-task qualification of #23 |
| H1 bounded/full detail | `test_output_limits_rows_and_untrusted_multiline_text` uses 64 rows, limits the summary to 3 and retains full structured content | Source says “e.g. top 3”; do not require that exact number if another concise output meets the request. Assess persisted full-report behavior |
| H2 persisted guidance | Fresh native public CLI readback shows NOT DEMONSTRATED, source links, unverified plan text and coverage UNKNOWN; existing mapping readback tests detect mutations | Historical task-specific native tamper/readback remains pending |
| H3 public flag compatibility | Existing `test_cli_inputs.py`, `test_supported_cli.py`, `test_intentline_advisory.py`; fresh producer/check/status path | The subject-candidate flags matrix is not fully observed. Unit acceptance and source-citation matches are not whole-source proof |
| H4 documented example | Current `README.md` “Optional next-check workflow” includes the lockout before/after and agent next action | Separate reviewer must judge source fidelity and usability. No delivery benefit follows from documentation existing |

The smallest useful next step for the historical packet is reviewer adjudication,
not sixteen new mandatory stages or a second AI reviewer. Retain these cases as
mechanical controls. Prefer the new source-pinned shortlist for any future live
cohort, after its own complete oracle/control review. No reviewer name,
attestation, independent grade or approval is manufactured by this assessment.
