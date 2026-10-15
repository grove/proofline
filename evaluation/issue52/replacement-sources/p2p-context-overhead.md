# Cut repeated agent instruction and handoff cost on the critical path

## Outcome

Reduce agent time and tokens spent reading **P2P's own extensive rules, repetitive handoffs and reports**, without reducing the accepted promises, fresh independence of review/proof, material test coverage or retained evidence.

The current acceptance protocol exceeds 100 KB, and delivery/implementation/review/proof skills contain substantial instructions. Each model stage reads its skill and referenced protocol; there is no current live evidence for how much of the elapsed time or provider input tokens this accounts for. #57 explicitly deferred compact prompts pending paired real-model evidence. Do **not** assume smaller prompts are automatically safer or faster.

## Narrow experiment

Use #109 observations or a small matched real-host benchmark to compare exact current stages with one **canonical, stage-specific instruction delivery** approach. Trace the actual instruction bytes/tokens each worker consumes, accounting for host caching and any separately loaded material. Favor a deterministic selection of relevant canonical sections and a compact stable stage entry over manually maintained abbreviated copies of rules. The full authoritative rules must remain accessible when needed, pinned by exact identity through #85 upgrades and #82 portable checkpoints.

Consider whether repetitive report prose can be replaced by controller-rendered explanation from the existing validated structured records **without weakening fields needed for full review/proof, command evidence, recovery or external receipts**. Do not introduce a new artifact schema to save a few sentences.

## Acceptance

1. Capture a reproducible baseline of real stage input tokens, model elapsed time, and observed stage outcomes for at least one passing and one materially defective or repaired case; treat unsupported host usage as unknown.
2. A paired run demonstrates whether the smaller canonical context reduces **actual input tokens and/or end-to-end time**, including costs of dynamic assembly/caching and any follow-up reads.
3. Verify complete agreement/requirement coverage, applicable safety/authority rules, distinct stage sessions, fresh exact-candidate reviewer/prover reports, evidence quality, and successful repair/restore/instruction-upgrade paths. Run relevant #72/#40 live judgment controls, not only instruction-shape unit tests.
4. Unknown material rule dependencies conservatively load the full authoritative context. Missing selected material, changed provenance or incompatible instruction versions block/reconcile, never silently waive a rule.
5. Deliver the smallest supported improvement with measured savings, **or** document the negative result and retain current instructions.

## Boundaries

No agent-generated summary may become an alternative authority; no mandatory summarizer, second protocol, separate prompt cache, public plugin SDK, or relaxation of PROVEN/REVIEWED. This work owns **instruction/context cost**, not #109's profiling, the cold preflight design issue, or #52's broader comparison with simpler workflows.
