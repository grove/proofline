# atomic-transfers

`app.process(payload)` and `service.handle(payload)` accept an object with
`balances` (account names mapped to nonnegative integers) and `transfers`
(a list of `[from, to, amount]` lists). Account names must be nonempty strings,
both accounts must exist, and amounts must be nonnegative integers. Booleans
are rejected as balances and amounts. Extra object keys are allowed.

Transfers are applied in order. Insufficient funds at any step raise
`ValueError`, including self-transfers larger than the current balance.
Successful calls return `{"balances": final_balances}`; rejected calls return
no partial result. Inputs are never modified.

`service.batch(payloads)` accepts a list and returns each result in input order.
A non-list or any invalid member raises `ValueError` without changing inputs.

The CLI reads one JSON payload from stdin and writes its JSON result to stdout:

```sh
echo '{"balances":{"a":5,"b":0},"transfers":[["a","b",3]]}' | python3 cli.py
```

Invalid input exits with status 2 and an `ERROR:` message on stderr.
`python3 cli.py --version` prints `api-v1`; unsupported arguments exit with
status 2.

Run tests with `python3 -B -m unittest discover -s tests`.
