# S3 local four-way comparison

## Completed fixed 240-second repeat — 11–12 October 2026

S3's local experiment is complete. All 20 assignments ran with the declared
versions and limits. Ordinary agent, agent plus review and Proofline each
correctly delivered four positive cases; P2P delivered two. All four cohorts
correctly rejected the omitted-source agreement. No false acceptance or timeout
was observed in this repeat. P2P's two invalid implementation handoffs remain
failures, with their correct partial candidates and full costs retained.
Recovery, resume, publication and merge remain deferred.

| Case | Ordinary agent | Agent + review | P2P | Proofline |
| --- | --- | --- | --- | --- |
| Missing validation | Accepted correctly | Accepted correctly | Accepted correctly | Accepted correctly |
| Correct alternative | Accepted correctly | Accepted correctly | Failed handoff | Accepted correctly |
| Green tests / defect | Accepted correctly | Accepted correctly | Accepted correctly | Accepted correctly |
| False scope change | Accepted correctly | Accepted correctly | Failed handoff | Accepted correctly |
| Omitted source promise | Qualified rejection | Qualified rejection | Qualified rejection | Qualified rejection |

The omission's raw outcome is `FAILED` with
`matched_source_gap_rejection: true`: it is a successful negative workflow
control, not a satisfactory delivery. The private oracle accepted all observed
candidate behaviors, including the two candidates whose handoffs failed.
Working code never certified the deliberately incomplete agreement.

### Versions, limits and evidence

The run began at `2026-10-11T21:31:17.610925+00:00`, used shared preplanned inputs,
and ran all assignments sequentially. Every cohort had **900 seconds per
assignment and 240 seconds per stage**; P2P retained 12 dispatches and one repair.
The configured model was `gpt-6.1-sol`, reasoning `high`, with Codex CLI
`0.162.1` (binary SHA-256
`74c6a6d263f40d65f99c27a815275f5b4ed0bcc2baecc396b4cf3255498bdfc0`).
The host was Apple Silicon macOS 26.6.2 (25G83), Apple Git 2.54.0, and controller
Python 3.14.8. Ordinary/Proofline observation maps use that interpreter; P2P
workers used system Python 3.9.6 for product checks. Actual commands are retained.
That interpreter difference further limits performance comparisons.

| Runtime | Commit | Archived patch SHA-256 |
| --- | --- | --- |
| P2P | `7e5e62c8257a1e240ab74d1a12ca3dbdc11154a9` | `39deded453e5a7f9d4273587a98e09a895dcb5b90d65f23c010197cb70749d22` |
| Proofline | `309c5e4a78386c89e76d20f1ae446d9a40e52be8` | `5094d7d85e4888501b61beccff0fe168c880925c2cea7c8966e8c7eb0d2730b6` |

`repair-comparison-240/operator/manifest.json` archives the declaration before
model calls, both patches, runners, instruction package hashes, transport and
oracle identities. The controller hash is
`1c29f8efdff3ed93b02a01f29caef598dc111c14da3292af2e4585923084d3e7`;
the transport hash is
`c2c8d2fd4a0e617f92e6d81ae369d5d7a3c304b7b32bf337330132c323367cbf`.
The original oracle remains
`f919e131ee691fcc396c24661bb8e7f4faa214f2ec10690dde39b0d82cd69b2f`.
No runtime, prompt, source, oracle or limit changed during the repeat.
Host details observed during the run are separately identified in
`host-observation.json`. Later documentation edits do not alter archived runtime versions.

The S2 readback gate and four native oracle sanity controls passed before model
calls. All 20 scores have actual executed observations. All five P2P privacy
probes denied answer-key reads through absolute paths, symlinks and subprocesses.
Final readback preserves eight earlier and four new accepted Proofline records;
see `repair-accepted-readback/report.json`. No model calls were needed for readback.
Evidence lives under `.proofline/s3/`; original report bytes and scores are unchanged.

Reproduce a fresh current-version run with a new output directory on the qualified
host (this invokes real models):

```bash
python3.14 -B checks/s3_compare.py \
  --s2-record .proofline/s2-live/final-audit/report.json \
  --p2p-repo /Users/grove/projects/promise-to-proof \
  --output .proofline/s3/new-comparison-240
```

### Costs and remaining handoff mechanism

