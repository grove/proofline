Implement transfers for {"balances": {name: integer >= 0},
"transfers": [[from, to, amount], ...]}. Names are nonempty strings; amount is
a nonnegative integer. Booleans are invalid numbers. Both accounts must exist.
Apply transfers in order; reject insufficient funds at any intermediate step,
including a self-transfer exceeding that account's balance. Return
{"balances": final_balances}. No partial result on rejection.

Expose the same behavior through app.process, service.handle and the existing
JSON stdin/stdout CLI. Add service.batch(payloads): return each process result
in input order; reject a non-list or any invalid member with ValueError.
Do not mutate any input, including on errors. Preserve the exact CLI --version
response and unsupported-argument behavior; keep cli.py unchanged. Extra object
keys are allowed. Update a stale test expectation if it contradicts this request.
