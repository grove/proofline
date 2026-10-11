# S1 direct local delivery

S1 passed its scoped gate on 11 October 2026 using the S0-qualified macOS host,
Codex 0.162.1, Python 3.14.8, and the configured `gpt-6-luna` / `high` preference.
These are small real CLI deliveries and falsification controls, not a benchmark
or a claim that arbitrary repositories are supported.

## Actual observations

| Task/control | Dispatches | Seconds | Observed outcome |
| --- | ---: | ---: | --- |
| Username validation, from the original baseline | 3 | 131.985 | READY → PASS → PROVEN; status confirms LOCAL ACCEPTED; all 19 private oracle observations match |
| Independent skill forward test: add `greet --version` | 3 | 141.805 | READY → PASS → PROVEN; status confirms LOCAL ACCEPTED; 14 separately checked CLI cases pass |
| Correct product but U1 omitted from the brief | 2 | Part of 220.044-second challenge | Both roles return NOT VERIFIED and name the missing original-source promise |
| New leading-hyphen username regression | 2 | Same challenge | Both roles return FAIL; existing tests stay green, independent oracle rejects |

The forward tester independently followed SKILL.md, prepared its own small
repository and source-grounded D1–D4 brief, invoked one delivery episode, then
checked the public CLI and preserved repository bytes including Git metadata.
It did not use a planner or P2P controller. Its findings improved `status` to
print the exact candidate commit and documented macOS tool-discovery limitations.

The omission/regression experiment deliberately invokes both acceptance roles
on bad inputs to test each judgment. Ordinary delivery remains review-first:
a material review failure skips proof. Positive roles do not share transcripts,
scratch, judgments or execution trees. Each verifier runs actual boundary
canaries and matches the same original source, brief, base, commit and tree.

## Retained evidence

All paths below are relative to the checkout; these ignored local records are
not remotely published artifacts:

- `.proofline/delivery/6a1b3aea1df64b8689bfcc1ab56c2ab2/report.json` and
  `independent-oracle.json`. Candidate commit
  `e28b8039af92f7c89bf23605eb8afd0ff5e6c049`, tree
  `95d158078589988011aa28841a36a33118d77ff7`.
- `.proofline/skill-forward/delivery/report.json` and
  `.proofline/skill-forward/forward-test-result.json`. Candidate commit
  `a40ec8c92428b3d1704e29d9e1b39b67e4babb66`, tree
  `30fdc5aabfc181013ac4e10f3bb05ebd976013a4`.
- `.proofline/s1-judgments/ee4f47d626b34cd6b83f2e2e3ede8435/report.json` and
  `independent-oracle.json`. All four fresh native invocations matched the
  expected rejection, with unchanged protected inputs.

The records contain native thread IDs, invocation argv, raw JSONL hashes,
commands/results and criterion observations. None substitutes an imported or
mocked verdict for live evidence. `proofline.py status` re-reads native evidence
and rejects stale candidates; editing after checking does not preserve success.

| Episode | Input tokens | Cached input (subset) | Output tokens | Reasoning output (subset) |
| --- | ---: | ---: | ---: | ---: |
| Username delivery | 336,095 | 277,504 | 11,722 | 3,854 |
| Skill forward delivery | 287,415 | 242,688 | 8,713 | 3,076 |
| Negative judgment controls | 666,140 | 593,408 | 17,371 | 4,832 |

Reviewer/prover subprocess times were 33.226/52.690 seconds for username
delivery and 46.286/55.485 seconds for the forward test. Native usage categories
are recorded as reported, not summed into a fabricated bill. Monetary cost,
human-attention time, upstream implementation cost and a comparative baseline
were not measured. Failed S0 development experiments are retained separately in
the [S0 report](S0-CODEX-RUNNER.md), not hidden from an efficiency claim.

## Gate mapping and limits

D1 is supported by the two actual deliveries and independent skill forward test.
D2 is supported by frozen identity/canary observations, status checks and stale
candidate regressions. D3/D4 combine the real omission/regression controls with
S0's structurally different good candidate and green-test defect, plus mechanical
checks for absent verifiers, hollow/missing references and contradictory reports.
D5 is supported by the retained records and explicit local-only outcomes.

The final native suite ran 51 tests: 49 passed, two Linux-specific tests skipped.
All three fixed oracle-control tests passed. The skill's bundled quick validator
could not run because its own PyYAML dependency was unavailable; its simple
frontmatter/references were checked manually and the actual forward test passed.
Proofline itself has no added Python dependency.

This initial runner accepts clean Git repositories with regular tracked files.
It freezes new ignored files too, rejects links/special files/nested repositories,
preserves exact blobs and executable modes without export-ignore or filters,
and captures the full untruncated Git diff. Verifiers execute against protected
product files and use scratch for outputs; unsupported source-mutating harnesses
remain NOT VERIFIED. There is no evidence-only recovery, correction loop,
resume, dependency installation, network service, publication or merge path yet.

The evidence opens S2, not S3. S2 still needs an actual approved-contract live
qualification. Milestone A and performance superiority remain unclaimed.