| Cohort | Correct deliveries / 4 | Native calls | Delivery seconds, all five assignments | Seconds per correct delivery |
| --- | ---: | ---: | ---: | ---: |
| Ordinary agent | 4 | 5 | 379.941 | 94.985 |
| Agent + review | 4 | 9 | 740.914 | 185.229 |
| P2P | 2 | 20 | 2,703.203 | 1,351.602 |
| Proofline | 4 | 13 | 1,172.056 | 293.014 |

These failure-inclusive delivery subtotals include the negative control and
exclude separate private scoring/setup. The repeat took 5,089.055 seconds,
including 17.333 seconds of setup and independent scoring. All 47 model calls
have reported usage in `repair-comparison-240/operator/cost-accounting.json`.

The fresh `repair-final-summary/report.json` includes the original eight campaign
inputs, every qualification generation, Git diagnosis and this repeat, without
adding intermediate summaries again. It retains **188 native model calls**:
176 have usage and 12 do not. Known native campaign time is at least
21,429.757 seconds; three campaign durations are unknown. The final P2P offline
suite separately took 4,613.483 seconds. Superseded interrupted validation logs
are retained; they are not passes. Monetary cost, human attention and upstream
planning cost remain unknown. No unknown cost is converted to zero.

Both P2P failures returned on time (171.814 and 210.253 seconds). Their commands
and output observations matched native evidence, but they labeled an expected
exit-2 blank-input rejection as `passed`. The unchanged slice validator requires
exit 0 for `passed`; a direct negative probe must be `observed`, or a wrapper
must assert the expected rejection and exit 0. The reports were rejected before
independent review/proof. `repair-failed-handoffs.json` preserves that diagnosis.
Two extra model preflights and report-format fragility remain observed P2P costs.
This is one small, repeatedly inspected CLI mechanism experiment; these numbers
establish neither general correctness nor a statistical performance advantage.

### Repairs, qualification and verification boundary

Readiness schema/prompt now require one exact declared criterion ID per check.
Existing slice field limits are exposed in the schema, and the Git inspection
recognizer accepts environment bindings and global Git options while retaining
host grounding and product relevance. Controller-managed skills and the canonical
protocol distinguish controller identity/storage duties from independent source,
scope and product judgment. Stage guidance reserves 30 seconds for handoff.
No source promise, private oracle, effect authority or trust validator was weakened.

The retained Proofline alternative timeout completed its independent checks,
including 1,112,063 Unicode scalar checks, then supplied no report. Shared guidance
now stops redundant work at sufficient evidence and reserves report time. In
this repeat its alternative prover returned a valid report in 133.514 seconds.

Native probes reproduced P2P's Git denial: absolute discovery inspected the
protected executions ancestor. Configuration isolation and a relative `.git`
file did not fix it. Relative `GIT_DIR`/`GIT_WORK_TREE` bindings did. The benchmark
transport supplies these relative to the initial worker directory and discloses
rebinding after changing directories. Implementation and read-only proof probes
passed with private keys still denied; filesystem permissions were unchanged.

The ninth qualification completed actual implementation, review and proof
(749.338 seconds including scoring) and a valid omitted-source handoff (485.392).
Its nine calls and 1,249.796-second campaign are additional costs, excluded from
paired scores. The exact qualified P2P patch was applied to the original checkout
without a commit or remote effect and verified identical to the tested copy.

| Retained qualification | Stage cap | Outcome / observed blocker |
| --- | ---: | --- |
| v1 | 180 | Native startup failed inside enclosing sandbox; no model calls, duration unknown |
| v2 | 180 | Both implementation handoffs timed out |
| v3 | 180 | Positive timeout; omission citation invalid |
| v4 | 240 | Positive timeout after metadata audits; omission citation invalid |
| v5 | 240 | Git-options recognizer and undisclosed citation-length failures |
| v6 | 240 | Unattributable scratch-test citation; omission diagnosis timeout |
| v7 | 240 | Implementation/review accepted, proof timed out; valid planning handoff initially miscounted |
| v8 | 240 | Positive Git fallback timeout; omission rejection qualified |
| v9 | 240 | Complete positive delivery and omission rejection qualified |

