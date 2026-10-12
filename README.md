# Proofline

Let capable coding agents solve problems. Preserve the user's complete promise,
then independently review and challenge the exact result.

Proofline is an experiment in reducing delivery overhead while retaining
credible acceptance. [DESIGN.md](DESIGN.md) defines the product;
[IMPLEMENTATION.md](IMPLEMENTATION.md) orders its evidence gates.

## What works now

**Runnable direct local delivery through Codex.** One autonomous implementer
produces an isolated candidate; fresh independent review and behavioral proof
check the same frozen source, brief, comparison base, and candidate. Review runs
first and skips proof on a material blocker. Product defects return to the same
implementer session; evidence gaps get focused independent rechecks. The original repository is preserved.

| Slice | Status |
| --- | --- |
| S0 — Real host boundary | Demonstrated on macOS with seven fresh Codex invocations; correct and alternative implementations pass, seeded defect fails |
| S1 — Direct local delivery | Demonstrated on two small CLI tasks; source omissions and regressions rejected |
| S2 — Approved contracts | Real approved delivery and all input/source/regression/parent controls qualified; see the retained failed trials and narrow support boundary |
| S3 — Four-way comparison | Fixed 240-second repeat complete: ordinary/agent + review/Proofline delivered 4/4, P2P 2/4; all four rejected omitted source; earlier failures and costs retained |
| S4 — Bounded correction and resume | Native repair, unchanged evidence recovery and separate-process resume demonstrated; budget/stopping controls tested; see [S4 evidence](docs/S4-RECOVERY.md) |
| S5 — Authorized publication | Real PR/merge, separate-process recovery and exact-tree remote readback demonstrated in the authorized disposable repo; see [S5 evidence and limits](docs/S5-PUBLICATION.md) |
| S6 — Full pilot | Implemented: four approaches and Luna/Sol. Initial pilot stopped at the trust gate after a Proofline false acceptance: 69/120 assignments executed. See [measured results](docs/S6-RESULTS.md) and [protocol](docs/S6-PILOT.md) |

Read the [S0 results and failed experiments](docs/S0-CODEX-RUNNER.md),
[S1 evidence](docs/S1-DIRECT-DELIVERY.md), and
[S2 live evidence](docs/S2-LIVE-EVIDENCE.md) and [exact support boundary](docs/S2-CONTRACT-INPUT.md).
The [S3 comparison](docs/S3-COMPARISON.md) records every assignment, failed setup,
available usage and unknown cost; it makes no P2P performance advantage claim.
These results establish neither broad correctness nor a performance advantage.
The S6 ledger retains unavailable models, failed handoffs, budget exhaustion,
unexecuted assignments and unknown costs. The observed false acceptance requires
stronger verification before expansion; this pilot establishes no advantage.

## Deliver a direct request

The qualified runtime is **macOS, Codex CLI 0.162.1, Python 3.11+, Git**, with
existing Codex authentication. Live observations used Apple Silicon, Python
3.14.8, and the user's configured model and reasoning effort. Other hosts/CLI
versions need S0 qualification first. There are no third-party Python dependencies.
The macOS system Python may be too old; select a supported interpreter explicitly.

Use a clean Git repository with regular tracked files or relative aliases to
regular files inside the product. Save the original request
verbatim as `source.md` and a small source-grounded `brief.md` outside that
repository's tracked changes. A brief indexes every material promise with stable
IDs; it cannot narrow the source. For example:

```markdown
| ID | Required observable outcome |
| --- | --- |
| D1 | --version prints greet 1.0 and exits successfully without requiring a name. |
| D2 | Existing positional-name greetings, help, and argument errors are preserved. |
| D3 | No new dependencies or external effects. |
```

```sh
python3 -B /absolute/path/to/proofline/proofline.py deliver \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --brief /absolute/path/to/brief.md \
  --map 'Relevant commands, public interfaces, fixtures and environment gaps' \
  --seconds 900 --stage-seconds 240 --verification-reserve 120 --dispatches 12

python3 -B /absolute/path/to/proofline/proofline.py status /path/to/run/report.json
```

This consumes real model usage. A new ignored `.proofline/delivery/<id>/` directory
contains the candidate, protected role transcripts, and one `report.json` with
identities, observations, dispatches, elapsed time, and available usage. `--output`
selects a new directory; existing runs are never overwritten. Successful `status`
revalidates candidate identity and native receipt evidence before showing the
candidate path and commit. Exit `0` means the requested target is confirmed
(local by default); `2` means a gap, rejection, exhausted budget, stale evidence,
or invalid input.

**LOCAL ACCEPTED establishes local proof only.** With the default local target,
nothing is published or merged. Inspect the retained candidate and diff; the tool
does not copy changes into your original checkout. Optional GitHub targets require
an explicit initial repository/action grant; see below. There is no receipt-import command. Correction and focused verification
share the original time and dispatch limits. Implementation preserves the
configurable time reserve and two dispatches for independent checking; review
keeps half that time reserve for proof. Two consecutive correction rounds without
independent criterion improvement stop early. A productive third round may run
when the same episode still has verification capacity. Environment failures and
source/authority gaps are distinct from product defects.

Resume an interrupted episode with:

```sh
python3 -B /absolute/path/to/proofline/proofline.py resume /path/to/run/report.json
```

Resume validates retained receipts, source/contract authority, execution guidance
and candidate identity before continuing. It recovers a completed worker result
or confirms termination before replacing an incomplete verifier. A partial
implementation resumes its exact host-issued implementer session and must still
produce a valid handoff and fresh independent judgments. A running or uncertain
worker blocks redispatch; wait for termination and reconcile the recorded worker.
An episode lock prevents concurrent controllers. Downtime counts toward the
original elapsed budget, and interrupted dispatches remain consumed. Limits
cannot be reset or extended through `resume`. Historical S1/S3 records remain
inspectable but cannot be converted into S4 episodes. Terminal source gaps and
non-progress stops preserve work for an explicit next decision.

