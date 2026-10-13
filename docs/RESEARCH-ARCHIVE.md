# Historical Proofline research archive

The S0–S6 exploratory implementation, designs, tests and evaluation scripts
were removed from the **active branch** to keep Proofline vNext small.
They are **unchanged in the ancestor Git commit**:

- [Full frozen repository at e46814efce7e](https://github.com/grove/proofline/tree/e46814efce7e2b59adecb4583be60806012b1707)
- [Original DESIGN.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/DESIGN.md)
- [Original IMPLEMENTATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/IMPLEMENTATION.md)
- [Original experimental proofline.py (deliver/resume)](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/proofline.py)
- [All historical experiment scripts](https://github.com/grove/proofline/tree/e46814efce7e2b59adecb4583be60806012b1707/checks)
- [All historical experiment tests and fixtures](https://github.com/grove/proofline/tree/e46814efce7e2b59adecb4583be60806012b1707/tests)

## Historical reports

- [S0-CODEX-RUNNER.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S0-CODEX-RUNNER.md)
- [S0-HOST-FEASIBILITY.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S0-HOST-FEASIBILITY.md)
- [S1-DIRECT-DELIVERY.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S1-DIRECT-DELIVERY.md)
- [S2-CONTRACT-INPUT.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S2-CONTRACT-INPUT.md)
- [S2-LIVE-EVIDENCE.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S2-LIVE-EVIDENCE.md)
- [S3-COMPARISON.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S3-COMPARISON.md)
- [S4-RECOVERY.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S4-RECOVERY.md)
- [S5-PUBLICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S5-PUBLICATION.md)
- [S6-AMBIGUITY-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-AMBIGUITY-QUALIFICATION.md)
- [S6-FOLLOWUP.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-FOLLOWUP.md)
- [S6-FULL-TIMESTAMP-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-FULL-TIMESTAMP-QUALIFICATION.md)
- [S6-ISO-READBACK.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-ISO-READBACK.md)
- [S6-ORDERING-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-ORDERING-QUALIFICATION.md)
- [S6-PILOT.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-PILOT.md)
- [S6-REPRESENTATION-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-REPRESENTATION-QUALIFICATION.md)
- [S6-RESULTS.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-RESULTS.md)
- [S6-SCALAR-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-SCALAR-QUALIFICATION.md)
- [S6-SOURCE-BASIS.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-SOURCE-BASIS.md)
- [S6-SOURCE-CONTRACTS.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-SOURCE-CONTRACTS.md)
- [S6-SOURCE-EVIDENCE.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-SOURCE-EVIDENCE.md)
- [S6-TEXT-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-TEXT-QUALIFICATION.md)
- [S6-UTC-QUALIFICATION.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-UTC-QUALIFICATION.md)
- [S6-VERIFICATION-REDESIGN.md](https://github.com/grove/proofline/blob/e46814efce7e2b59adecb4583be60806012b1707/docs/S6-VERIFICATION-REDESIGN.md)

The [S6 decision](S6-DECISION.md) and [bounded comparison](BOUNDED-COMPARISON.md)
are still present in the active tree. The initial and follow-up full
comparisons were **incomplete**, and no general delivery superiority was
established. The original historical files are preserved byte-for-byte
in Git; removing them from the active branch does not revise their verdicts.

**Limit:** Private raw records previously written in ignored local
`.proofline/` directories were never included in the Git repository.
This index preserves the committed reports and code, not local-only
private artifacts that were not published.

Retired external authorization, S2 contract/Intentline, S3–S6
benchmarking, automatic reviewer/prover and publication machinery are
**not supported runtime commands**. Reintroducing them requires a
separate, justified design and independent qualification.
