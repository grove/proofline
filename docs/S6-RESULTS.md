# S6 — Measured results

Final population: **TRUST GATE FAILED**. Decision: **STRENGTHEN VERIFICATION BEFORE EXPANDING: independently observed false acceptance**.

Of 120 assigned cases, 69 executed and 51 remain unexecuted under the trust stop. Outcomes: `{"ACCEPTED CORRECTLY": 42, "BUDGET EXHAUSTED": 15, "FAILED": 7, "FALSE ACCEPTED": 5, "NOT EXECUTED": 51}`. Unexecuted cases remain in the assigned denominator; this is not a completed efficacy comparison.

These are actual local native runs, not illustrative benchmark figures. All methods were judged against the original source. Finite probes establish observed correctness; they cannot prove absence of every defect.

## Results across 20 tasks

| Model / approach | Correct deliveries | False acceptances | Terminal false blocking | Median successful seconds | All-attempt seconds / correct | Correct / workflow hour | All-attempt tokens / correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| sol/ordinary-agent | 8/20 | 2 | 0 | 150.9 | unknown | unknown | unknown |
| sol/agent-plus-review | 7/20 | 0 | 0 | 218.7 | unknown | unknown | unknown |
| sol/p2p | 0/20 | 0 | 0 | unknown | unknown | unknown | unknown |
| sol/proofline | 8/20 | 0 | 0 | 465.5 | unknown | unknown | unknown |
| luna/ordinary-agent | 9/20 | 2 | 0 | 105.3 | unknown | unknown | unknown |
| luna/proofline | 10/20 | 1 | 0 | 296.8 | unknown | unknown | unknown |

Costs per successful delivery charge failed attempts to the denominator. A workflow hour sums elapsed episodes; it is not parallel wall time. Cached input is already included in input tokens. Dollar rates were not declared, so correct deliveries per dollar and dollar costs are **unknown**. Internal provider request counts and unreported tool charges are unavailable.

All automatic task episodes record zero task-specific human interventions. Corpus authoring, protocol repair and operator attention were not timed; study autonomy and full human cost remain unknown. Shared-plan authoring cost is also unknown.

## Provenance and protocol amendments

- Final declaration SHA-256: `f480bc60d57b490285b707506d7a8f074a6284bc780b3299be04a6c9fccc44f4`.
- Exact coding models/settings: `{"luna": {"model": "gpt-6-luna", "model_reasoning_effort": "high"}, "sol": {"model": "gpt-6.1-sol", "model_reasoning_effort": "high"}}`.
- Twenty component tasks, ten raw requests and ten shared plans per arm; eight tasks designated held-out before tuning. One host and one repetition. Only the local delivery target was authorized.
- Forty-six independent controls passed before task dispatch. Candidate tests never supplied the answer key. Those finite probes did not establish complete source coverage.
- Protocol amendments and retained prior results are recorded in the frozen study amendment. Superseded trials are included below; valid observations are carried by exact artifact hash.
- Uniform regression readback preserves original scores. Final false acceptances: 5, including 1 by Proofline. Post-declaration evaluator changes limit causal inference.
- Raw receipts, rejected candidates, frozen runtimes, original scores, superseded trials and unexecuted assignments remain in the private evidence directory. No remote effects were performed.

## Entire study resource ledger

Original episodes across retained and superseded campaigns: **112**. Carried copies are counted once. Known native stage dispatches: **224**; unknown-usage dispatches: **31**.

Known summed workflow seconds: **30408.2**. Token categories: `{"cached_input_tokens": 19181440, "input_tokens": 23974475, "output_tokens": 751212}`. Preparation, oracle controls, readback and controlled diagnostics are separate from this task-episode subtotal; human study time and dollar cost remain unknown.

Known episode observation seconds, including each worker's independent acceptance evaluation: **30574.0**; episodes with unavailable observation time: **0**. Known evaluator setup seconds across campaigns: **237.3**. Stopped coordinator wall totals are unavailable; they are not replaced with zero.

