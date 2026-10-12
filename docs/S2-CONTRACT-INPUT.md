# Approved-contract input and live qualification

`proofline.py inspect-contract contract.md` reads current P2P Markdown without
importing its controller, executing product commands, changing the agreement,
or granting approval. It reports exact UTF-8 hashes, revision, original source
chain, stable criterion IDs, parent/contribution identities and scope.

The adapter requires the current eight-column acceptance matrix, complete unique
`planned` rows, an intended outcome, exclusions, change notes, and explicit
absence of unresolved decisions and evidence gaps. Relative `Source` links can
name Markdown or JSON; linked source contracts are followed to their original
inputs. Every constituent retains its path and byte hash. Single-source byte
identities remain unchanged; multiple sources have a length-indexed bundle whose
hash is reported separately. Cycles and unrecoverable inputs are readiness gaps.

## Approval and preserved inputs

The initiating caller must inspect the original source and actual authority.
Inspection, a file saying `approved`, an issue label, or an agent-authored fixture
does not authorize delivery. Use either explicit user adoption of the displayed
exact contract/source bytes, or an actual P2P approval reference whose authority
the caller has established. Supply both exact input hashes and the reference;
an inspected P2P reference additionally supplies its file and digest:

```sh
python3 -B proofline.py deliver --repo /path/to/product \
  --contract /path/to/contract.md \
  --adopt-contract-sha256 EXACT_AUTHORIZED_CONTRACT_HASH \
  --adopt-source-sha256 EXACT_AUTHORIZED_SOURCE_OR_BUNDLE_HASH \
  --approval-reference 'Actual inspected original approval reference' \
  --approval-file /path/to/original-approval.md \
  --approval-sha256 EXACT_INSPECTED_APPROVAL_HASH \
  --map 'Task-specific public interfaces and commands'
```

Omit the last two approval flags for direct exact user adoption. These flags are
trusted-caller assertions, not cryptographic authentication or automatic P2P
receipt import. The adapter checks that the inspected reference bytes still
match and name the exact contract digest. It never interprets arbitrary approval
prose as authority. Synthetic parser references never authorize a model run.

Absent/stale approval, changed source, an incomplete matrix or unavailable
prerequisite produces `INPUT NOT READY` before host/model dispatch. The complete
source, unchanged contract, approval and parent/contribution snapshots are
protected inputs. Their context digest joins the same frozen base/candidate
binding used by S1. Fresh review and proof receive every material criterion ID
unchanged. Planned checks remain guidance; their presence is not an observation.
The trusted run record preserves the complete original approval reference bytes.
Workers receive its inspected reference, path and digest; the raw payload is
excluded because a P2P state record can contain old peer verdicts. Predecessor
agreement/review/proof documents required by the source remain available as
historical preservation context, never as proof of the new candidate.

Successful `status` also rechecks the original contract/source/context and
inspected approval reference. Changed agreements cannot inherit old acceptance.
Historical qualification requires a retained, clearly attributed snapshot;
substituting historical routing for today's routing is not supported.

## Parent and prerequisite boundary

A child requires one linked parent agreement, its exact snapshot digest, a linked
contribution plan and its exact `## Approved delivery plan` section digest. Each
child row maps through `Source` to existing qualified parent revision/IDs.
The source retains the full parent and transitive original promises; both roles
check the child's complete contribution and inherited constraints. Unrelated
sibling outcomes stay outside child acceptance. Child local acceptance always
records `parent_completion: false`.

A contract with `## Children` is a combined-parent request. Its full matrix and
original source are checked by all three fresh stages on one assembled candidate;
only that successful delivery can record parent completion. Historical child
verdicts and closed tickets cannot compose into a parent verdict.

Runtime prerequisite imports remain unsupported and fail closed. The supported
child input shape permits `None`, or the selected initial-sizing contract's explicit
absence of prerequisites beyond its approved parent agreement, backed by its
captured contribution plan. This does not waive inherited availability or
constraints: the independent roles still check them. Arbitrary prerequisite
prose, “issue closed”, a missing outcome, or an unsupported snapshot is an
actionable input gap. The adapter does not rewrite such inputs into a standalone
contract or direct brief.

One additional supported shape is the diagnosis correction's preservation-only
constraint: its source supplies an exact predecessor patch and hashes for the
predecessor agreement, review, and proof. All three documents must remain
recoverable with those exact hashes, and both reports must identify the same
source-bound predecessor candidate. They are captured as protected context;
their old verdicts cannot prove the new candidate. This supports preservation,
not importing arbitrary runtime prerequisites or authorizing installation.

