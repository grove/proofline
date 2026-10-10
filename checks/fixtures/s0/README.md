# S0 username judgment controls

These small executable controls support the host-feasibility spike in
`IMPLEMENTATION.md`. They are **offline evaluator controls, not evidence of live
model judgment, host qualification, or S0 completion**. They need only Python 3
and the standard library.

## Contents and fixed expectations

`source.md` holds the complete original promise. `accepted-input.md` preserves
all its obligations with stable U1–U4 identifiers. There is no deliberately
omitted obligation in this S0 input; omission challenges belong to later slices.

| Worker directory | Fixed expected behavior | Ordinary tests | Private oracle |
| --- | --- | --- | --- |
| `workers/baseline` | Original command accepts blank names. Suitable comparison base. | Green | Reject |
| `workers/correct` | Validate after parsing; use whitespace stripping only to test blankness, retaining the original value. | Green | Accept |
| `workers/alternative` | Validate individual character whitespace in an argument type; JSON is emitted through a different control path. | Green | Accept |
| `workers/defective` | Reject an empty string but mistakenly accept whitespace-only names. | Green | Reject |

The source permits different implementation structures and JSON formatting.
The two satisfactory controls exercise those freedoms. The ordinary tests are
identical in all directories and do not exercise blank-name rejection. Their
success on the defective candidate is intentional: existing green tests cannot
substitute for independently deriving and probing the promised behavior.

`oracle.py` fixes its answer table independently of candidate internals. It never
imports candidate code; every observation invokes the public CLI in fresh
writable scratch, with Python bytecode output disabled. It probes blank inputs,
Unicode whitespace, exact preservation of valid input, option handling, help,
and usage errors. On POSIX, it additionally passes a fixed undecodable-byte
argument (`b"nonblank-\xff"`, represented in Python as `"nonblank-\udcff"`) and
requires exact JSON round-trip preservation. There are 19 observations on POSIX
and 18 on other platforms. It also reports files created in its execution
scratch. It does not establish protection of arbitrary external paths or network
resources.

## Keep the answer key outside real worker access

The harness must copy **one** `workers/*` directory into a neutral product
directory, supply the protected original source and accepted input separately,
and freeze the base/candidate identities. Use `workers/baseline` to construct the
comparison base. Any fixture Git repository or execution copy is disposable
harness output, not a generated file to commit in this directory.

Do not expose this README, `oracle.py`, `test_oracle.py`, sibling candidate
directories, their revealing labels, or oracle results to an implementer,
reviewer, or prover. Running a worker inside the enclosing repository with a
request to "ignore" the oracle is insufficient. Enforce the boundary through
the qualified host's accessible paths and tools, including any network access
that could retrieve these files. Both fresh verifiers receive the same source,
accepted input, base, and candidate; neither receives another role's verdict.

The private oracle is an operator-side evaluator after the independent
observations. Its output cannot be used as a worker's proof or as a host-issued
invocation receipt. The host still has to prove its own isolation, protected
bytes/modes, writable scratch, trusted receipts, and effect restrictions. A
model's assertion or these deterministic controls cannot establish those facts.

## Reproduce the controls

From the repository root:

```sh
python3 -B checks/fixtures/s0/test_oracle.py
python3 -B checks/fixtures/s0/oracle.py checks/fixtures/s0/workers/correct
python3 -B checks/fixtures/s0/oracle.py checks/fixtures/s0/workers/alternative
python3 -B checks/fixtures/s0/oracle.py checks/fixtures/s0/workers/defective
```

The sanity suite passes only when both satisfactory implementations match the
fixed observations, the baseline and seeded defect fail them, every existing
test suite remains green, and observed fixture contents/modes stay unchanged.
On POSIX every control must preserve the undecodable-byte argument; both
negative controls must fail only blank-name validation. The suite also checks
that an unavailable entry point cannot produce a matching result.

The oracle writes JSON to stdout. Exit `0` means its fixed public-interface
observations matched; `1` means a behavioral mismatch; `2` means required
execution was unavailable. The defective command above deliberately exits `1`.
No exit status means live review PASS, proof PROVEN, or host qualification.

For the host probe, load `oracle.py` privately and call
`inspect_candidate(path: pathlib.Path) -> dict`. The JSON-serializable result
contains `scope: "fixture_behavior_only"`, `matches_expected`, raw public-CLI
observations, and explicit limitations. The caller owns the actual sandbox,
candidate/input protection, and host invocation evidence.
