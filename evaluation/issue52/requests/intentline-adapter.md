# [vNext integration] Optional Intentline acceptance-to-evidence adapter

## Why
Intentline already expresses source-grounded requirements (`R1` etc.), exact original source references, boundaries, expected oracles, proposed evidence, explicit gaps and versioned identities. Proofline should reuse that **optionally**, not invent a second planner or resurrect historical `deliver`/`inspect-intentline` controllers.

## Small scope
Implement one **read-only, explicitly opted-in adapter** that converts a supported Intentline export into the generic promise/evidence input defined by [#13](https://github.com/grove/proofline/issues/13). Start with **a single original-request acceptance schema 1 export** (e.g. `export --format json` with its complete `export-manifest.json`, `contract.json`, source manifest and original source capture). If amended/lineage/native bundles cannot be validated fully, **reject with an exact unsupported-format explanation**; never flatten them to a misleading single request. Future expansion needs evidence of value.

## Acceptance criteria
- [ ] The existing `proofline.py check` still works unchanged with only the original request and selected check argv. No Intentline install, account, extra config, planning skill, model invocation or second approval is required.
- [ ] On explicit opt-in only, read supported Intentline export **as untrusted data**. Validate the completion marker, every imported byte hash, contract/source revision identity and original request's exact bytes against the Proofline request. Reject mismatch, stale/partial/missing data, ambiguous source/adoption claims and unsupported successor formats; no executable exported scripts.
- [ ] Project source citations, `R` IDs, requirement statements, boundaries, intended oracles and `planned_evidence`/evidence-gaps carry through into the generic #13 display **as proposed expectations**, not executable proof or accepted authority.
- [ ] Distinguish `draft/advisory`, `operator-asserted but unverified` and caller-provided external approval; Intentline metadata/hashes/labels **never authenticate user consent** or grant editing, PR, merge, deployment or model/compute effects.
- [ ] Link only explicitly selected executable check receipts to the *exact frozen candidate* and imported requirement IDs. Unlinked obligations are reported **NOT DEMONSTRATED**; green commands don't establish that the requirements inventory is exhaustive.
- [ ] Test reference export, real round-trip on source and candidate, optional absence, corrupted manifest, forged source quote, unsupported successor, swapped/changed contract, lost evidence gaps, wrong candidate, and malicious paths/symlinks. Preserve old check/run/status semantics and bounded sandbox checks.
- [ ] Document one short optional workflow; no new general adapter registry, model review/prover, implicit export, peer runtime invocation, or additional mandatory steps.

## Dependencies
- [#13](https://github.com/grove/proofline/issues/13) provides generic source-linked evidence/gap mapping first.
- Coordinate the existing producer format and stale-handoff cleanup with **[Intentline #36](https://github.com/grove/intentline/issues/36)**. Do not block direct Proofline checks while that work is incomplete.
- [#16](https://github.com/grove/proofline/issues/16) independently tests whether this optional path actually improves delivery enough to justify its latency and tokens.

## Non-goals
No automatic plan creation, retrospective promise certification, compulsory Intentline, full native historical delivery adoption, PR/merge, or another workflow controller. Preserve complete original source as authority.
