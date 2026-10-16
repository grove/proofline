# [P2][Deferred] Reconcile externally measured provider billing with existing usage records

## Status: narrow remaining work after 0.8 provider-accounting implementation

Lore 0.8 implemented nullable provider attempt/token accounting, retry and error events, privacy-filtered opt-in ledgers, SQLite schema 8, and evaluator capture/aggregation. See [provider usage documentation](https://github.com/grove/lore/blob/main/docs/PROVIDER_USAGE.md), [0.8 implementation tracker](https://github.com/grove/lore/blob/main/docs/IMPLEMENTATION_TRACKER.md), and [0.9 scorecard](https://github.com/grove/lore/blob/main/evaluation/PRODUCT_QUALITY_09.md).

That closes the **provider-usage instrumentation** portion of this original issue. It **does not** establish actual invoices or a verified paid-model benchmark. Keep this issue open, narrowed to **externally measured billed-cost reconciliation**, deferred until the focused product and real-model study need it.

## Remaining scope

- [ ] Specify a caller-supplied, source-attributed **actual billed USD** receipt for a particular invocation/run (not token-price guesswork).
- [ ] Validate run identity, source, accounting interval, currency/amount and provenance; reject incompatible, overlapping or forged-looking data as unverified.
- [ ] Reconcile external billing with attempt-level provider usage while retaining unknowns where billing is not available.
- [ ] Present provider-reported tokens, measured billed cost and unknowns as different fields in the evaluator, with tests for null usage, retries, cached runs, refusals, and partial billing.
- [ ] Avoid storing prompts, source content, raw provider errors, credentials or secrets in ledgers.

## Non-goals / sequencing

Do **not** convert model tokens to invented paid amounts, assume zero cost for local/uncaptured use, add provider-specific price tables, or reopen working provider-usage accounting. This is a **P2 deferred cost-evidence follow-up** until [#65](https://github.com/grove/lore/issues/65) and simplification are stable; coordinate with [#2](https://github.com/grove/lore/issues/2).

### Original coverage acknowledged

The earlier issue also called for structured usage attempts, OpenAI/Ollama response mappings, failure/retry retention, privacy protection, offline tests and evaluator accounting; those are already covered by the 0.8 work.