Models run under native permissions with read-only binding inputs and verifier
candidates, separate writable scratch, and protected host receipts. Network,
ambient shell credentials, MCP, plugins, web, delegation, and browser/computer
surfaces are unavailable. The native sandbox must initialize on the host; a
nested sandbox failure is an explicit gap, never a reason to disable isolation.

The boundary rejects external, directory, missing, cyclic and Git-metadata
symlinks. It does not support submodules, ignored local
dependencies, or tests that need to modify their source tree. Such tasks need a
qualified build/observation path. Supply exact interpreter/tool paths in the map
when macOS developer-tool discovery is unavailable inside the sandbox.

## Authorized PR and merge targets

S5's real authorized GitHub gate passed on a disposable repository: independent
local acceptance, PR publication, interruption/resume and verified merge. The live
case used an unprotected base with no CI; required-check/protection failures and
squash/rebase equivalence have deterministic coverage. See [S5 evidence and
limits](docs/S5-PUBLICATION.md). GitHub.com, installed `gh`, and existing host
Git/SSH and GitHub authentication are required for remote targets. Local delivery
needs neither GitHub nor remote credentials.

Only when the initial user request explicitly authorizes these exact effects,
add the following to `deliver` (direct and approved-contract paths both work):

```sh
--target pr-merged --github-repo OWNER/REPO --base main --branch proofline/task \
--authorize push --authorize create-pr --authorize merge \
--effect-reference 'Actual initial user authorization reference'
```

For `pr-created`, omit `--authorize merge`. `--merge-method` accepts `merge`
(default), `squash`, or `rebase`. These flags record a real grant; they cannot
invent one. No worker receives authority or credentials. There are no comment,
force-push, administrative bypass, deployment, or branch-deletion actions.

Publication uses the accepted product tree with the original source commit as
its parent. It never pushes the synthetic local history. The remote base must
still equal that original commit; moved bases, changed heads, conflicts and
protection failures preserve a precise partial result. GitHub checks and
protections must permit the merge. Current PR head/base and fetched Git trees
establish completion; transformed commits must have the same accepted tree.
`status` performs fresh read-only remote inspection and fails closed when it is
unavailable. `resume` reconciles any pending effect before continuing within the
original grant and cumulative budget. Local acceptance remains separately visible
if the remote target is incomplete. See [S5's boundary and qualification
command](docs/S5-PUBLICATION.md).

## Use as a Codex skill

[SKILL.md](SKILL.md) is the single `/proofline` entry point. Keep it with this
repository's scripts. To install a personal skill, link the whole checkout into
your Codex skills directory (choose an unused destination):

```sh
mkdir -p ~/.codex/skills
ln -s /absolute/path/to/proofline ~/.codex/skills/proofline
```

The skill prepares the source and brief in the initiating context, invokes the
runner, and checks the retained outcome. No P2P controller or planning agent is
required. Installation is optional; the CLI works directly.

## Check and qualify

Offline checks need only Python 3.11+ and Git:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B checks/fixtures/s0/test_oracle.py
```

Native qualification on an authenticated authorized host:

```sh
# Diagnostic only: zero model calls, always leaves S0 unqualified (exit 2).
python3 -B checks/host_probe.py
# Actual S0 qualification: seven fresh model calls.
python3 -B checks/s0_live.py --seconds 1500 --stage-seconds 240
# S1 negative judgment controls: four fresh model calls.
python3 -B checks/s1_judgments.py
# S2: actual approved delivery, retained child context, nine readiness and six judgment controls.
python3 -B checks/s2_live.py /path/to/approved-delivery/report.json \
  --parent-record /path/to/approved-child/report.json \
  --preservation-manifest /path/to/preserved-originals.json
# S3: predeclared four-way comparison; current P2P checkout required.
python3 -B checks/s3_compare.py --s2-record .proofline/s2-live/final-audit/report.json \
  --p2p-repo /path/to/promise-to-proof --output .proofline/s3/new-comparison
# S4: real seeded repair, evidence-only recovery and separate-process resume.
python3 -B checks/s4_live.py --output .proofline/s4-live/new-qualification
# S5: only in an explicitly authorized disposable remote repository.
python3 -B checks/s5_live.py --repo /path/to/clean-disposable-checkout \
  --github-repo OWNER/REPO --base main --branch proofline/s5-test \
  --authorize push --authorize create-pr --authorize merge \
  --effect-reference 'Actual user grant reference' --output .proofline/s5-live/new-run
# Native subprocess/permission regressions, no model calls.
PROOFLINE_NATIVE_TESTS=1 python3 -B -m unittest discover -s tests -v
# S6: freeze the complete assignment ledger before any task models run.
python3 -B checks/s6_compare.py declare --p2p-repo /path/to/promise-to-proof \
  --output .proofline/s6/new-pilot --sol gpt-6.1-sol --luna gpt-6-luna
python3 -B checks/s6_compare.py run .proofline/s6/new-pilot
python3 -B checks/s6_compare.py summary .proofline/s6/new-pilot
# Separate native recovery stresses, excluded from natural pilot quality rates.
python3 -B checks/s6_challenges.py --output .proofline/s6/new-challenges
```

Canaries use disposable files and a controlled local listener. Timeout or refused
connections do not count as network denial. Fixed answer keys stay outside worker
contexts. Raw evidence remains local and ignored by Git. The original PR's
[Linux NO-GO](docs/S0-HOST-FEASIBILITY.md) is retained; it describes that executor,
not all Linux hosts.

## License

[Apache License 2.0](LICENSE).
