"""Keep all eight slots, source disputes and unknown resource observations."""
from collections import Counter

from evaluation.sol_luna_host.accounting import completed_usage

TOKENS = ('input_tokens', 'cached_input_tokens', 'output_tokens')


def total(values):
    return sum(values) if all(value is not None for value in values) else None


def summarize(rows):
    expected = {(task, arm) for task in (12, 28, 41, 42) for arm in ('medium', 'high')}
    if len(rows) != 8 or {(row['task'], row['arm']) for row in rows} != expected:
        raise ValueError('All eight unique assigned slots are required')
    result = {'assigned': 8, 'arms': {}, 'paired': [], 'recommendation': 'INCONCLUSIVE',
              'billing_usd': None, 'organizer_tokens': None, 'human_active_seconds': None,
              'limit': 'Four retrospective public repository requests, one repetition. Neither an all-correct ceiling nor this small cohort establishes general reliability.'}
    for arm in ('medium', 'high'):
        assigned = [row for row in rows if row['arm'] == arm]
        attempted = [row for row in assigned if row.get('attempted')]
        stages = [stage for row in assigned for stage in row['stages']]
        usages = []
        tools = []
        for stage in stages:
            usage = stage.get('usage')
            if usage is None:
                observed = completed_usage(stage)
                if observed:
                    usage = observed[1]
            if usage is not None and (any(type(usage.get(k)) is not int or usage[k] < 0 for k in TOKENS)
                                      or usage['cached_input_tokens'] > usage['input_tokens']):
                raise ValueError('Invalid native token observations')
            usages.append(usage)
            tools.append(stage.get('tool_executions', len(stage['commands']) if 'commands' in stage else None))
        tokens = {key: total([usage.get(key) if usage else None for usage in usages]) for key in TOKENS}
        tokens['uncached_input_tokens'] = (tokens['input_tokens']-tokens['cached_input_tokens']
            if tokens['input_tokens'] is not None and tokens['cached_input_tokens'] is not None else None)
        correct = sum(row['status'] == 'CORRECT_DELIVERY' for row in assigned)
        elapsed = total([row.get('total_seconds') for row in attempted]) if attempted else None
        result['arms'][arm] = {'assigned': 4, 'attempted': len(attempted),
            'outcomes': dict(Counter(row['status'] for row in assigned)),
            'correct_deliveries': correct, 'confirmed_defects': sum(row['status'] == 'FALSE_ACCEPTANCE' or
                (row.get('source_audit') or {}).get('verdict') == 'DEFECT' for row in assigned),
            'disputed': sum(row['status'] == 'DISPUTED' for row in assigned),
            'false_acceptance': sum(row['status'] == 'FALSE_ACCEPTANCE' for row in assigned),
            'false_blocking': sum(row['status'] == 'CORRECT_BUT_BLOCKED' for row in assigned),
            'green_test_omissions': sum((row.get('source_audit') or {}).get('verdict') == 'DEFECT' and
                                       row.get('repository_tests_passed') is True for row in assigned),
            'elapsed_seconds': elapsed, 'seconds_per_correct_delivery': elapsed/correct if elapsed is not None and correct else None,
            'native_turns': len(stages), 'tool_executions': total(tools), 'tokens': tokens,
            'tokens_per_correct_delivery': {key: value/correct if value is not None and correct else None for key, value in tokens.items()},
            'dollars_per_correct_delivery': None}
    for task in (12, 28, 41, 42):
        pair = {row['arm']: row for row in rows if row['task'] == task}
        resolved = all(row['status'] in ('CORRECT_DELIVERY', 'FALSE_ACCEPTANCE', 'CORRECT_BUT_BLOCKED', 'DEFECTIVE_DELIVERY') for row in pair.values())
        result['paired'].append({'task': task, 'medium': pair['medium']['status'], 'high': pair['high']['status'],
            'correct_delivery_difference': int(pair['medium']['status'] == 'CORRECT_DELIVERY')-int(pair['high']['status'] == 'CORRECT_DELIVERY') if resolved else None,
            'elapsed_seconds_difference': pair['medium']['total_seconds']-pair['high']['total_seconds'] if resolved else None})
    if all(pair['correct_delivery_difference'] is not None for pair in result['paired']):
        medium, high = (result['arms'][arm] for arm in ('medium', 'high'))
        if medium['correct_deliveries'] == high['correct_deliveries'] and medium['correct_deliveries']:
            if medium['seconds_per_correct_delivery'] < high['seconds_per_correct_delivery']:
                result['recommendation'] = 'MEDIUM: candidate default for similarly scoped work; general reliability and dollar savings remain inconclusive'
            elif high['seconds_per_correct_delivery'] < medium['seconds_per_correct_delivery']:
                result['recommendation'] = 'HIGH: lower observed elapsed time per source-correct delivery on this cohort; broader evidence remains inconclusive'
        elif high['correct_deliveries'] > medium['correct_deliveries']:
            result['recommendation'] = 'HIGH: more source-correct deliveries on this cohort; smallest follow-up is a fresh bounded study of same-Luna checks/feedback if medium defects are confirmed'
    return result