Each generation retains its pre-call manifest, source patches, native receipts,
failures and costs. Historical v7 flags are not rewritten after recognizing both
validated `BLOCKED` and `ACTIONABLE` planning handoffs. The user's new 240-second
cap is a separate generation; every 180-second failure remains unchanged.
Detailed declarations are retained in `retained-repair-declarations.md` and the
per-generation archives.

Proofline's native-enabled suite passed **75 tests**, with two Linux-specific
skips. The final default P2P suite ran **468 tests: 466 passed, one failure and
one error**. Both exceptions reproduce on the untouched checkout. The instruction
storage fixture used macOS's `/var` alias; all four snapshot tests pass with
canonical `TMPDIR=/private/tmp`, preserving the symlink guard. The packaging check
first invoked Python 3.9; with supported Python it still exposes missing shared
files in the pre-existing `publish-pr-review` package. Publication packaging is
deferred, and the default suite is **not reported as passing**. Checkout-based
native delivery/control qualified. Logs and hashes are retained in
`repair-regression-evidence.json` and `repair-regression-baseline.json`.

## Historical 180-second protocol and retained results

Predeclared after S2 passed, before the original comparison model calls. This is a directional
mechanism experiment on one small CLI promise, not a representative task sample.

All four cohorts receive the same original username source, a shared preplanned
contract, and the same product seed for each case. Compare ordinary agent,
ordinary agent plus fresh review, the actual current checked-in P2P controller,
and the existing Proofline runner. Use the same configured host/model where
feasible. Raw-request planning is not measured; shared upstream planning cost and
human attention time remain unknown. Record setup time separately.

| Case | Fixed seed / control | Expected source-valid delivery |
| --- | --- | --- |
| missing-validation | Existing baseline | Complete the original CLI promise |
| correct-alternative | Existing alternative implementation | Preserve and accept correct behavior |
| green-tests-defect | Existing defective implementation; its tests pass | Fix omitted whitespace behavior |
| false-scope-change | Correct seed changed to trim nonblank names; weak existing tests | Restore exact names and interface |
| source-omission | Correct alternative; shared contract omits R2 | Reject the incomplete agreement; do not claim acceptance |

The source-omission case separately scores agreement readiness and behavior:
working code cannot certify a deliberately incomplete approved plan. It is a
negative workflow control, not a satisfactory delivery. Fixed public-CLI answer
keys are the existing S0 oracle, with known-good/alternative/known-bad sanity
controls and the trim counterexample. Oracle code, sibling answer-bearing seeds,
operator records and per-case expected outcomes remain outside worker contexts.

Each cohort/case has at most 900 seconds; individual model stages have at most
180 seconds. P2P retains its own stages and bounded repair capability, with at
most 12 dispatches and one repair. Proofline keeps its three-stage path with no
recovery. Cases run sequentially; do not tune prompts or discard failures after
seeing scores. A failed current-P2P host invocation stays in the comparison and
is not replaced by an emulated review/proof pipeline.
All native transports disable the Codex daemon. The first current-P2P transport
used an enclosing private-read sandbox; the qualified replacement below moves
those denials into the native worker profile. Its controller, stage instructions
and repair logic are unchanged. Shared isolation and structured handoffs are harness overhead, not
an additional ordinary-agent reviewer or prover.

Score every assignment as accepted correctly, false accepted, false blocked,
failed, budget exhausted, or not executed. Include native elapsed time, calls,
available usage, reviewer/prover time and failed runs in time per independently
satisfactory delivery. Zero deliveries yields an unavailable ratio, not zero.
Monetary costs and unobserved usage/attention are unknown. Publish per-case
results and observed overhead/failure mechanisms without a superiority claim.

The native single-profile host is qualified and the guarded repeat is complete.
P2P still produced no accepted delivery within the fixed budgets; its completed
delivery/verifier-quality comparison remains inconclusive. Recovery, resume and
product publication remain deferred.

