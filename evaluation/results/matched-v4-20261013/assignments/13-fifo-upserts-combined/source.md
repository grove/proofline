Implement a FIFO record cache for {"capacity": integer >= 0,
"events": [{"id": nonempty_string, "value": any_JSON_value}, ...]}.
Every event must contain both id and value. Booleans are invalid capacities.
Update an existing ID in its original insertion position, without promoting it.
When inserting a new ID would exceed capacity, evict the oldest resident ID.
Capacity zero immediately evicts EVERY event. Return {"items": [final records
in FIFO order], "evicted": [IDs in eviction order, retaining repetitions]}.
Output records contain only id and value; extra input keys are ignored.
Reject malformed records/containers with ValueError. Input values may be null.

Expose the same behavior through app.process, service.handle and the existing
JSON stdin/stdout CLI. Add service.batch(payloads): return each process result
in input order; reject a non-list or any invalid member with ValueError.
Do not mutate any input, including on errors. Preserve the exact CLI --version
response and unsupported-argument behavior; keep cli.py unchanged. Extra object
keys are allowed. Update a stale test expectation if it contradicts this request.
