"""Issue #46 adapter over the immutable #38 execution/snapshot/receipt utilities.

prepare/controls never dispatch models. execute requires an exact-freeze review
and fresh bounded user authorization. Historical studies are never rewritten.
"""
import argparse
import json
from pathlib import Path
import platform
import sys
import time

from checks import candidate_snapshot as snapshots, codex_catalog, host_probe as host
from checks.native_checks import write_record
from evaluation.checklist import oracle
from evaluation.effort import report as old_report, study as existing
from evaluation.matched import study as boundaries
from evaluation.sol_luna.grader import bound_module

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STORE = ROOT / '.proofline/issue46-checklist-v1'
CODEX = existing.CODEX
TASKS = {10: 12, 11: 28, 14: 41, 13: 42}
ARMS = {'ordinary': 'medium', 'checklist': 'high'}


def protocol():
    return json.loads((HERE / 'protocol.json').read_text())


def identities():
    frozen = json.loads((HERE / 'FREEZE.json').read_text())
    expected = {'model': 'gpt-6-luna', 'model_reasoning_effort': 'medium'}
    if protocol()['models'] != {arm: expected for arm in ARMS}:
        raise ValueError('Both arms must use identical Luna:medium')
    for name, digest in frozen['sha256'].items():
        if host.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError('Frozen input drift: '+name)
    for name, path in [('codex', Path(CODEX).resolve()), ('python', Path(sys.executable).resolve())]:
        if host.sha256(path.read_bytes()) != frozen['runtime_sha256'][name]:
            raise ValueError('Frozen runtime drift: '+name)
    for task in TASKS:
        if oracle.preflight(task)['status'] != 'QUALIFIED':
            raise ValueError('Source-to-oracle declaration not qualified')
    return host.sha256((HERE / 'FREEZE.json').read_bytes())


def capture(repo, product):
    began = time.monotonic()
    result = existing.capture_with_history(repo, product)
    _, task, arm = repo.parent.name.split('-')
    distribution_started = time.monotonic()
    if arm == 'checklist':
        guidance = product.parent / 'guidance.md'
        guidance.write_text(guidance.read_text()+'\n'+
                            (HERE / 'checklists' / f'issue-{task}.md').read_text().replace(
                                f'../requests/issue-{task}.md', 'source.md'))
    path = STORE / 'distribution.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append({'task': int(task), 'arm': arm, 'capture_and_distribution_seconds': time.monotonic()-began,
                 'checklist_distribution_seconds': time.monotonic()-distribution_started if arm == 'checklist' else 0})
    write_record(path, rows)
    return result


def summarize(rows):
    # Reuse validated native token arithmetic and complete-slot accounting.
    mapped = [{**row, 'task': TASKS[row['task']], 'arm': ARMS[row['arm']]} for row in rows]
    result = old_report.summarize(mapped)
    result['arms'] = {arm: result['arms'][old] for arm, old in ARMS.items()}
    reverse = {value: key for key, value in TASKS.items()}
    for pair in result['paired']:
        pair['task'] = reverse[pair['task']]
        pair['ordinary'] = pair.pop('medium'); pair['checklist'] = pair.pop('high')
        for key in ('correct_delivery_difference', 'elapsed_seconds_difference'):
            if pair[key] is not None:
                pair[key] = -pair[key]  # B minus A, consistently.
    result.update(recommendation='INCONCLUSIVE',
                  recommendation_reason='Incomplete/very small one-attempt cohort or full preparation overhead unknown.',
                  checklist_preparation_tokens=None, checklist_preparation_seconds=None,
                  actual_billing='UNKNOWN')
    for arm in result['arms'].values():
        arm['total_seconds_per_correct_delivery_including_preparation'] = None
        arm['total_tokens_per_correct_delivery_including_preparation'] = None
    return result


def approved():
    freeze = identities()
    review_path = STORE / 'review.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else {}
    reviewer = review.get('reviewer')
    if (review.get('freeze_sha256') != freeze or review.get('decision') != 'QUALIFIED' or
            not isinstance(reviewer, str) or not reviewer.strip() or reviewer.startswith('organizer: /root') or
            review.get('independent_of_organizer_and_workers') is not True or
            review.get('reviewed_tasks') != list(TASKS) or not review.get('adjudication_reference')):
        raise ValueError('Independent exact-freeze source/checklist/inventory/control review required')
    approval_path = STORE / 'approval.json'
    approval = json.loads(approval_path.read_text()) if approval_path.exists() else {}
    if (approval.get('study_id') != protocol()['study_id'] or approval.get('freeze_sha256') != freeze or
            approval.get('max_native_dispatches') != 8 or approval.get('max_seconds') != 9600 or
            approval.get('host') != protocol()['host'] or approval.get('models') != protocol()['models'] or
            not isinstance(approval.get('user_authorization'), str) or not approval['user_authorization'].strip()):
        raise ValueError('Fresh explicit exact-freeze host/model/budget user authorization required')
    return approval