The first setup trial exposed two harness errors: shared `U` IDs are not accepted
by current P2P, and ordinary-agent handoffs need exact native command citations
or empty command lists. Both ordinary agents produced oracle-correct code but
their handoffs were invalid; P2P rejected the input grammar before dispatch;
Proofline accepted the first case. The next alternative-agent assignment was
interrupted when the setup-error trial was stopped. All five attempted and 15
unstarted assignments remain explicit. The partial trial consumed 567.943 seconds
and six stage dispatches. It is excluded from quality comparisons but included
in campaign costs. Source text, case seeds and private oracle expectations are
unchanged. Shared plans now use `R1`–`R4`; the oracle's `U1`–`U4` are mapped to
those same promises. The corrected comparison is preregistered separately.
Its first startup stopped before model dispatch because personal P2P stage skills
are not installed; that zero-dispatch failure and its unknown duration remain
recorded. The final run's entry adapter resolves `installed_skill` to the unchanged
current checkout packages. It records their hashes and changes no P2P stage,
controller, repair, approval, or verdict logic. No host installation is performed.

Before further P2P model calls, a transport follow-up is declared for its five
assignments. The original transport used `source.md` inside `.p2p/work/username`,
which current P2P rejects as a generated artifact before admission. All original
invocations remain recorded, including their zero dispatches and elapsed time.
The follow-up uses P2P's supported `source-issue.md` basename and changes only the
contract's relative link; source bytes, seeds, requirements, limits and oracle
are identical. The real current parser and binding walker accept this location
in a zero-model smoke check. The collector uses P2P's actual external runtime
helper for attempt receipts and candidate location. This is a correction to the
benchmark transport, not a change to P2P. It runs after the original assignments
finish, without tuning from their scores. Both transport generations contribute
to campaign cost; only the supported transport is eligible for the P2P quality
comparison. The original setup-error campaign is likewise cost-only.

## Historical host qualification and 180-second repeat protocol

Before a second full comparison, reproduce the launch failure without a model.
The exact retained enclosing read-denial profile allows `/usr/bin/true` but a
second `sandbox-exec` exits 71 with `sandbox_apply: Operation not permitted`.
A direct Codex named-profile sandbox succeeds; the same invocation inside that
enclosing sandbox fails. This narrows the failure to that nested boundary on
this host; the earlier generic allow-default nesting check did not exercise it.

