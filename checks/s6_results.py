#!/usr/bin/env python3
"""Publish measured S6 readback, including the cost of superseded protocol trials."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6


def resources(reports):
    attempts = []
    ids = set()
    for report in reports:
        for assignment in report['assignments']:
            if assignment.get('carried_from') or assignment['outcome'] == 'NOT EXECUTED':
                continue
            if assignment['id'] in ids:
                raise ValueError('Duplicate original episode: ' + assignment['id'])
            ids.add(assignment['id'])
            attempts.append(assignment)
    stages = []
    calls = 0
    for assignment in attempts:
        planning = assignment.get('planning_stages', [])
        delivery = s6.account_delivery(assignment.get('delivery', {}))
        stages += planning + delivery.get('stages', [])
        calls += len(planning) + delivery.get('model_dispatches', len(delivery.get('stages', [])))
    tokens, missing = s6.stage_usage(stages, calls)
    return {'original_episodes': len(attempts), 'known_native_dispatches': calls,
            'known_workflow_seconds': sum(a.get('end_to_end_seconds', 0) for a in attempts),
            'unknown_time_episodes': sum(a.get('end_to_end_seconds') is None for a in attempts),
            'known_episode_observation_seconds': sum(a.get('total_observation_seconds', 0) for a in attempts),
            'unknown_observation_time_episodes': sum(a.get('total_observation_seconds') is None for a in attempts),
            'known_tokens': tokens, 'unknown_usage_dispatches': missing,
            'human_study_attention_seconds': None, 'cost_usd': None}


def render(campaign, readback, preliminary, challenges):
    manifest, original = s6.verify_declaration(campaign, runtime=False)
    report = json.loads(readback.read_text()) if readback else original
    if report['manifest_sha256'] != original['manifest_sha256']:
        raise ValueError('Readback is for a different declaration')
    rates = json.loads((campaign / 'operator/rates.json').read_text())
    summary = s6.summarize(manifest, report, rates)
    prior = [s6.verify_declaration(path, runtime=False)[1] for path in preliminary]
    total = resources(prior + [original])
    amended_protocol = bool(manifest.get('study_amendment') or preliminary)
    false_proofline = sum(a['cohort'] == 'proofline' and a['outcome'] == 'FALSE ACCEPTED' for a in report['assignments'])
    def display(value):
        return 'unknown' if value is None else f'{value:.1f}' if isinstance(value, float) else str(value)
    counts = Counter(a['outcome'] for a in report['assignments'])
    lines = ['# S6 — Measured results', '', f'Final population: **{report["status"]}**. Decision: **{summary["decision"]}**.', '',
        f'Of {len(report["assignments"])} assigned cases, {len(report["assignments"])-counts["NOT EXECUTED"]} executed and {counts["NOT EXECUTED"]} remain unexecuted under the trust stop. Outcomes: `{json.dumps(dict(counts), sort_keys=True)}`. Unexecuted cases remain in the assigned denominator; this is not a completed efficacy comparison.', '',
        'These are actual local native runs, not illustrative benchmark figures. All methods were judged against the original source. Finite probes establish observed correctness; they cannot prove absence of every defect.', '',
        '## Results across 20 tasks', '',
        '| Model / approach | Correct deliveries | False acceptances | Terminal false blocking | Median successful seconds | All-attempt seconds / correct | Correct / workflow hour | All-attempt tokens / correct |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for model, cohort in [('sol', 'ordinary-agent'), ('sol', 'agent-plus-review'), ('sol', 'p2p'), ('sol', 'proofline'), ('luna', 'ordinary-agent'), ('luna', 'proofline')]:
        assignments = [a for a in report['assignments'] if a['model'] == model and a['cohort'] == cohort]
        correct = sum(a['outcome'] == 'ACCEPTED CORRECTLY' for a in assignments)
        rows = [v for k, v in summary['cohorts'].items() if k.startswith(model + '/') and k.endswith('/' + cohort)]
        seconds = sum(r['known_seconds'] for r in rows)
        complete = all(not r['unknown_seconds'] and not r['outcomes'].get('NOT EXECUTED') for r in rows)
        tokens = sum(r['known_tokens']['input_tokens'] + r['known_tokens']['output_tokens'] for r in rows)
        successful = [a['end_to_end_seconds'] for a in assignments if a['outcome'] == 'ACCEPTED CORRECTLY']
        values = [f'{model}/{cohort}', f'{correct}/{len(assignments)}', sum(r['false_acceptances'] for r in rows),
                  sum(r['false_blocked'] for r in rows), statistics.median(successful) if successful else None,
                  seconds/correct if correct and complete else None, 3600*correct/seconds if seconds and complete else None,
                  tokens/correct if correct and complete and not any(r['unknown_usage_calls'] for r in rows) else None]
        lines.append('| ' + ' | '.join(map(display, values)) + ' |')
    money = 'Dollar rates were not declared, so correct deliveries per dollar and dollar costs are **unknown**.' if not rates else 'Declared token-price estimates appear in the detailed ledger where population and usage are complete; unreported tool charges remain unknown.'
    lines += ['', 'Costs per successful delivery charge failed attempts to the denominator. A workflow hour sums elapsed episodes; it is not parallel wall time. Cached input is already included in input tokens. ' + money + ' Internal provider request counts and unreported tool charges are unavailable.', '',
        'All automatic task episodes record zero task-specific human interventions. Corpus authoring, protocol repair and operator attention were not timed; study autonomy and full human cost remain unknown. Shared-plan authoring cost is also unknown.', '',
        '## Provenance and protocol amendments', '',
        f'- Final declaration SHA-256: `{original["manifest_sha256"]}`.',
        f'- Exact coding models/settings: `{json.dumps(manifest["models"], sort_keys=True)}`.',
        '- Twenty component tasks, ten raw requests and ten shared plans per arm; eight tasks designated held-out before tuning. One host and one repetition. Only the local delivery target was authorized.',
        '- Forty-six independent controls passed before task dispatch. Candidate tests never supplied the answer key. Those finite probes did not establish complete source coverage.',
        '- Protocol amendments and retained prior results are recorded in the frozen study amendment. Superseded trials are included below; valid observations are carried by exact artifact hash.' if amended_protocol else '- No amended comparison cohorts were supplied to this report.',
        f'- Uniform regression readback preserves original scores. Final false acceptances: {counts["FALSE ACCEPTED"]}, including {false_proofline} by Proofline. Post-declaration evaluator changes limit causal inference.' if report.get('supplemental_regression_readback') else '- No supplemental regression readback was supplied.',
        '- Raw receipts, rejected candidates, frozen runtimes, original scores, superseded trials and unexecuted assignments remain in the private evidence directory. No remote effects were performed.', '',
        '## Entire study resource ledger', '',
        f'Original episodes across retained and superseded campaigns: **{total["original_episodes"]}**. Carried copies are counted once. Known native stage dispatches: **{total["known_native_dispatches"]}**; unknown-usage dispatches: **{total["unknown_usage_dispatches"]}**.', '',
        f'Known summed workflow seconds: **{total["known_workflow_seconds"]:.1f}**. Token categories: `{json.dumps(total["known_tokens"], sort_keys=True)}`. Preparation, oracle controls, readback and controlled diagnostics are separate from this task-episode subtotal; human study time and dollar cost remain unknown.', '']
    lines += [f'Known episode observation seconds, including each worker\'s independent acceptance evaluation: **{total["known_episode_observation_seconds"]:.1f}**; episodes with unavailable observation time: **{total["unknown_observation_time_episodes"]}**. Known evaluator setup seconds across campaigns: **{sum(r.get("setup_seconds", 0) for r in prior + [original]):.1f}**. Stopped coordinator wall totals are unavailable; they are not replaced with zero.', '']
    lines += ['### Qualified executed subtotals', '',
              'These are consumed resources through the trust stop, including failures. Ratios describe executed cases only, not complete-population efficiency. Unknown usage means token totals are lower bounds. Methods have different task subsets executed; these ratios cannot establish superiority.', '',
              '| Model / approach | Executed / assigned | Known workflow seconds | Executed seconds / correct | Executed correct / hour | Native dispatches | Known input tokens | Known output tokens | Unknown usage dispatches | Correct but undelivered |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for model, cohort in [('sol', 'ordinary-agent'), ('sol', 'agent-plus-review'), ('sol', 'p2p'), ('sol', 'proofline'), ('luna', 'ordinary-agent'), ('luna', 'proofline')]:
        assignments = [a for a in report['assignments'] if a['model'] == model and a['cohort'] == cohort]
        rows = [v for k, v in summary['cohorts'].items() if k.startswith(model + '/') and k.endswith('/' + cohort)]
        seconds = sum(r['known_seconds'] for r in rows)
        correct = sum(r['satisfactory'] for r in rows)
        timed = all(a.get('end_to_end_seconds') is not None for a in assignments if a['outcome'] != 'NOT EXECUTED')
        values = [f'{model}/{cohort}', f'{sum(a["outcome"] != "NOT EXECUTED" for a in assignments)}/{len(assignments)}',
                  seconds, seconds/correct if correct and timed else None, 3600*correct/seconds if seconds and timed else None, sum(r['known_calls'] for r in rows),
                  sum(r['known_tokens']['input_tokens'] for r in rows), sum(r['known_tokens']['output_tokens'] for r in rows),
                  sum(r['unknown_usage_calls'] for r in rows), sum(r['correct_but_undelivered'] for r in rows)]
        lines.append('| ' + ' | '.join(map(display, values)) + ' |')
    lines += ['', f'Supplemental regression readback seconds: {display(report.get("regression_readback_seconds"))}. ISO ordinal-date interpretation: [NASA\'s ISO-8601 notation reference](https://science.data.nasa.gov/fits/documentation/iso-time). The requirement said ISO-8601, without narrowing it to calendar-date syntax.', '']
    rows = [v for k, v in summary['cohorts'].items() if k.endswith('/proofline')]
    lines += [f'Recoverable negative Proofline judgments independently scored: **{sum(r["rejection_judgments_scored"] for r in rows)}**; observed false rejections: **{sum(r["false_rejections"] for r in rows)}**; unscored structured negative judgments: **{sum(r["unscored_rejection_judgments"] for r in rows)}**. Unfinished verifier invocations are unavailable judgments, not confirmed true or false rejections.', '']
    if challenges:
        diagnostic = json.loads(challenges.read_text())
        lines += ['## Controlled recovery diagnostics', '', 'Host fault injections are excluded from natural task reliability rates.', '', '| Case | Result | Matched declared control | Implementations | Proofs |', '|---|---|---|---:|---:|']
        for case in diagnostic['cases']:
            lines.append(f'| {case["case"]} | {case["status"]} | {case["matched"]} | {case["implementations"]} | {case["proofs"]} |')
        calls = sum(c['dispatches'] for c in diagnostic['cases'])
        tokens, missing = s6.stage_usage([s for c in diagnostic['cases'] for s in c['stages']], calls)
        lines += ['', f'Diagnostic wall seconds: {diagnostic["elapsed_seconds"]:.1f}; native dispatches: {calls}; known tokens: `{json.dumps(tokens, sort_keys=True)}`; unknown usage dispatches: {missing}.', '']
    lines += ['## Paired complete ledger and input-specific hypotheses', '', s6.render(summary),
              '## Practical limits', '', 'This small amended component pilot does not establish performance on production repositories, other hosts, PR/merge delivery, unmeasured dollar prices, or the broader coding-model population. The Luna/Sol comparison reports these exact installed IDs and reasoning settings; it does not assume a price ordering. The 25% target remains a hypothesis wherever quality gates or paired successful populations are unavailable.']
    return '\n'.join(lines) + '\n', total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--readback', type=Path)
    parser.add_argument('--preliminary', type=Path, action='append', default=[])
    parser.add_argument('--challenges', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    text, total = render(args.campaign.resolve(), args.readback, args.preliminary, args.challenges)
    args.output.write_text(text)
    print(json.dumps(total, sort_keys=True))
