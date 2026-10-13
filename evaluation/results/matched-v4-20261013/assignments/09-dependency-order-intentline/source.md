Implement stable dependency ordering for {"nodes": [name, ...],
"edges": [[before, after], ...]}. Names are nonempty strings and nodes unique.
Edges must reference declared nodes. Repeated identical edges have no effect.
At EACH step choose the earliest node in the ORIGINAL nodes list whose
dependencies are already emitted. Return {"order": [names]}.
Reject malformed records, self-loops and ANY cycle, including disconnected
cycles, with ValueError. Empty nodes/edges are allowed. Never sort by name.

Expose the same behavior through app.process, service.handle and the existing
JSON stdin/stdout CLI. Add service.batch(payloads): return each process result
in input order; reject a non-list or any invalid member with ValueError.
Do not mutate any input, including on errors. Preserve the exact CLI --version
response and unsupported-argument behavior; keep cli.py unchanged. Extra object
keys are allowed. Update a stale test expectation if it contradicts this request.
