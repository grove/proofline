# Proofline #59 — read-only macOS OpenSSL startup file, tested with real RepoTend behavior

**Status: one narrow proposed permission change passed an actual GitHub-hosted macOS native check; awaiting independent Proofline maintainer review.** This is *not* a universal sandbox/security certification or a general release qualification.

- Issue: [Proofline #59](https://github.com/grove/proofline/issues/59)
- Previously blocked external product: [RepoTend #15](https://github.com/grove/repotend/issues/15), merged product [PR #16](https://github.com/grove/repotend/pull/16), historical native-unavailable evidence [PR #17](https://github.com/grove/repotend/pull/17)
- **Actual paired macOS run:** [39123644533](https://github.com/grove/proofline/actions/runs/39123644533), `push`, **completed success**, tested Proofline branch/workflow commit `f019a3927e5f4ce8a325b73edb2a28369265a95f`.
- [Actual 7-day artifact](https://github.com/grove/proofline/actions/runs/39123644533/artifacts/12134224973), ZIP SHA-256 `31f8eb7ce91eb2a647a2e6af4e12050dddb47a3a73df619c7c24c8410c1883e8`, expires **2026-10-25 11:32:59 UTC**. The archive was downloaded, hashed and independently read back by the investigation assistant; the raw `identity.json`, both positive native `report.json` files, three process receipts, paired startup receipts, actual check maps and exit codes matched the summary below. This is not an independently administered second human/operator review.
- Earlier, separate [successful nonpaired macOS run 39123425146](https://github.com/grove/proofline/actions/runs/39123425146) with [artifact 12134589755](https://github.com/grove/proofline/actions/runs/39123425146/artifacts/12134589755) yielded the same R1/R2 status results, on its own exact tested branch commit `3181f3cd7753b355f03af71c9ae9be4433b919ca`.

## What changed (pending approval)

In `checks/host_probe.py`'s `permission_profile`, on **macOS only**, add:

```python
openssl_config = Path("/System/Library/OpenSSL/openssl.cnf")
if openssl_config.is_file() and not openssl_config.is_symlink():
    profile["filesystem"][str(openssl_config)] = "read"
```

This is **one exact file with `read` only**, not its parent directory, `/System`, user files, network, execution, write or managed-configuration access. When that file is absent or a final-component symlink, no allowance is added. Existing network-disabled, scratch-write, source-read and private-deny rules are unchanged. Offline Python structural regressions exercise macOS, non-macOS, absent and symlink cases; they do not replace the native trial.

The real runner inspected that exact file: **regular file present**, `is_symlink: false`, resolved path identical, effective permission **`read`**. Other macOS versions/Node installations may have different runtime needs; parent-directory path resolution and broader attack surface still merit maintainer review.

## Paired Node startup diagnosis — same runner and sandbox profile

Both startup invocations used the same macOS 15.7.9 ARM64 host, Python 3.12.10, **Node 22.16.0**, native **Codex CLI 0.162.1**, same `sandbox_argv` construction, native executable, scratch, private paths, and `PATH`/`TMPDIR`. The sole profile difference was the exact OpenSSL configuration-file read above.

| Startup case | Actual result |
| --- | --- |
| **File explicitly allowed read-only** | Node exited **0**, stdout `NODE_BOOTSTRAPPED`, empty stderr |
| **Only that file entry removed** | Node exited **1**, empty stdout; stderr reports `BIO_new_file:Operation not permitted` opening `/System/Library/OpenSSL//openssl.cnf` |

Raw receipts: `node-startup-receipt.json`, `node-baseline-without-file-receipt.json`, and `paired-startup-comparison.json` in the artifact. This is stronger attribution than unrelated historical runs, but only for the tested host/runtime.

## Original, unchanged acceptance, candidate and native check identities

- RepoTend product implementation **frozen** at `ead77fde6a5a7ba33e54cc81deb76fced8dbc333` and tree **`544421686de4112ca1ac8bfb118cde750821e3ef`**. Proofline's synthetic snapshot commit `9d1060391fffd0466688b628ed605406613814eb` preserves that tree.
- **Original issue body `S1`** retained byte for byte from the [RepoTend #15 genuine Intentline producer archive](https://github.com/grove/repotend/blob/cba5c66754c4e27e06d29363c8a52060ccdc5c2e/docs/evidence/issue-15/README.md). SHA-256 `e1d61d83be03e8c442d05d1953bd2de47cd3a5a17a755c87d81826c56cb163f8`. Original exporter Intentline pin `25e926f57e69395193fc0ac258f9e6dd2332cb18`; **advisory, unapproved** complete single-S1 initial export, no new draft/adoption generated in this test.
- Proofline's source before this scoped patch was `8e117fff4de2459637fe7f74f47ab17fc3341d84`; the **actual patched tool tested** is `f019a3927e5f4ce8a325b73edb2a28369265a95f`, not that original pin. The final review branch will drop the temporary workflow and probe script; **do not claim later evidence/doc appendices were themselves native-checked**.
- Native selected command argv on the host:

```json
["/Users/runner/hostedtoolcache/node/22.16.0/arm64/bin/node", "--test", "--test-name-pattern=^R1", "test/audit-cli.test.mjs"]
["/Users/runner/hostedtoolcache/node/22.16.0/arm64/bin/node", "--test", "--test-name-pattern=^R2", "test/audit-cli.test.mjs"]
```

| Native selection on the *same frozen candidate and export* | Observed Proofline report and process results |
| --- | --- |
| R1 only, index 0, exact argv | `CHECKS PASSED`; R1 **LINKED CHECKS PASSED (limited evidence)**; R2 **NOT DEMONSTRATED**; one selected Node test executed, exit 0, TAP **1 passed / 0 failed** |
| R1 index 0 plus R2 index 1, exact argv | `CHECKS PASSED`; both R1 and R2 **LINKED CHECKS PASSED (limited evidence)**; both distinct Node tests executed, each exit 0, TAP **1 passed / 0 failed** |
| Deliberately bad R1 argv link | Real importer rejected, **exit 1**, no product report/selected command; correct export/records untouched |

Both genuine positive Proofline checks exited **0**, native `status --show-source` exited **0**, protected boundary canaries were **OBSERVED** in each check, model dispatches were **0**, original source/selected candidate/tree matched, and retained check stdout was complete (no stderr, truncation or timeout). The boundary observations retained denied private reads, source/target/receipt writes, chmod and loopback access, with scratch allowed. They establish only these canary properties, not a general security theorem.

The importer refusal demonstrates a correct mapping rejection but no product behavior. Original RepoTend ordinary CI tests (67 passed) remain distinct evidence. Even with the two native passes, **`coverage_completeness: UNKNOWN`**: full source inventory, all outcomes, other operating systems, remote policies and future candidate changes are not certified.

## Review and next decision

1. Independently review the exact permission difference and sandbox profile construction, including host path/symlink semantics and potential impacts on other native check runtimes.
2. Review the **raw** artifact (before expiry), source/export and selected check receipts rather than accepting this Markdown as proof. Confirm selected checks are meaningful behavioral assertions for R1/R2.
3. **Do not silently merge this security-boundary change**. The source patch and deterministic tests are proposed in Proofline for review; host behavior was tested on the immutable probe workflow revision above. No RepoTend/Foundryline tracker issues are automatically closed and no deployment, unsandboxed fallback or scheduled agent execution is enabled.

**Conclusion:** On the observed GitHub-hosted macOS runner, the single-file read allowance reproducibly removed Node's OpenSSL startup denial and enabled real, protected, candidate-bound R1/R2 selected checks. This qualifies **that specific experiment**, not universal sandbox isolation, total correctness or automatic acceptance.
