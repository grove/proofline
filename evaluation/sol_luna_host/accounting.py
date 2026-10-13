"""Post-process cumulative native usage; never alter frozen execution evidence."""
from copy import deepcopy
import json
from pathlib import Path

from checks import codex_live, host_probe
from evaluation.sol_luna import report


def completed_usage(stage):
    """Usage observations survive a killed CLI; they never upgrade its status."""
    receipt = stage.get('receipt', {})
    if not receipt.get('events_path'):
        return None
    with Path(receipt['events_path']).open('rb') as stream:
        raw = stream.read(codex_live.MAX_EVENTS_BYTES+1)
    if len(raw) > codex_live.MAX_EVENTS_BYTES or host_probe.sha256(raw) != receipt.get('events.jsonl_sha256'):
        raise ValueError('Native usage evidence changed or oversized')
    events = [json.loads(line) for line in raw.splitlines()]
    threads = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
    completed = [e for e in events if e.get('type') == 'turn.completed']
    if len(threads) != 1 or len(completed) != 1:
        return None
    return threads[0], completed[0].get('usage')


def normalize(result):
    result = deepcopy(result)
    previous = {}
    identities = {}
    groups = [result.get('handoff_qualification') or {}, *result['assignments']]
    for group in groups:
        for stage in group.get('stages', []):
            usage = stage.get('usage')
            thread = stage.get('thread_id')
            if usage is None:
                observed = completed_usage(stage)
                if observed:
                    thread, usage = observed
                    stage['thread_id'] = thread
                    stage['accounting_observation'] = 'Completed-turn usage; invocation status remains unchanged'
            stage['observed_session_usage'] = deepcopy(usage)
            stage['usage_basis'] = 'Delta of completed native session totals; raw receipt unchanged'
            if usage is None:
                if thread:
                    previous[thread] = None
                continue
            if not isinstance(thread, str) or not thread:
                raise ValueError('Completed usage requires native thread identity')
            if (not isinstance(usage, dict) or not all(k in usage for k in report.TOKENS) or
                    any(type(v) is not int or v < 0 for v in usage.values()) or
                    usage['cached_input_tokens'] > usage['input_tokens']):
                raise ValueError('Invalid native cumulative usage')
            identity = (stage['model'], stage['reasoning_effort'])
            if thread in identities and identities[thread] != identity:
                raise ValueError('Native thread model/effort changed')
            identities[thread] = identity
            if thread in previous:
                baseline = previous[thread]
            else:
                baseline = None if stage['stage'] == 'correction' else {k: 0 for k in usage}
            if baseline is None:
                stage['usage'] = None
            else:
                if set(baseline) != set(usage) or any(usage[k] < baseline[k] for k in usage):
                    raise ValueError('Native cumulative usage reset or schema changed')
                stage['usage'] = {k: usage[k]-baseline[k] for k in usage}
                if stage['usage']['cached_input_tokens'] > stage['usage']['input_tokens']:
                    raise ValueError('Invalid native incremental cache usage')
            previous[thread] = usage
    result['metrics'] = report.summarize(result['assignments'])
    return result