def variant(product, task, kind):
    for edit in json.loads((HERE / 'controls.json').read_text())[str(task)][kind]:
        path = product / edit['path']; raw = path.read_text()
        if raw.count(edit['old']) != edit['occurrences']:
            raise ValueError('Control patch drift')
        path.write_text(raw.replace(edit['old'], edit['new']))
    snapshots.freeze(product)


def controls():
    """Model-free execution qualification; semantic review remains a separate gate."""
    identities()
    directory = STORE / 'preflight'; directory.mkdir(exist_ok=False)
    began = time.monotonic(); rows = []
    deadline = began + protocol()['limits']['preflight_seconds'] - protocol()['prior_preflight_seconds']
    execution_qualified = False
    blocker = None
    try:
        if [platform.system(), platform.machine(), platform.mac_ver()[0], platform.python_version()] != protocol()['host']['versions']:
            raise ValueError('Frozen host unavailable')
        for task in protocol()['tasks']:
            for kind in ('reference', 'alternative', 'defective'):
                folder = directory / str(task['issue']) / kind
                product = existing.seed(task, folder / 'product', reference=True)
                if kind != 'reference':
                    variant(product, task['issue'], kind)
                observed = oracle.observe(product, task['issue'], folder / 'grade', trusted=True,
                                          seconds=min(120, deadline-time.monotonic()))
                available = observed['invocation']['available']
                target = {10: 'status-interface', 11: 'check-interface',
                          14: 'no-invented-expectation', 13: 'complete-source-display'}[task['issue']]
                cases = observed['observed']['cases'] if available else []
                matched = available and (not observed['observed']['unknown'] and
                          observed['observed']['passed'] if kind != 'defective' else
                          any(case['id'] == target and case['passed'] is False for case in cases))
                rows.append({'task': task['issue'], 'kind': kind, 'matched': matched,
                             'tree': host.git(product, 'rev-parse', 'HEAD^{tree}'), 'observation': observed})
                if not matched:
                    raise ValueError('Control mismatch/unavailability: '+str(task['issue'])+' '+kind)
        inputs = directory / 'boundary/inputs'; inputs.mkdir(parents=True)
        existing.seed(protocol()['tasks'][0], inputs / 'product')
        (inputs / 'product/app.py').write_text('Disposable worker boundary canary.\n')
        (inputs / 'source.md').write_bytes((HERE / 'requests/issue-10.md').read_bytes())
        (inputs / 'accepted-input.md').write_text('The complete original request controls.\n')
        (STORE / 'qualification').mkdir(exist_ok=True)
        (STORE / 'qualification/sibling.txt').write_text('Private sibling canary.\n')
        native = bound_module(boundaries, STORE=STORE)
        native.read_protocol = lambda: {'model': protocol()['models']['ordinary']}
        for worker in (False, True):
            native.boundary(inputs, directory / ('writable' if worker else 'readonly'), worker=worker)
        codex_catalog.readback(CODEX, HERE / 'model-catalog.json', protocol()['models'], directory)
        # Qualify the actual protected assembly, not only trusted control execution.
        reference = directory / '11/reference/product'
        protected = oracle.observe(reference, 11, directory / 'protected-reference',
                                   seconds=min(120, deadline-time.monotonic()))
        if not protected['invocation']['available'] or not protected['observed']['passed']:
            raise ValueError('Protected native CLI assembly unavailable; no live dispatch')
        results = json.loads((STORE / 'results.json').read_text())
        results['status'] = 'QUALIFIED_NOT_DISPATCHED'
        write_record(STORE / 'results.json', results)
        execution_qualified = True
    except BaseException as error:
        blocker = str(error)
        raise
    finally:
        if blocker:
            results = json.loads((STORE / 'results.json').read_text())
            results.update(status='STOPPED_NOT_QUALIFIED', blocker=blocker)
            write_record(STORE / 'results.json', results)
        write_record(directory / 'controls.json', {'controls': rows, 'all_matched': len(rows) == 12 and all(row['matched'] for row in rows),
                     'execution_qualified': execution_qualified, 'blocker': blocker,
                     'elapsed_seconds': time.monotonic()-began, 'model_dispatches': 0,
                     'scope': 'Authored public reference/alternative/defective controls; independent semantic adjudication still required.'})


def adapter():
    return bound_module(existing, HERE=HERE, STORE=STORE, protocol=protocol,
                        identities=identities, oracle=oracle, summarize=summarize,
                        approved=approved, capture_with_history=capture)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'controls', 'execute'))
    args = parser.parse_args()
    if args.action == 'controls':
        controls()
    else:
        getattr(adapter(), args.action)()


if __name__ == '__main__':
    main()
