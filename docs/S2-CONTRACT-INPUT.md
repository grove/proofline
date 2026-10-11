# Experimental standalone contract adapter

`proofline.py inspect-contract contract.md` reads the current P2P Markdown
contract shape without importing P2P code, executing product commands, changing
the contract, or granting approval. It reports the exact UTF-8 byte hashes,
revision, original-source location/hash and preserved criterion IDs.

The supported subset has one `# Acceptance contract:` heading, one `Contract
revision: vN`, a single relative Markdown `Source` link, `Parent: None`,
`Prerequisites: None`, an intended outcome, and the current eight-column
acceptance matrix. Rows must be complete, uniquely identified, and `planned`.
Unresolved gaps and open questions must explicitly be `None` or `- None`.
Exclusions and change notes remain in the exact contract bytes; nothing is
renumbered or summarized away. CRLF bytes are preserved.

The adapter was derived from the current
`skills/productivity/plan-acceptance/SKILL.md` output template and the approval
rules in `docs/acceptance-contract-protocol.md` of the local Promise-to-Proof
checkout. It deliberately does not import that project's controller, generated
checkpoint formats, legacy records, or approval parsers.

## Authority and execution

Inspection is read-only and never says a contract is approved. For this first
adapter, the invoking user must explicitly adopt the exact contract and original
source bytes. Only then may the initiating agent invoke:

```sh
python3 -B proofline.py deliver --repo /path/to/product \
  --contract /path/to/contract.md \
  --adopt-contract-sha256 EXACT_USER_ADOPTED_CONTRACT_HASH \
  --adopt-source-sha256 EXACT_USER_ADOPTED_SOURCE_HASH \
  --approval-reference 'Actual user adoption reference' \
  --map 'Task-specific public interfaces and commands'
```

These flags carry the trusted caller's actual user authorization; they do not
cryptographically authenticate it. An agent must never generate them from a
generic implementation request, a file saying `approved`, an issue label,
an agent-created fixture or a planning/audit result. The skill enforces this
invocation rule. Existing P2P approval receipts need trustworthy inspection or
new exact adoption, not automatic conversion into authority.

The runner compares both hashes before host/model dispatch. A mismatch or
missing adoption yields `INPUT NOT READY`, zero dispatches, and an actionable
record. It preserves the exact source and complete contract as protected inputs,
then uses the same implementation/freeze/review/proof functions as direct
delivery. The record retains the original locations, revision, hashes, stable
IDs and actual adoption reference. Saved acceptance checks those bindings again.
Planned tests/oracles are guidance; proof still needs actual observations, and
the independent prompts require detection of omitted original-source promises.

Parent/child contributions, combined-parent acceptance, prerequisites and remote
source recovery are currently explicit input gaps. A closed prerequisite or
successful child cannot become a parent-completion claim. The adapter does not
rewrite these inputs into a standalone contract or direct brief.

## Qualification status

Four deterministic tests cover exact bytes, revision/IDs/exclusions, absent and
stale adoption, unavailable source, ambiguous/incomplete/unsupported matrices,
unresolved decisions, parent/prerequisite gaps and rejection before dispatch.
Synthetic test adoption references never authorize a real model run.

**S2 is not complete.** No actual approved, source-linked P2P contract has been
provided for P1's live acceptance run; the contract-path positive and negative
judgment controls and P4 contribution support remain unqualified. The next step
is an exact approved/adopted contract and its original source, then the same
live success/defect/omission checks used for S1. Do not claim Milestone A or
start S3's comparison gate from parser tests alone.