### Qualified executed subtotals

These are consumed resources through the trust stop, including failures. Ratios describe executed cases only, not complete-population efficiency. Unknown usage means token totals are lower bounds. Methods have different task subsets executed; these ratios cannot establish superiority.

| Model / approach | Executed / assigned | Known workflow seconds | Executed seconds / correct | Executed correct / hour | Native dispatches | Known input tokens | Known output tokens | Unknown usage dispatches | Correct but undelivered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sol/ordinary-agent | 10/20 | 1561.9 | 195.2 | 18.4 | 10 | 804151 | 35092 | 0 | 0 |
| sol/agent-plus-review | 11/20 | 2570.7 | 367.2 | 9.8 | 21 | 1426916 | 52988 | 2 | 1 |
| sol/p2p | 12/20 | 6953.1 | unknown | 0.0 | 41 | 3998349 | 117423 | 12 | 8 |
| sol/proofline | 13/20 | 6102.4 | 762.8 | 4.7 | 38 | 3288966 | 112968 | 7 | 4 |
| luna/ordinary-agent | 11/20 | 1201.2 | 133.5 | 27.0 | 11 | 1248275 | 44023 | 0 | 0 |
| luna/proofline | 12/20 | 3854.9 | 385.5 | 9.3 | 47 | 8512025 | 236050 | 0 | 0 |