## Reproduce the live gate

First deliver the actual approved contract through the ordinary CLI above, then:

```sh
python3 -B checks/s2_live.py /path/to/delivery/report.json \
  --parent-record /path/to/retained-approved-child/report.json \
  --preservation-manifest /path/to/preserved-originals.json \
  --seconds 3600 --stage-seconds 600
```

The focused qualification accepts the real diagnosis correction or the original
initial-sizing child. For the diagnosis case, retain the actual sizing child
record separately for parent/contribution controls. Its bindings and frozen
candidate are revalidated, and its actual outcome is recorded without upgrading
a failed or unverified child run to acceptance. The positive delivery must still
be locally accepted. Nine zero-dispatch readiness controls cover both contracts;
six fresh reviewers/provers challenge an omitted source promise, a candidate
regression, and the complete original parent on the incomplete sizing candidate.
Altered controls are explicitly unapproved fault
injections; they do not grant implementation authority. Findings must name the
challenged obligation. All observations, contexts, elapsed time and available
usage are retained locally; existing output is never overwritten.
For the diagnosis replay the preservation manifest contains original attempt and
agreement file paths and hashes captured before work. The qualifier rechecks all
of them before and after the live controls. It does not reconcile those attempts.

If a mechanical scoring correction is needed, audit a completed record without
changing any worker report or rerunning a model:

```sh
python3 -B checks/s2_live.py /path/to/qualification/report.json --audit
```

The audit revalidates original positive acceptance, child bindings, every native
control report and its frozen source/candidate, all nine readiness records, fresh
thread identities, and preserved original files. It writes a separate record;
incomplete or changed observations cannot qualify. This is qualification scoring,
not product recovery, resume, or imported P2P acceptance.

The first sizing replay reached READY and PASS, then returned NOT VERIFIED:
material planning/slicing and installed-skill behavior had not been observed.
That result and the earlier environment failures remain in the trial ledger.
The diagnosis positive and full negative-control gate passed; the separate audit
revalidated every native receipt and frozen candidate. See
[actual agreements, failed trials and costs](S2-LIVE-EVIDENCE.md).

**S2's narrow live gate is OBSERVED.** This qualifies the demonstrated input
shapes, not arbitrary P2P prerequisites or successful child/combined-parent
delivery. S3 may now start. Recovery, resume and publication remain deferred.

## Experimental native Intentline input

`proofline.py inspect-intentline BUNDLE` is a dependency-free offline inspection,
with authorization not_established and consumer_execution not_observed. The
Proofline-owned validator is adapted from a pinned Apache-2.0 producer inspector;
its shared ancestry is disclosed in THIRD_PARTY_NOTICES.md, not claimed as an
independent review. It imports neither Intentline nor P2P and never executes the
exported inspector. Original direct and P2P S2 paths retain their prior semantics.

Native delivery explicitly selects `--intentline-bundle BUNDLE`, mutually exclusive
with --source/--brief and --contract, and needs `--adopt-contract-sha256`,
`--adopt-source-chain-sha256`, `--adopt-bundle-sha256`, and an actual caller-inspected
`--approval-reference`. Inspection/export/Intentline ADOPTED_ASSERTED, an approval
label, generated JSON, a hash or ambient credentials cannot populate these grants.
The trusted initiating caller must establish actual authority to adopt the exact
displayed contract and complete source chain. These flags record that external
boundary; they do not authenticate a human. Optional --approval-file/--approval-sha256
bind actual externally inspected bytes to both identities and are revalidated.

The full current canonical JSON, separate original/amendment streams, constraint
sources and bounded predecessor records are protected inputs for all three roles.
The indexed source display is not a verbatim single request. Binding current project
documents must be exact regular tracked files in a clean product. Raw approval
payload/reference/path remains host-protected and is replaced by a binding hash
in worker context. Permission/input-map, bundle, source-chain, contract and candidate
identities are frozen together; status revalidates original bundle, external
reference, product documents, candidate and actual independent receipts.

Native input failures return INPUT NOT READY before dispatch with no direct/P2P
fallback. This route is experimental/offline-qualified only: producer bundles,
actual parser/admission/status and authored fake-host controls are tested; they
are not real model judgment, actual human approval or live delivery qualification.
No task-specific native inference budget/host grant exists. Live end-to-end delivery,
review and proof remain not_run. P2P S2 live qualification is unchanged.
