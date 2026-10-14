Compare Luna:medium versus Luna:high on source-validated real coding tasks

## Why

The completed [#32 / PR #33](https://github.com/grove/proofline/pull/33) pilot had **4/4 correct Luna:high** deliveries; [#34 / PR #35](https://github.com/grove/proofline/pull/35) stopped after **five confirmed-correct Luna:high candidates and one disputed oracle grade**. There were no confirmed naturally occurring defects to repair. Mandatory Sol assistance added overhead without observed delivery gain on the prior cohort.

The near-term, cost-effective question is therefore simpler: **Does GPT-6 Luna:`medium` produce sufficiently reliable implementations at lower end-to-end time/model usage than Luna:`high` on genuinely representative work?** Do not assume that medium is cheaper per correct delivery before measuring it.

## Newly verified real-host blockers (from #37)

Two narrowly scoped product/qualification defects were observed on real PR heads. Track and resolve them separately instead of expanding this benchmark runner:

- [#41 — Homebrew Python receipt alias mismatch](https://github.com/grove/proofline/issues/41): **qualify or fix before a live #38 oracle comparison** so a successfully executed child suite cannot be mislabeled `ORACLE UNAVAILABLE`. Preserve exact trusted argv binding, not permissive alias acceptance.
- [#42 — Safe skill-discovery directory symlinks](https://github.com/grove/proofline/issues/42): resolve before using the existing Proofline checkout or real candidate repos with its `.agents`/`.claude` directory links as model-frozen task inputs or check targets. This should **not** become an unrelated prerequisite if the fresh primary medium/high tasks have no such links, since that comparison does not require mandatory Proofline checks.

Keep [#36](https://github.com/grove/proofline/issues/36)'s source-faithful independent-oracle preflight mandatory before any model dispatch. Preserve the small two-arm study and explicit new spending-authorization requirement.

## Dependencies and narrow scope

- **First:** satisfy [#36](https://github.com/grove/proofline/issues/36)'s source-faithful oracle checks, including correct treatment of unspecified exception classes and repository-test subprocess outcomes. No live model calls before this preflight succeeds.
- Prefer **4–6 new real repository tasks** identified through [#37](https://github.com/grove/proofline/issues/37) or an equivalent well-grounded selection of actual user-requested changes. Include multi-file changes, regression/compatibility obligations, negative cases and one smaller control. Do **not** reuse exposed #16/#32/#34 task/solution/hidden-oracle pairs, or select tasks after observing a model's failures.
- Freeze the complete original requests, actual base commits, starting files, independent source-grounded expectations (including acceptable alternatives/ambiguities), normal visible tests, model/host/reasoning IDs, prompts, matched order, grading, budgets, exposure and stop rules **before** any live execution. Qualify independent reference/alternative/defective controls before model spending. No worker receives private grader expectations or another arm's results.
- **Primary study: exactly two ordinary coding arms** on the same 4–6 tasks: **Luna:medium** and **Luna:high**. Same supported native host, initial project bytes, complete source request, allowed tools and cumulative per-assignment budget. Agents self-test normally. No Sol planner/verifier, mandatory Proofline, new corrective supervisor or reasoning escalation inside an assignment.
- Cap the initial comparison at **8–12 live implementation assignments, one coding turn each**, plus explicitly bounded no-model preflight. Predeclare and get **separate user authorization** for the exact frozen study and actual model/compute spending. Do not reuse #34 authorization, restart failed runs, change models mid-cohort or pool historical outcomes.
- Reuse the existing Proofline/native evaluation, snapshots, receipts and minimal reporting. **No new runner framework** or new product workflow. Where feasible, separately dogfood `proofline-check` in the ordinary development process through #37; do not confound this primary model-effort comparison by giving only one model extra tests or feedback.
- If medium makes **confirmed source-grounded defects**, retain exact initial candidate and error evidence and recommend a **separate, bounded experiment** comparing ordinary checks versus optional Proofline feedback and at most one same-Luna correction on a **fresh predeclared cohort**. Do not automatically add Sol, change this study's arms, cherry-pick failed tasks or claim that a subsequent repair is independent of this model comparison.

## Measurements and acceptance

- [ ] Independently grade **all assigned** medium/high deliveries on material source obligations; report true successes, genuine defects, unsupported/disputed expectations, false acceptance/blocking, green-test omissions, unavailable and unexecuted attempts. A disputed oracle must not count as a verified product defect.
- [ ] Report per-task and paired independently correct deliveries, full elapsed seconds, model turns/tools, exact Luna input/cached/uncached/output token categories, initial self-checking, grading/preparation overhead and human work where measured. Do not double-count cached input.
- [ ] Report **total observed dollar charges only if actually available**; otherwise keep dollars unknown and provide separately labeled token-price sensitivity or break-even conditions. Compare *resources per independently correct delivery*, not merely per-turn token count or per-token pricing.
- [ ] Clearly label any all-correct ceiling or too-small sample as **inconclusive about general reliability**. If medium matches high on the chosen tasks and measurably saves resources, identify it as a *candidate default for similarly scoped work*, not an unconditional switch.
- [ ] Publish a concise **medium / high / inconclusive** recommendation with the smallest justified follow-up, **without implementing model routing, a mandatory reviewer or extra verification machinery**.

## Definition of done

One **executed, source-valid, small matched medium/high comparison**, or a transparent qualified stop if model access/authorization is unavailable; retained exact inputs and evidence, honest complete denominators, meaningful end-to-end resource accounting and an explicit decision. Create a PR; **do not merge without user approval**.

**Priority:** After #36 oracle qualification; reuse lessons and genuine tasks from #37 where feasible.