Supplemental regression readback seconds: 18.0. ISO ordinal-date interpretation: [NASA's ISO-8601 notation reference](https://science.data.nasa.gov/fits/documentation/iso-time). The requirement said ISO-8601, without narrowing it to calendar-date syntax.

Recoverable negative Proofline judgments independently scored: **6**; observed false rejections: **0**; unscored structured negative judgments: **0**. Unfinished verifier invocations are unavailable judgments, not confirmed true or false rejections.

## Controlled recovery diagnostics

Host fault injections are excluded from natural task reliability rates.

| Case | Result | Matched declared control | Implementations | Proofs |
|---|---|---|---:|---:|
| third-implementation | LOCAL ACCEPTED | True | 3 | 1 |
| weak-evidence | LOCAL ACCEPTED | True | 1 | 2 |
| valid-alternative | LOCAL ACCEPTED | True | 1 | 1 |

Diagnostic wall seconds: 1681.2; native dispatches: 15; known tokens: `{"cached_input_tokens": 1504640, "input_tokens": 1808278, "output_tokens": 49848}`; unknown usage dispatches: 1.

## Paired complete ledger and input-specific hypotheses

# S6 measured pilot

Status: TRUST GATE FAILED. STRENGTHEN VERIFICATION BEFORE EXPANDING: independently observed false acceptance.

These are measured outcomes only where native runs and private observations exist. Unknown costs are not zero. Failed and unexecuted assignments remain in the denominator.

| Model / input / approach | Correct / assigned | False accepted | False blocked | Seconds per correct delivery | Tokens per correct delivery | USD per correct delivery |
|---|---:|---:|---:|---:|---:|---:|
| sol/raw-request/proofline | 5/10 | 0 | 0 | unknown | unknown | unknown |
| sol/raw-request/ordinary-agent | 4/10 | 1 | 0 | unknown | unknown | unknown |
| luna/raw-request/ordinary-agent | 5/10 | 1 | 0 | unknown | unknown | unknown |
| luna/raw-request/proofline | 5/10 | 0 | 0 | unknown | unknown | unknown |
| sol/raw-request/p2p | 0/10 | 0 | 0 | unknown | unknown | unknown |
| sol/raw-request/agent-plus-review | 3/10 | 0 | 0 | unknown | unknown | unknown |
| luna/shared-preplanned/proofline | 5/10 | 1 | 0 | unknown | unknown | unknown |
| sol/shared-preplanned/ordinary-agent | 4/10 | 1 | 0 | unknown | unknown | unknown |
| sol/shared-preplanned/agent-plus-review | 4/10 | 0 | 0 | unknown | unknown | unknown |
| sol/shared-preplanned/p2p | 0/10 | 0 | 0 | unknown | unknown | unknown |
| luna/shared-preplanned/ordinary-agent | 4/10 | 1 | 0 | unknown | unknown | unknown |
| sol/shared-preplanned/proofline | 3/10 | 0 | 0 | unknown | unknown | unknown |

| Task | Model | Input | Approach | Outcome | End-to-end seconds |
|---|---|---|---|---|---:|
| unicode-usernames | sol | raw-request | proofline | ACCEPTED CORRECTLY | 494.860 |
| unicode-usernames | sol | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 76.684 |
| unicode-usernames | luna | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 69.944 |
| unicode-usernames | luna | raw-request | proofline | ACCEPTED CORRECTLY | 292.888 |
| unicode-usernames | sol | raw-request | p2p | BUDGET EXHAUSTED | 680.222 |
| unicode-usernames | sol | raw-request | agent-plus-review | ACCEPTED CORRECTLY | 195.342 |
| stable-pagination | luna | shared-preplanned | proofline | ACCEPTED CORRECTLY | 235.511 |
| stable-pagination | sol | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 105.493 |
| stable-pagination | sol | shared-preplanned | agent-plus-review | ACCEPTED CORRECTLY | 218.727 |
| stable-pagination | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 492.819 |
| stable-pagination | luna | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 112.396 |
| stable-pagination | sol | shared-preplanned | proofline | BUDGET EXHAUSTED | 900.146 |
| quoted-csv | sol | raw-request | agent-plus-review | FAILED | 244.438 |
| quoted-csv | luna | raw-request | proofline | FAILED | 153.510 |
| quoted-csv | sol | raw-request | ordinary-agent | FALSE ACCEPTED | 158.759 |
| quoted-csv | luna | raw-request | ordinary-agent | FALSE ACCEPTED | 94.397 |
| quoted-csv | sol | raw-request | p2p | BUDGET EXHAUSTED | 687.109 |
| quoted-csv | sol | raw-request | proofline | BUDGET EXHAUSTED | 900.153 |
| decimal-invoices | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 491.459 |
| decimal-invoices | sol | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 194.418 |
| decimal-invoices | sol | shared-preplanned | proofline | ACCEPTED CORRECTLY | 732.094 |
| decimal-invoices | luna | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 80.637 |
| decimal-invoices | luna | shared-preplanned | proofline | ACCEPTED CORRECTLY | 349.852 |
| decimal-invoices | sol | shared-preplanned | agent-plus-review | ACCEPTED CORRECTLY | 360.492 |
| merge-settings | sol | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 151.878 |
| merge-settings | luna | raw-request | proofline | ACCEPTED CORRECTLY | 395.696 |
| merge-settings | sol | raw-request | agent-plus-review | FAILED | 66.524 |
| merge-settings | sol | raw-request | proofline | ACCEPTED CORRECTLY | 445.425 |
| merge-settings | sol | raw-request | p2p | BUDGET EXHAUSTED | 651.078 |
| merge-settings | luna | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 107.558 |
| safe-archive-paths | sol | shared-preplanned | agent-plus-review | ACCEPTED CORRECTLY | 230.626 |
| safe-archive-paths | luna | shared-preplanned | proofline | ACCEPTED CORRECTLY | 300.701 |
| safe-archive-paths | luna | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 157.584 |
| safe-archive-paths | sol | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 124.298 |
| safe-archive-paths | sol | shared-preplanned | proofline | FAILED | 166.579 |
| safe-archive-paths | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 453.271 |
| interval-union | sol | raw-request | proofline | ACCEPTED CORRECTLY | 501.274 |
| interval-union | sol | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 156.142 |
| interval-union | luna | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 155.622 |
| interval-union | sol | raw-request | agent-plus-review | ACCEPTED CORRECTLY | 208.297 |
| interval-union | luna | raw-request | proofline | ACCEPTED CORRECTLY | 259.976 |
| interval-union | sol | raw-request | p2p | BUDGET EXHAUSTED | 887.637 |
| dependency-order | sol | shared-preplanned | proofline | ACCEPTED CORRECTLY | 428.766 |
| dependency-order | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 304.572 |
| dependency-order | sol | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 149.881 |
| dependency-order | luna | shared-preplanned | ordinary-agent | ACCEPTED CORRECTLY | 105.254 |
| dependency-order | luna | shared-preplanned | proofline | ACCEPTED CORRECTLY | 204.381 |
| dependency-order | sol | shared-preplanned | agent-plus-review | ACCEPTED CORRECTLY | 163.393 |
| retry-schedule | luna | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 91.100 |
| retry-schedule | sol | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 172.548 |
| retry-schedule | luna | raw-request | proofline | ACCEPTED CORRECTLY | 284.897 |
| retry-schedule | sol | raw-request | p2p | BUDGET EXHAUSTED | 687.904 |
| retry-schedule | sol | raw-request | proofline | BUDGET EXHAUSTED | 241.015 |
| retry-schedule | sol | raw-request | agent-plus-review | ACCEPTED CORRECTLY | 265.365 |
| utc-timestamps | sol | shared-preplanned | agent-plus-review | FAILED | 410.565 |
| utc-timestamps | sol | shared-preplanned | ordinary-agent | FALSE ACCEPTED | 271.778 |
| utc-timestamps | sol | shared-preplanned | proofline | FAILED | 5.236 |
| utc-timestamps | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 473.485 |
| utc-timestamps | luna | shared-preplanned | proofline | FALSE ACCEPTED | 640.340 |
| utc-timestamps | luna | shared-preplanned | ordinary-agent | FALSE ACCEPTED | 134.884 |
| query-multimap | sol | raw-request | agent-plus-review | FAILED | 206.973 |
| query-multimap | luna | raw-request | proofline | ACCEPTED CORRECTLY | 313.498 |
| query-multimap | sol | raw-request | p2p | BUDGET EXHAUSTED | 240.254 |
| query-multimap | luna | raw-request | ordinary-agent | ACCEPTED CORRECTLY | 91.795 |
| query-multimap | sol | raw-request | proofline | ACCEPTED CORRECTLY | 416.114 |
| query-multimap | sol | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| version-order | sol | shared-preplanned | proofline | ACCEPTED CORRECTLY | 485.611 |
| version-order | luna | shared-preplanned | proofline | ACCEPTED CORRECTLY | 423.651 |
| version-order | luna | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| version-order | sol | shared-preplanned | p2p | BUDGET EXHAUSTED | 903.301 |
| version-order | sol | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| version-order | sol | shared-preplanned | agent-plus-review | NOT EXECUTED | unknown |
| redact-secrets | sol | raw-request | proofline | ACCEPTED CORRECTLY | 385.105 |
| redact-secrets | sol | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| redact-secrets | sol | raw-request | p2p | NOT EXECUTED | unknown |
| redact-secrets | sol | raw-request | agent-plus-review | NOT EXECUTED | unknown |
| redact-secrets | luna | raw-request | proofline | NOT EXECUTED | unknown |
| redact-secrets | luna | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| json-pointer | sol | shared-preplanned | agent-plus-review | NOT EXECUTED | unknown |
| json-pointer | sol | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| json-pointer | sol | shared-preplanned | proofline | NOT EXECUTED | unknown |
| json-pointer | sol | shared-preplanned | p2p | NOT EXECUTED | unknown |
| json-pointer | luna | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| json-pointer | luna | shared-preplanned | proofline | NOT EXECUTED | unknown |
| ttl-cache | sol | raw-request | proofline | NOT EXECUTED | unknown |
| ttl-cache | luna | raw-request | proofline | NOT EXECUTED | unknown |
| ttl-cache | sol | raw-request | agent-plus-review | NOT EXECUTED | unknown |
| ttl-cache | sol | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| ttl-cache | sol | raw-request | p2p | NOT EXECUTED | unknown |
| ttl-cache | luna | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| atomic-patches | sol | shared-preplanned | p2p | NOT EXECUTED | unknown |
| atomic-patches | sol | shared-preplanned | agent-plus-review | NOT EXECUTED | unknown |
| atomic-patches | sol | shared-preplanned | proofline | NOT EXECUTED | unknown |
| atomic-patches | luna | shared-preplanned | proofline | NOT EXECUTED | unknown |
| atomic-patches | sol | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| atomic-patches | luna | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| stream-deduplication | sol | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| stream-deduplication | sol | raw-request | proofline | NOT EXECUTED | unknown |
| stream-deduplication | sol | raw-request | p2p | NOT EXECUTED | unknown |
| stream-deduplication | luna | raw-request | proofline | NOT EXECUTED | unknown |
| stream-deduplication | sol | raw-request | agent-plus-review | NOT EXECUTED | unknown |
| stream-deduplication | luna | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| sliding-rate-limit | sol | shared-preplanned | p2p | NOT EXECUTED | unknown |
| sliding-rate-limit | sol | shared-preplanned | agent-plus-review | NOT EXECUTED | unknown |
| sliding-rate-limit | luna | shared-preplanned | proofline | NOT EXECUTED | unknown |
| sliding-rate-limit | luna | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| sliding-rate-limit | sol | shared-preplanned | proofline | NOT EXECUTED | unknown |
| sliding-rate-limit | sol | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| schema-migration | luna | raw-request | proofline | NOT EXECUTED | unknown |
| schema-migration | sol | raw-request | proofline | NOT EXECUTED | unknown |
| schema-migration | sol | raw-request | p2p | NOT EXECUTED | unknown |
| schema-migration | luna | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| schema-migration | sol | raw-request | agent-plus-review | NOT EXECUTED | unknown |
| schema-migration | sol | raw-request | ordinary-agent | NOT EXECUTED | unknown |
| inventory-transactions | sol | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| inventory-transactions | luna | shared-preplanned | proofline | NOT EXECUTED | unknown |
| inventory-transactions | sol | shared-preplanned | p2p | NOT EXECUTED | unknown |
| inventory-transactions | sol | shared-preplanned | agent-plus-review | NOT EXECUTED | unknown |
| inventory-transactions | luna | shared-preplanned | ordinary-agent | NOT EXECUTED | unknown |
| inventory-transactions | sol | shared-preplanned | proofline | NOT EXECUTED | unknown |

- raw-request: 25% target INCONCLUSIVE; quality gate False.
- shared-preplanned: 25% target INCONCLUSIVE; quality gate False.

- Synthetic standard-library component tasks; not large production repositories.
- Held-out tags mean excluded from prompt tuning, not unknown to the corpus author.
- Single host, fixed declared concurrency; repeated runs are not independent task samples.
- P2P raw planning uses its current local planning instructions under a benchmark source-preserving mandate.
- Shared plans are independently authored synthetic agreements; authoring attention/cost is unknown.
- Baselines use native Codex with a minimal completion/review response; transport overhead is included.
- Standalone coding gets the whole episode; coding plus review reserves one stage for review. P2P/Proofline use their stage limits.

Pricing: UNKNOWN: no declared rates. Remote targets: NOT EXECUTED: no remote effect grant in this pilot.

## Practical limits

This small amended component pilot does not establish performance on production repositories, other hosts, PR/merge delivery, unmeasured dollar prices, or the broader coding-model population. The Luna/Sol comparison reports these exact installed IDs and reasoning settings; it does not assume a price ordering. The 25% target remains a hypothesis wherever quality gates or paired successful populations are unavailable.
