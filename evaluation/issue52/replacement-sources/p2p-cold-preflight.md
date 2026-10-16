# Reduce cold-start preflight model overhead without weakening isolation

## Outcome

On the currently supported macOS/Codex host, reduce the **actual elapsed/model cost** of cold `deliver-issue` admission while establishing the same trusted execution isolation and task readiness. Today a newly admitted delivery normally launches **two separate real Codex preflight contexts** before implementation; completed #60 already supplies reusable admission facts, so do not rebuild admission.

## Scope

Start with the live timings and observations in #109 (or a small equivalent matched real-host probe). Identify which preflight decisions are mechanical host/OS properties and which genuinely require a restricted worker's observed capability. Test the smallest safe options: trusted deterministic boundary probes controlled by P2P, one verified restricted invocation rather than two if independently justified, or narrowly applicable reuse of existing #60 host-capability evidence. **None is preapproved.** If the second independent host identity is necessary to demonstrate fresh verifier capability, preserve it.

Retain actual checks that protected contract/base/candidate/binding inputs cannot be written through direct paths, symlinks, and subprocesses; scratch is writable; effect/network restrictions hold; independent verifier sessions are distinguishable; task-dependent tools/services are actually available from the correct boundary. A host declaration or prior machine's check is not enforcement evidence.

Use the existing admission/capability receipt representation and #59 measurements. A checkpoint restore on another machine, material host/policy change, unknown provenance, or changed required service access must refresh the corresponding facts. Do not silently reuse an old or unrelated sandbox claim.

## Acceptance

1. Matched live current-host cold-delivery comparison records preflight dispatches, elapsed time and tokens, then the changed implementation's same metrics; distinguish unavailable token data.
2. Deliberate protected-write, symlink, subprocess, scratch, network/effect and session-provenance probes still prove or conservatively block the required boundaries.
3. Representative missing service/tool, material host-configuration drift, fresh-machine restore, stale/tampered evidence, interrupted dispatch and unchanged-reuse cases preserve the present admission semantics.
4. Independent review and proof still receive distinct fresh sessions on the exact unchanged contract/candidate; source work and external authority remain protected.
5. Demonstrate a **meaningful measured reduction in live model work or elapsed time**; if no safe reduction is supported, document that result and close without adopting a weaker shortcut.

## Boundaries

Do not add an admission UI, extra model stage, universal cache, second host, new schema or generic adapter. #62–#64 are independent portability work. No production adoption from offline timing or synthetic sandbox checks alone. Prerequisite: #109 live observations or an explicitly documented equivalent, not #52.
