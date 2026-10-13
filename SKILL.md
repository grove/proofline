---
name: proofline
description: One bounded coding attempt and explicit executable checks on a frozen local candidate, without universal correctness certification.
---

Use the [supported local runner](proofline.py) `run` command. It currently
requires **macOS**, Python 3.11+, authenticated **Codex CLI 0.162.1**, and
a **clean Git repository**. Do not launch historical `deliver` or `resume`;
they are no longer supported commands. **Check-only is planned (#11), not
currently available.** Direct requests need no P2P/Intentline workflow.

Preserve the user's **entire original request** in a file outside product
changes. Select relevant project-native executable checks and store each
exact argv list in `checks.json`, also outside product changes. Do not
fabricate expectations, silently narrow requested behavior, or modify
unrelated user work. The runner creates an isolated candidate with the Git snapshot helper;
the source repository stays untouched.

```sh
/opt/homebrew/bin/python3.14 -B /absolute/path/to/proofline/proofline.py run \
  --repo /absolute/path/to/product \
  --source /absolute/path/to/source.md \
  --checks /absolute/path/to/checks.json \
  --seconds 900 --stage-seconds 600 --check-seconds 120
```

The coding agent owns strategy and self-checks. Proofline dispatches one
model attempt and runs the caller-selected commands against its frozen,
read-only candidate under native protection. All time counts toward the
episode budget. Linux offline CI does not establish a native macOS/Codex qualification.
No automatic AI reviewer/prover, correction, publication,
merge or deployment runs. Existing authorization rules still apply;
local checking never permits external mutations.

Use `proofline.py status <report.json>` to revalidate the receipts.
Report the exact candidate, actual named check results and uncovered
requirements. `CHECKS PASSED` means only that listed commands exited
successfully. Distinguish `CHECKS FAILED`, `CHECKS UNAVAILABLE`,
`EXECUTION UNAVAILABLE`, and `STALE CHECKS`. Never call checks
full-promise certification or claim a PR/merge occurred.

The [vNext contract](DESIGN.md) and [open issues](https://github.com/grove/proofline/issues)
prioritize zero-extra-model check-only use and useful failure feedback.
New mandatory stages must demonstrate improvements in independently
correct deliveries that justify their latency, cost and blocking risk.
