"""Reuse protected #38 receipts and #36 source qualification; no model calls."""
import json
from pathlib import Path
import time

from checks import host_probe as host
from checks.native_checks import write_record
from evaluation.effort.oracle import visible
from evaluation.recovery.grader import invoke
from evaluation.source_preflight import qualify

HERE = Path(__file__).resolve().parent


def script(task):
    return (HERE / 'probes.py').read_text() + f'\nmain({task!r})\n'


def preflight(task):
    return qualify(json.loads((HERE / 'expectations.json').read_text())[str(task)],
                   source=(HERE / 'requests' / f'issue-{task}.md').read_bytes(),
                   oracle_text=script(task),
                   inventory=json.loads((HERE / 'inventory.json').read_text())[str(task)])


def observe(product, task, directory, *, trusted=False, seconds=120):
    started = time.monotonic()
    qualification = preflight(task)
    if qualification['status'] != 'QUALIFIED':
        raise ValueError('Source declaration not qualified: '+str(qualification['problems']))
    invocation = invoke(product, script(task), directory, trusted=trusted, seconds=seconds)
    observed = None
    try:
        if not invocation['available'] or invocation['receipt']['exit_code'] != 0:
            raise ValueError('Private probe did not complete')
        observed = json.loads(invocation['receipt']['stdout'])
        expected = list(json.loads((HERE / 'inventory.json').read_text())[str(task)])
        # native-check may be unknown before the more specific feature probes run.
        ids = [row['id'] for row in observed['cases']]
        if len(ids) != len(set(ids)) or not set(ids) <= set(expected):
            raise ValueError('Unexpected/duplicate observations')
        if any(row['passed'] is not None and type(row['passed']) is not bool for row in observed['cases']):
            raise ValueError('Invalid observation values')
        values = {row['id']: row['passed'] for row in observed['cases']}
        observed['cases'] = [{'id': identifier, 'passed': values.get(identifier)} for identifier in expected]
        observed['unknown'] = [row['id'] for row in observed['cases'] if row['passed'] is None]
        observed['passed'] = all(row['passed'] is True for row in observed['cases'])
        if host.sha256((directory / 'scratch/probe-receipts.json').read_bytes()) != observed['receipts_sha256']:
            raise ValueError('Process receipts changed')
    except (OSError, ValueError, KeyError, TypeError):
        invocation['available'] = False
    result = {'qualification': qualification, 'invocation': invocation, 'observed': observed,
              'elapsed_seconds': time.monotonic()-started, 'model_dispatches': 0,
              'status': 'SOURCE AUDIT REQUIRED' if invocation['available'] else 'ORACLE UNAVAILABLE',
              'correct': None}
    write_record(directory / 'observation.json', result)
    return result
