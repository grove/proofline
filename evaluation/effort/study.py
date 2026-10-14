"""Small #38 adapter over existing snapshots, native coding and oracle receipts.

No planner, reviewer model, Proofline feedback or correction is dispatched.
Source audits are recorded separately from regression observations.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time

from checks import candidate_snapshot as snapshots, coding_attempt as coding
from checks import codex_catalog, codex_live as live, host_probe as host
from checks.native_checks import write_record
from evaluation.effort import oracle
from evaluation.effort.report import summarize
from evaluation.sol_luna.grader import bound_module
from evaluation.matched import study as boundary_checks

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STORE = ROOT / '.proofline/issue38-medium-high-v4'
CODEX = '/opt/homebrew/bin/codex'


def protocol():
    return json.loads((HERE / 'protocol.json').read_text())


def identities():
    frozen = json.loads((HERE / 'FREEZE.json').read_text())
    if protocol()['models'] != {'medium': {'model': 'gpt-6-luna', 'model_reasoning_effort': 'medium'},
                               'high': {'model': 'gpt-6-luna', 'model_reasoning_effort': 'high'}}:
        raise ValueError('Exactly the two ordinary Luna effort arms are required')
    for name, digest in frozen['sha256'].items():
        if host.sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError('Frozen input drift: '+name)
    for name, path in [('codex', Path(CODEX).resolve()), ('python', Path(sys.executable).resolve())]:
        if host.sha256(path.read_bytes()) != frozen['runtime_sha256'][name]:
            raise ValueError('Frozen runtime drift: '+name)
    for task in protocol()['tasks']:
        if oracle.preflight(task['issue'])['status'] != 'QUALIFIED':
            raise ValueError('Source-to-oracle preflight is not qualified')
    return host.sha256((HERE / 'FREEZE.json').read_bytes())


def seed(task, destination, *, reference=False):
    commit = task['reference_commit'] if reference else task['base_commit']
    destination.mkdir(parents=True, exist_ok=False)
    # Exact tracked Git blobs and modes; no checkout filters, history or export rules.
    for entry in filter(None, snapshots.git_bytes(ROOT, 'ls-tree', '-rz', commit).split(b'\0')):
        metadata, name = entry.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755', '120000'):
            raise ValueError('Unsupported initial Git entry')
        target = destination / os.fsdecode(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = snapshots.git_bytes(ROOT, 'cat-file', 'blob', oid)
        if mode == '120000':
            target.symlink_to(os.fsdecode(data))
        else:
            target.write_bytes(data)
            target.chmod(0o755 if mode == '100755' else 0o644)
    snapshots.validate_links(destination)
    host.git(destination, 'init', '--quiet', '--template=')
    snapshots.freeze(destination)
    expected = snapshots.git_bytes(ROOT, 'rev-parse', commit+'^{tree}').decode().strip()
    if host.git(destination, 'rev-parse', 'HEAD^{tree}') != expected:
        raise ValueError('Starting Git tree mismatch')
    restore_history(ROOT, destination, commit)
    return destination


def restore_history(source, product, commit):
    """Only reachable pre-base objects; archival tests need these, not later solutions."""
    def objects(repo, revision):
        return {line.split()[0] for line in snapshots.git_bytes(repo, 'rev-list', '--objects', revision).splitlines()}
    expected = objects(source, commit) | objects(product, 'HEAD')
    location = snapshots.git_bytes(source, 'rev-parse', '--git-path', 'objects').decode().strip()
    alternate = product / '.git/objects/info/alternates'
    alternate.parent.mkdir(exist_ok=True)
    alternate.write_text(str((source / location).resolve())+'\n')
    try:
        host.git(product, 'update-ref', 'refs/heads/frozen-history', commit)
        host.git(product, '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                 'repack', '--quiet', '-a', '-d', '-f')
    finally:
        alternate.unlink()
    actual = set(snapshots.git_bytes(product, 'cat-file', '--batch-all-objects', '--batch-check=%(objectname)').splitlines())
    if actual != expected:
        raise ValueError('History contains missing or post-base Git objects')
    host.git(product, 'update-ref', 'HEAD', commit)
    host.git(product, 'update-ref', '-d', 'refs/heads/frozen-history')
    host.git(product, 'reset', '--mixed', '--quiet', commit)
    if host.git(product, 'rev-parse', 'HEAD') != commit or host.git(product, 'status', '--porcelain'):
        raise ValueError('Actual base commit/history restoration failed')


def capture_with_history(repo, product):
    source_commit, _ = snapshots.capture_base(repo, product)
    restore_history(repo, product, source_commit)
    return source_commit, source_commit


def variant(product, task, kind):
    edits = json.loads((HERE / 'controls.json').read_text())[str(task)][kind]
    for edit in edits:
        path = product / edit['path']
        if 'symlink' in edit:
            path.unlink()
            path.symlink_to(edit['symlink'])
        else:
            raw = path.read_text()
            if raw.count(edit['old']) != 1:
                raise ValueError('Control patch does not match exact reference')
            path.write_text(raw.replace(edit['old'], edit['new']))
    snapshots.freeze(product)


def prepare():
    identities()
    STORE.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    spec = protocol()
    rows = []
    for task, order in zip(spec['tasks'], spec['order'], strict=True):
        for arm in order:
            product = seed(task, STORE / 'assignments' / f'{len(rows)+1:02d}-{task["issue"]}-{arm}' / 'seed')
            rows.append({'sequence': len(rows)+1, 'task': task['issue'], 'arm': arm,
                         'seed': str(product), 'seed_tree': host.git(product, 'rev-parse', 'HEAD^{tree}'),
                         'status': 'NOT_EXECUTED', 'stages': [], 'source_audit': None,
                         'total_seconds': None, 'billing_usd': None})
    result = {'study_id': spec['study_id'], 'freeze_sha256': identities(),
              'status': 'PREPARED_NOT_QUALIFIED', 'model_dispatches': 0,
              'reserved_native_dispatches': 0,
              'assignments': rows, 'preparation_seconds': time.monotonic()-began}
    write_record(STORE / 'results.json', result)


def qualify():
    freeze = identities()
    result = json.loads((STORE / 'results.json').read_text())
    if result['status'] != 'PREPARED_NOT_QUALIFIED' or result['freeze_sha256'] != freeze:
        raise ValueError('No qualification replay or declaration drift')
    began = time.monotonic()
    deadline = began + protocol()['limits']['preflight_seconds'] - protocol()['prior_preflight_seconds']
    controls = []
    try:
        expected = protocol()['host']
        if [platform.system(), platform.machine(), platform.mac_ver()[0], platform.python_version()] != expected['versions']:
            raise ValueError('Frozen host unavailable')
        version = host.run_command([CODEX, '--version'], STORE)
        if not host.succeeded(version) or version['stdout'].strip() != expected['codex']:
            raise ValueError('Frozen Codex unavailable')
        if host.auth_status(host.run_command([CODEX, 'login', 'status'], STORE)) != 'authenticated':
            raise ValueError('Existing model authentication unavailable')
        codex_catalog.readback(CODEX, HERE / 'model-catalog.json', protocol()['models'], STORE)
        for task in protocol()['tasks']:
            for kind in ('reference', 'alternative', 'defective'):
                folder = STORE / 'controls' / str(task['issue']) / kind
                product = seed(task, folder / 'product', reference=True)
                if kind != 'reference':
                    variant(product, task['issue'], kind)
                remaining = min(120, deadline-time.monotonic())
                if remaining <= 0:
                    raise ValueError('Bounded no-model qualification exhausted')
                observation = oracle.observe(product, task['issue'], folder / 'grade', seconds=remaining)
                expected_pass = kind != 'defective'
                matched = (observation['invocation']['available'] and
                           observation['observed']['passed'] == expected_pass)
                controls.append({'task': task['issue'], 'kind': kind, 'matched': matched,
                                 'tree': host.git(product, 'rev-parse', 'HEAD^{tree}'),
                                 'observation': str(folder / 'grade/observation.json')})
                write_record(STORE / 'controls.json', controls)
                if not matched:
                    raise ValueError('Control unavailable or disagrees: '+str(task['issue'])+' '+kind)
        # Coding transport qualification is process-only; private inputs are denied.
        folder = STORE / 'worker-boundary'; folder.mkdir()
        inputs = folder / 'inputs'; inputs.mkdir()
        product = seed(protocol()['tasks'][0], inputs / 'product')
        (inputs / 'source.md').write_bytes((HERE / 'requests/issue-12.md').read_bytes())
        (inputs / 'accepted-input.md').write_text('The complete original request controls.\n')
        target = product / 'proofline.py'
        with host.boundary_fixture(folder, inputs, target=target, denied_reads={
                'private_grader': str(HERE / 'oracle.py'), 'other_assignments': str(STORE / 'results.json')}) as (spec, before, private_before, network):
            receipt = host.run_command(host.sandbox_argv(CODEX, inputs, folder/'scratch', folder/'private'), folder/'scratch', min(15, deadline-time.monotonic()))
        assessment = host.assess_canary(receipt, spec, before == host.snapshot(inputs) and private_before == host.snapshot(folder/'private'))
        write_record(folder / 'report.json', {'assessment': assessment, 'receipt': receipt, 'network_control': network})
        if assessment['status'] != 'OBSERVED':
            raise ValueError('Native boundary unavailable')
        # Reuse the existing model-free writable-role qualification without a turn.
        (inputs / 'product/app.py').write_text('Disposable worker write canary.\n')
        sibling = STORE / 'qualification/sibling.txt'; sibling.parent.mkdir()
        sibling.write_text('Denied sibling input.\n')
        writable = bound_module(boundary_checks, STORE=STORE)
        writable.read_protocol = lambda: {'model': protocol()['models']['medium']}
        writable.boundary(inputs, folder / 'writable', worker=True)
        result['status'] = 'QUALIFIED_NOT_DISPATCHED'
    except BaseException as error:
        result.update(status='STOPPED_NOT_QUALIFIED', blocker=str(error))
        raise
    finally:
        result['qualification_seconds'] = time.monotonic()-began
        write_record(STORE / 'results.json', result)


def approved():
    path = STORE / 'approval.json'
    approval = json.loads(path.read_text()) if path.exists() else {}
    limits = protocol()['limits']
    if (approval.get('study_id') != protocol()['study_id'] or
        approval.get('freeze_sha256') != identities() or
        approval.get('max_native_dispatches') != 8 or
        approval.get('max_seconds') != limits['campaign_seconds'] or
        not isinstance(approval.get('user_authorization'), str) or not approval['user_authorization'].strip()):
        raise ValueError('Separate exact-freeze user spending authorization required')
    return approval


def execute():
    approved()
    result = json.loads((STORE / 'results.json').read_text())
    if result['status'] != 'QUALIFIED_NOT_DISPATCHED' or result['freeze_sha256'] != identities():
        raise ValueError('No restart, resume or declaration drift')
    began = time.monotonic()
    result['status'] = 'EXECUTING'
    write_record(STORE / 'results.json', result)
    try:
        for row in result['assignments']:
            identities()
            started = time.monotonic()
            row['attempted'] = True
            deadline = min(started+protocol()['limits']['assignment_seconds'],
                           began+protocol()['limits']['campaign_seconds'])
            folder = Path(row['seed']).parent
            source = (HERE / 'requests' / f'issue-{row["task"]}.md').read_bytes().decode('utf-8')
            if host.git(Path(row['seed']), 'status', '--porcelain') or host.git(Path(row['seed']), 'rev-parse', 'HEAD^{tree}') != row['seed_tree']:
                raise ValueError('Frozen seed changed')
            def dispatch():
                if row['status'] != 'NOT_EXECUTED':
                    raise ValueError('Assignment slot already reserved')
                row['status'] = 'DISPATCHED'
                result['reserved_native_dispatches'] += 1
                write_record(STORE / 'results.json', result)
            preferences = {**protocol()['models'][row['arm']], 'model_catalog_json': str(HERE / 'model-catalog.json')}
            ordinary_coding = bound_module(coding, capture_base=capture_with_history)
            delivery = ordinary_coding.run(Path(row['seed']), source, protocol()['guidance'], folder / 'coding',
                CODEX, preferences, min(protocol()['limits']['coding_seconds'], deadline-time.monotonic()-120),
                protocol()['execution_map'], on_dispatch=dispatch, deadline=deadline-120)
            row.update(stages=delivery['stages'], candidate=delivery['candidate'], handoff=delivery['accepted'])
            for stage in row['stages']:
                stage.update(model=preferences['model'], reasoning_effort=preferences['model_reasoning_effort'], billing_usd=None)
                path = Path(stage['receipt']['events_path'])
                if path.is_file() and host.sha256(path.read_bytes()) == stage['receipt'].get('events.jsonl_sha256'):
                    events = [json.loads(line) for line in path.read_bytes().splitlines()]
                    stage['tool_executions'] = len({event['item']['id'] for event in events
                        if event.get('type') in ('item.started', 'item.completed') and
                        event.get('item', {}).get('type') in ('command_execution', 'file_change')})
            result['model_dispatches'] = sum(len(entry['stages']) for entry in result['assignments'])
            if not row['stages'] or row['stages'][0]['status'] != 'OBSERVED':
                raise ValueError('Native coding unavailable')
            candidate = Path(row['candidate'])
            snapshots.freeze(candidate)
            row['candidate_tree'] = host.git(candidate, 'rev-parse', 'HEAD^{tree}')
            row['grade'] = oracle.observe(candidate, row['task'], folder / 'grade', seconds=min(120, deadline-time.monotonic()))
            visible = next(task['visible_tests'] for task in protocol()['tasks'] if task['issue'] == row['task'])
            row['repository_suite'] = oracle.visible(candidate, visible, folder / 'repository-suite', seconds=min(30, deadline-time.monotonic()))
            row['repository_tests_passed'] = row['repository_suite']['repository_tests_passed']
            row['status'] = row['grade']['status']
            write_record(folder / 'result.json', row)
            write_record(STORE / 'results.json', result)
            if not row['grade']['invocation']['available'] or row['repository_tests_passed'] is None or time.monotonic() > deadline:
                raise ValueError('Grading unavailable or cumulative assignment budget exceeded')
            print('SOURCE AUDIT REQUIRED', row['sequence'], row['task'], row['arm'], str(folder), flush=True)
            audit_started = time.monotonic()
            while not (folder / 'audit.json').exists():
                if time.monotonic() >= deadline:
                    raise ValueError('Source audit exhausted the same assignment budget')
                time.sleep(min(1, deadline-time.monotonic()))
            audit = json.loads((folder / 'audit.json').read_text())
            validate_audit(row, audit)
            row['source_audit'] = audit
            row['source_audit_seconds'] = time.monotonic()-audit_started
            verdict = audit['verdict']
            row['status'] = ('CORRECT_DELIVERY' if row['handoff'] else 'CORRECT_BUT_BLOCKED') if verdict == 'PASS' else (
                ('FALSE_ACCEPTANCE' if row['handoff'] else 'DEFECTIVE_DELIVERY') if verdict == 'DEFECT' else verdict)
            row['total_seconds'] = time.monotonic()-started
            write_record(folder / 'result.json', row)
            result['metrics'] = summarize(result['assignments'])
            write_record(STORE / 'results.json', result)
            if time.monotonic() > deadline:
                raise ValueError('Cumulative assignment budget exhausted')
        result['status'] = 'COMPLETED'
    except BaseException as error:
        result.update(status='STOPPED_INCOMPLETE', blocker=str(error))
        for row in result['assignments']:
            if row.get('attempted') and row['status'] in ('NOT_EXECUTED', 'DISPATCHED', 'SOURCE AUDIT REQUIRED', 'ORACLE UNAVAILABLE'):
                row.update(status='UNAVAILABLE', unavailable_reason=str(error), total_seconds=time.monotonic()-started)
                path = Path(row['seed']).parent / 'coding/implementation/stage.json'
                journal = path.parent / 'private/worker.json'
                if not row['stages'] and (path.exists() or journal.exists()):
                    stage = json.loads(path.read_text()) if path.exists() else {
                        'status': 'NOT VERIFIED', 'usage': None,
                        'receipt': json.loads(journal.read_text()).get('receipt', {})}
                    config = protocol()['models'][row['arm']]
                    stage.update(model=config['model'], reasoning_effort=config['model_reasoning_effort'], billing_usd=None)
                    row['stages'] = [stage]
        raise
    finally:
        result['campaign_seconds'] = time.monotonic()-began
        result['model_dispatches'] = sum(len(entry['stages']) for entry in result['assignments'])
        result['metrics'] = summarize(result['assignments'])
        write_record(STORE / 'results.json', result)


def validate_audit(row, audit):
    source = (HERE / 'requests' / f'issue-{row["task"]}.md').read_bytes()
    if (audit.get('source_sha256') != host.sha256(source) or
        audit.get('candidate_tree') != row['candidate_tree'] or
        audit.get('observation_sha256') != host.sha256((Path(row['seed']).parent / 'grade/observation.json').read_bytes()) or
        audit.get('verdict') not in ('PASS', 'DEFECT', 'DISPUTED', 'NOT_DEMONSTRATED') or
        audit.get('complete_source_read') is not True):
        raise ValueError('Source audit identity/verdict incomplete')
    required = json.loads((HERE / 'audit-clauses.json').read_text())[str(row['task'])]
    clauses = audit.get('clauses', [])
    if [entry.get('quote') for entry in clauses] != required:
        raise ValueError('All frozen material source clauses must be assessed')
    allowed = ('SUPPORTED', 'VIOLATED', 'DISPUTED', 'NOT_DEMONSTRATED')
    if any(entry.get('status') not in allowed or not isinstance(entry.get('evidence'), str) or not entry['evidence'].strip() for entry in clauses):
        raise ValueError('Every clause requires evidence and a supported status')
    statuses = [entry['status'] for entry in clauses]
    if audit['verdict'] == 'PASS' and any(status != 'SUPPORTED' for status in statuses):
        raise ValueError('Incomplete/disputed audit cannot declare success')
    if audit['verdict'] == 'DEFECT' and 'VIOLATED' not in statuses:
        raise ValueError('A defect needs a source-grounded violation')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'qualify', 'execute'))
    args = parser.parse_args(argv)
    {'prepare': prepare, 'qualify': qualify, 'execute': execute}[args.action]()


if __name__ == '__main__':
    main()