Use one native Codex permission profile instead. The benchmark transport removes
only P2P's three declared legacy sandbox settings and `--sandbox workspace-write`,
preserves the remaining arguments/configuration, and adds a named profile with
root reads, scratch writes, read-only Git metadata, network disabled, and all
previous private scoring path denials. Unexpected permission configuration fails
closed. Retain requested and effective argv separately, with transport and shim
hashes. No original P2P installation, controller, stage, repair or verdict rule
is changed. Codex documents profiles as an alternative to the legacy sandbox
settings, which cannot be combined:
[official permission documentation](https://developers.openai.com/codex/permissions).

Qualify the replacement with protected-input, private-read, mode-change, scratch
and reachable-loopback network canaries, then an actual P2P pipeline. Record this
extra qualification in campaign costs but exclude it from paired quality results.
After it qualifies, repeat all 20 assignments on the same host/model with the
same source bytes, five seeds, contract rows/omission, oracle, limits, stage
instructions and cohort prompts. Keep every earlier failure and cost. No oracle
or prompt adjustment follows inspection of results. Recovery, resume and product
publication remain deferred.

During the full repeat, inspection found that older P2P executions outside the
benchmark directory could expose sibling seeds through broad root reads. Before
the third P2P assignment, add a deny on the execution store and reopen only the
current disposable execution. A native canary establishes own-input reads and
denied sibling reads through absolute paths, symlinks and a subprocess. Preserve
the initial manifest, archived transport and both earlier P2P outcomes as costs;
declare the guard amendment and fresh repeats of those two P2P assignments. The
remaining cohorts already exclude that store. No sibling read was observed in
the earlier native command events, but those two P2P assignments are excluded
from quality results because their access boundary was incomplete. The change
affects private-input access only; source, seeds, oracle, host/model, prompts,
P2P stages, verdict rules and budgets remain fixed.

The subsequent key-access review also covers copies in the operator repository's
Git objects/bytecode and Codex session state. Before the fourth P2P assignment,
deny the entire operator repository and Codex state directory, with an explicit
read exception for the required RTK instruction. Native absolute, symlink and
subprocess canaries establish denial of repository/Git keys while RTK remains
readable. The final guard amendment makes the first three P2P assignments
cost-only and declares their fresh repeats under the complete guard. Preserve
all three archived transport versions and both amendments; no earlier record
is overwritten. Remaining P2P worker launches carry this same final profile.

## Historical qualified 180-second repeat and paired results

The single-profile transport is now qualified on the unchanged Codex 0.162.1
host/model. Process canaries establish protected-write and mode-change denial,
allowed scratch writes, and denied network access with a reachable-loopback
control. Final guards deny the operator repository (including Git/bytecode key
copies), Codex state/history except RTK, and sibling P2P executions. Native
absolute-path, symlink and subprocess canaries verify these read boundaries.
Two fresh P2P worker contexts independently completed their actual boundary
probes; the unchanged controller also accepted task readiness. This establishes
host/transport readiness, not completed P2P delivery.

All 20 repeat assignments finished. The three earlier P2P assignments are
cost-only; their predeclared final-guard fresh repeats also finished. The paired
view below selects only the final-guard P2P assignments, without discarding any
raw record or campaign cost. Source, seeds, oracle, model, current P2P commit,
instruction packages, prompts and budgets are unchanged. Each generation retains
its runner/transport hashes and native receipts; the guard amendments preceded
the affected model calls. No source-oracle or verdict-rule tuning occurred.

| Fixed case | Ordinary agent | Agent plus review | Current P2P, final guard | Proofline |
| --- | --- | --- | --- | --- |
| missing-validation | Accepted correctly | Accepted correctly | Failed: readiness IDs | Accepted correctly |
| correct-alternative | Accepted correctly | Accepted correctly | Failed: readiness IDs | Budget exhausted: prover |
| green-tests-defect | Accepted correctly | Accepted correctly | Budget exhausted: implementation | Accepted correctly |
| false-scope-change | Accepted correctly | Accepted correctly | Budget exhausted: implementation | Accepted correctly |
| source-omission | Failed: omission identified | Failed: omission identified | Failed: readiness IDs; omission unqualified | Failed: INPUT NOT READY |

Ordinary agent and agent plus review each produced four accepted correct
deliveries; Proofline produced three. All three explicitly identified the
omitted original exact-preservation promise and rejected the incomplete plan.
The omission seed remains behaviorally correct. No false acceptance was observed.
Proofline's correct-alternative candidate passed the private oracle and fresh
review, but its prover reached 180 seconds without a usable handoff. It is budget
exhausted, not accepted; its missing usage is unknown. The trimming case passed.
All three newly accepted Proofline records revalidate as LOCAL ACCEPTED.

Current P2P now establishes real worker boundaries and reaches implementation.
Three final-guard readiness responses were rejected for invalid requirement IDs:
`PREFLIGHT` and/or grouped IDs instead of one declared contract ID per check.
Its unchanged validator rejects them; the schema permits strings and its prompt
omits an explicit single-ID domain. Two implementations produced oracle-correct
code but reached the stage limit without usable completion reports. Neither
review nor proof ran. These are native readiness/handoff and budget failures,
not continuing nested-sandbox launch failures. P2P produced zero accepted
deliveries and no qualified omitted-source rejection. Its completed-delivery,
verifier-quality and throughput comparison remains inconclusive. Do not count
correct partial code as a completed delivery or a low failure time as speed.

The fixed oracle passed the repeat's four sanity controls and all four follow-up
controls. Every selected assignment has executed private observations; worker
inputs exclude the key paths. The full repeat has 38 distinct native threads and
the isolation follow-up seven more, with no overlap. Guard amendments preserve
both prior transport versions; these observations do not establish protection
against arbitrary same-user/controller tampering.

### Historical 180-second paired costs

Delivery seconds include each selected method's setup and failed assignments.
This table excludes extra harness generations only from the paired view; the
cumulative table below includes them all. The view itself is not added to
campaign costs a second time.

| Cohort | Dispatches | Accepted correct deliveries | Delivery seconds | Seconds per satisfactory delivery | Usage observed / unknown |
| --- | ---: | ---: | ---: | --- | --- |
| Ordinary agent | 5 | 4 | 440.385 | 110.096 | 5 / 0 |
| Agent plus review | 9 | 4 | 801.171 | 200.293 | 9 / 0 |
| Current P2P | 12 | 0 | 1376.010 | Unavailable: zero deliveries | 10 / 2 |
| Proofline | 13 | 3 | 1471.712 | 490.571 | 12 / 1 |

The full repeat took 3971.048 seconds and the three-assignment isolation follow-up
822.853 seconds, including shared setup and private scoring. These times are
from the same small promise and fixed sequential order, not a representative
sample or a superiority test. The earlier comparison's four accepted Proofline
deliveries remain recorded; this repeat's timeout is not replaced by that result.

### Historical campaign subtotal before the S3 repairs

| Cohort | Dispatches | Qualified correct deliveries across repeated campaigns | All satisfactory deliveries | Known delivery seconds | Seconds per satisfactory delivery | Known reviewer / prover seconds |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Ordinary agent | 12 | 8 | 8 | 1023.724 | Unknown; known subtotal 127.965 | Not executed / Not executed |
| Agent plus review | 19 | 8 | 8 | 1750.954 | 218.869 | 784.630 / Not executed |
| Current P2P | 25 | 0 | 0 | 2317.113 | Unavailable: zero deliveries | Not executed / Not executed |
| Proofline | 29 | 7 | 8 | 3331.613 | 416.452 | 995.081 / 1390.092 |

Counts across repeated campaigns are deliveries, not independent task samples.
Proofline's original setup-trial success remains an actual satisfactory delivery
but is excluded from paired quality counts. Its cumulative cost divided by only
seven qualified deliveries is 475.945 seconds. Ordinary agent's interrupted
setup dispatch still has unknown duration/usage, so its complete ratio is unknown.

| Cohort | Usage observed / unknown | Known input tokens | Cached tokens included in input | Known output tokens |
| --- | --- | ---: | ---: | ---: |
| Ordinary agent | 11 / 1 | 887619 | 687104 | 28192 |
| Agent plus review | 19 / 0 | 1758939 | 1352704 | 50224 |
| Current P2P | 22 / 3 | 1073921 | 765440 | 59501 |
| Proofline | 28 / 1 | 2902102 | 2311936 | 84829 |

Total: 85 native dispatches, usage observed for 80 and unknown for 5.
Known usage is 6622581 input tokens (5117184 cached)
and 222746 output tokens. Known campaign wall/process subtotals are
at least 8702.051 seconds. Full time remains unknown because
one startup duration and untimed preparation are unknown. The 3.786-second
non-overlapping zero-model diagnostic subtotal is included; later guard-canary
elapsed time overlaps the full repeat and is retained without double counting.
Monetary cost, human attention and upstream planning cost remain unknown.

The operator diagnosed the launcher, added private-read guards and declared
fresh P2P isolation repeats without changing prompts, source keys or budgets.
No P2P installation, upstream controller repair, resume, or product publication
was performed. The largest working-method overhead remains fresh review/proof;
current P2P additionally spends calls on readiness, rejects malformed prerequisite
reports and loses usable handoffs at the cap. Investigate ID schema/prompt
agreement and bounded evidence/handoff work before expanding automation. Do not
weaken source promises, extend limits after scoring, infer statistical benefit,
or claim the 25% pilot target. S4–S6 remain deferred.

Local readback references (native streams remain in their original locations):

| Record | SHA-256 |
| --- | --- |
| `.proofline/s3/single-sandbox/operator/report.json` | `0a5a56a1f53a025c36d88380a40beae508acff752fe26e7d6247b92e470846bd` |
| `.proofline/s3/single-sandbox/operator/audit.json` | `523ab4826179a9a1c17fcf40cc8eeec9f90cc10ce6c70b5859ba6f9d627b83a0` |
| `.proofline/s3/single-sandbox/operator/host-qualification-final.json` | `5dae30363c2a66202d1e495df4da2b1cc00637a769f47426bbec97cf98ec4f4e` |
| `.proofline/s3/single-sandbox/operator/guard-amendment.json` | `255bf54b70c5e4103a570d75314c34de2f3772357e38ef08ecbbb4f4cf2d2a5e` |
| `.proofline/s3/single-sandbox/operator/key-guard-amendment.json` | `6c2bb400b9a00637ae0cff9b022e92c8b6fb58e375b387cbc021ffb3539649c5` |
| `.proofline/s3/guard-retest/operator/report.json` | `c11905c9735577871c9b87341c7c31e009ecbaebfaf5e5bd81bdd6fb27da0b55` |
| `.proofline/s3/guard-retest/operator/audit.json` | `adf396be444327a0b0f4bc8be9928bfaf16c5fadbe670169745d417ca080679b` |
| `.proofline/s3/single-sandbox/operator/paired-view.json` | `e1329ebc6f495298abc1caaf6cedc4b3d8cd68a6f298839fdc1f11b4fb0b1f18` |
| `.proofline/s3/final-summary/report.json` | `180f74276802d94aff7b16d5547666e6a63de146daec220c689bf3eacd434092` |
| `.proofline/s3/final-host-s2-readback/report.json` | `19204af9db9cd3f6601ea640c0c7761c7fdf09b7977a10734e14d4d4e26a660f` |

## Earlier recorded results

The original 20 assignments and five supported-source P2P follow-ups all have
explicit outcomes. The first setup trial retains five attempted assignments
(including its interrupted sixth dispatch) and 15 unstarted assignments. The
skill-discovery startup failure retains all 20 unstarted assignments. Nothing
was discarded after inspecting quality scores.

| Fixed case | Ordinary agent | Agent plus review | Current P2P, supported source | Proofline |
| --- | --- | --- | --- | --- |
| missing-validation | Accepted correctly | Accepted correctly | Failed: host preflight | Accepted correctly |
| correct-alternative | Accepted correctly | Accepted correctly | Failed: host preflight | Accepted correctly |
| green-tests-defect | Accepted correctly | Accepted correctly | Failed: host preflight | Accepted correctly |
| false-scope-change | Accepted correctly | Accepted correctly | Failed: host preflight | Accepted correctly |
| source-omission | Failed: omission identified | Failed: omission identified | Failed: host preflight; omission untested | Failed: INPUT NOT READY |

The three non-P2P cohorts produced four valid deliveries each. Their omission
controls explicitly identified the missing original exact-preservation promise;
the working code did not establish a valid agreement. All stopped at the
implementer, so this control dispatched no subsequent reviewer or prover.
S2 separately demonstrated fresh independent omission judgments in both roles.
The fixed oracle passed all four sanity controls and made 551 protected CLI
observations in the main comparison and supported P2P follow-up (76 controls,
380 original-assignment observations, 95 follow-up observations). All four
accepted Proofline records still revalidate as LOCAL ACCEPTED. The main run's
27 native threads and P2P's five follow-up threads are distinct.

Actual P2P admitted each supported-source invocation and dispatched its own
`preflight-1`, with real configured `gpt-6.1-sol` / `high` responses. All five
responses were rejected by its unchanged permission-boundary validator. They
report `sandbox-exec: sandbox_apply: Operation not permitted`; their native
event streams contain no executed-command receipts establishing the probe.
No implementation, review, proof, repair or accepted delivery was established.
An independent zero-model nested-sandbox check succeeded. This establishes a
host/transport qualification failure, not its OS root cause or a P2P product
defect. The benchmark's private-read canaries passed. The no-daemon enclosing
sandbox and P2P's legacy workspace-write launcher remain a compatibility limit;
they were not replaced with a different pipeline to obtain a passing score.
No P2P resume, host installation, or controller repair was attempted.

The raw follow-up scorer initially labeled the unchanged correct alternative
FALSE BLOCKED because it mistook completed preflight for product judgment.
A zero-model classification audit records it as FAILED at host preflight,
retaining the original raw label and native receipts. Completed preflight or a
rejected report cannot count as observed product judgment. The resulting table
has no observed false acceptance and no established product false blocking;
P2P's omitted-source control was not exercised. Its small elapsed time is not a
successful-delivery speed measurement.

## Earlier costs and limits

These cumulative costs include both setup trials, all unsuccessful invocations,
and the supported-source follow-up. Delivery time includes each method's own
setup and stages; separate private-oracle scoring and shared setup are included
in campaign wall time. Known subtotals are lower bounds when anything is missing.

| Cohort | Native dispatches | Qualified valid deliveries | All independently satisfactory deliveries | Known delivery seconds | Seconds per satisfactory delivery | Known reviewer / prover seconds |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Ordinary agent | 7 | 4 | 4 | 583.338 | Unknown; known subtotal 145.835 per delivery | Neither role executed |
| Agent plus review | 10 | 4 | 4 | 949.783 | 237.446 | 399.412 / prover not executed |
| Current P2P | 5, all preflight | 0 | 0 | 179.480 | Unavailable: zero deliveries | Neither role executed |
| Proofline | 16 | 4 | 5 | 1859.902 | 371.980 | 556.309 / 773.048 |

Proofline's fifth independently satisfactory delivery is the original setup
trial's first-case success. It remains excluded from the paired quality table
but included in actual cost and delivery accounting. Dividing its entire
campaign cost only by the four qualified comparison deliveries gives 464.975
seconds. The ordinary agent's interrupted dispatch has unknown duration and
usage, so its full ratio is unknown. None of these ratios measures upstream
planning, human coordination, or a production pilot.

| Cohort | Usage observed / unknown stages | Known input tokens | Cached input tokens included in input | Known output tokens |
| --- | --- | ---: | ---: | ---: |
| Ordinary agent | 6 / 1 | 474090 | 362880 | 15747 |
| Agent plus review | 10 / 0 | 903454 | 677760 | 25804 |
| Current P2P | 5 / 0 | 117488 | 88576 | 1732 |
| Proofline | 16 / 0 | 1629365 | 1280384 | 48544 |

Campaign total: 38 dispatches, usage observed for 37 and unknown for one. Known
usage is 3124397 input tokens (2409600 cached) and 91827 output tokens. Monetary
cost, human attention and upstream planning cost are unknown. Recorded campaign
wall time is at least 3729.999 seconds; the skill-discovery startup duration is
unknown, so full campaign time is unknown. The main comparison used 2972.701
seconds including 15.944 shared-setup seconds; the P2P follow-up used 189.355.
The initiating agent stopped the first setup trial and corrected its ID/citation
setup, package lookup, source filename, external-runtime collection, and
preflight classification. No further per-case user decision was requested;
intervention/preparation attention was not timed.

The largest observed delivery overhead among working cohorts is Proofline's
fresh review and proof: 1086.887 seconds in the qualified comparison, compared
with 399.412 reviewer seconds for agent plus review. The one-shot ordinary agent
also solved these tiny tasks. This experiment demonstrates directional
mechanisms and their cost; it does not establish that extra stages improve
quality on representative work, that Proofline beats working P2P, or the design's
25% pilot target. P2P needs an independently qualified compatible host/transport
before a paired quality or throughput conclusion. S4–S6 remain deferred.

## Reproduction and evidence

Run only on the qualified native host, after S2's live gate:

```sh
python3 -B checks/s3_compare.py --s2-record .proofline/s2-live/final-audit/report.json \
  --p2p-repo /path/to/current/promise-to-proof --output .proofline/s3/new-comparison
```

The runner uses the supported source basename, external-runtime collector and
final single-profile key guard. It archives the transport, controller repair,
Proofline sources and repository patches, and retains requested/effective native
argv. The historical repeat used its archived 180-second runner. The new
declaration above records the subsequent handoff guidance and 240-second limit;
those changes do not alter any historical result.
`--p2p-followup` is restricted to the five retained
source-location admission failures; it checks unchanged source, seed trees,
plan, oracle, P2P commit and model preferences before new comparison work.
`--summary` takes final accounting records and writes a fresh cost summary,
without model calls. The initial and follow-up runner snapshots are retained
in their private operator directories; their hashes match the predeclarations.
Classification fixes change accounting copies, never the raw model records.

| Retained ignored artifact | SHA-256 |
| --- | --- |
| `.proofline/s3/qualified/operator/report.json` | `af7b506901faaffe32b25967e5596630fbbca8474e44041f3932f4a62c0f0abf` |
| `.proofline/s3/p2p-supported/operator/report.json` | `8443c6a08be40e8ac6993a0f14d8fa3c845f0bff3473f9bd04b739eca68af7a6` |
| `.proofline/s3/summary/report.json` | `8abd4dcb175a15c9254b82d06700d5fe11e5029a11d0699a192a5039ba948bf6` |

The earlier summary binds four accounting inputs by hash; the final summary
binds eight and reproduces byte-for-byte through `--summary`. Native attempt files and
failed reports remain in the recorded disposable P2P runtimes. Original P2P
checkout and the original S2 source/approval artifacts remain unchanged; the
final zero-model S2 readback is OBSERVED. These local artifacts are not shipped
as product files. All eight retained accepted Proofline records revalidate;
S2's original source and approval still pass readback. Final deterministic and
native-enabled regression verification: 74 tests, 72 passed and two Linux-specific
skips. The earlier 73-test verification remains historical.
