"""Model-free #52 qualification adapter over existing snapshot/native machinery.

There is deliberately no execute/dispatch command. Semantic review and spending
approval cannot be manufactured by passing these finite controls.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
from types import SimpleNamespace

from checks import candidate_snapshot as snapshots, host_probe as host
from checks.native_checks import write_record
from evaluation.effort.study import seed as existing_seed, capture_with_history
from evaluation.recovery import grader
from evaluation.recovery.grader import invoke
from evaluation.sol_luna.grader import bound_module
from evaluation.source_preflight import qualify as source_qualify
from evaluation.issue52 import oracles

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CODEX = host.find_codex(None) or '/opt/homebrew/bin/codex'
PYTHON = str(Path(sys.executable).resolve())


def spec():
    return json.loads((HERE / 'phase2.json').read_text())


def script(task):
    fixtures = {p.name: p.read_bytes() for p in (HERE / 'fixtures').iterdir()}
    return ((HERE / 'oracles.py').read_text() + '\n' +
            f"Path('fixtures').mkdir()\nfor name, raw in {fixtures!r}.items():\n    Path('fixtures', name).write_bytes(raw)\n" +
            f"names = {oracles.CASES[task]!r}\n" + '''results = []
for name in names:
    item = {'id': name, 'passed': False, 'error': None}
    try:
        globals()[name]()
        item['passed'] = True
    except AssertionError as error:
        item['diagnostic'] = str(error)[:300]
    except Exception as error:
        item['error'] = type(error).__name__+': '+str(error)[:300]
    results.append(item)
print(json.dumps({'cases': results}))
''')


# Separately maintained source/case inventory; a reviewer must still assess entailment.
CLAUSES = {
    'feedback': {'receipt': ['feedback_receipts'], 'failure-kinds': ['feedback_states'],
                 'green-path': ['feedback_bounded'], 'malformed-readback': ['feedback_annotations']},
    'promise-mapping': {'direct-check': ['mapping_outcomes'], 'invalid-mapping': ['mapping_validation'],
                        'unlinked': ['mapping_outcomes'], 'missing-gap': ['mapping_advisory']},
    'intentline-adapter': {'direct-path': ['adapter_links'], 'integrity': ['adapter_integrity'],
                          'unsupported': ['adapter_integrity'], 'binding': ['adapter_links']},
    'next-check-hints': {'bounded-hints': ['hint_actions'], 'distinct-kinds': ['hint_states'],
                         'truthful-coverage': ['mapping_outcomes'], 'no-fabrication': ['hint_actions']},
}


def source_binding(task):
    draft = json.loads((HERE / 'obligations-draft.json').read_text())
    entry = next(e for e in draft['entries'] if e['task'] == task)
    source = (HERE / 'requests' / (task+'.md')).read_bytes()
    task_spec = next(t for t in spec()['tasks'] if t['id'] == task)
    blob = hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()
    if blob != task_spec['source_blob_sha']:
        raise ValueError('Original request blob mismatch')
    inventory, rows = {}, []
    for row in entry['expectations']:
        cases = CLAUSES[task][row['id']]
        inventory[row['id']] = {'kind': row['kind'], 'cases': cases}
        rows.append({'id': row['id'], 'kind': row['kind'], 'cases': cases,
                     'claim': row['claim'], 'source_clause': row['source_clause'],
                     'support': 'source', 'ambiguity': '',
                     'acceptable_alternatives': row['acceptable_alternatives']})
    declaration = {'schema_version': 1, 'study_id': spec()['study_id'], 'author': 'phase2 control author',
                   'source_sha256': host.sha256(source), 'oracle_sha256': host.sha256(script(task).encode()),
                   'expectations': rows}
    result = source_qualify(declaration, source=source, oracle_text=script(task), inventory=inventory)
    expected = set(oracles.CASES[task])
    if {c for item in inventory.values() for c in item['cases']} != expected:
        raise ValueError('Source inventory omits a probe')
    return {'structural_preflight': result, 'declaration': declaration,
            'independent_review': 'PENDING', 'complete_source_audit': 'PENDING',
            'semantic_qualification': 'NOT_QUALIFIED'}


def seed(task, destination, variant):
    for kind in ('base', 'reference'):
        if host.git(ROOT, 'rev-parse', task[kind+'_commit']+'^{tree}') != task[kind+'_tree']:
            raise ValueError('Pinned Git tree mismatch')
    product = existing_seed({'base_commit': task['reference_commit']}, destination)
    # Retain only pre-change tests; otherwise a defect could be caught by solution tests.
    shutil.rmtree(product / 'tests')
    for entry in filter(None, snapshots.git_bytes(ROOT, 'ls-tree', '-rz', task['base_commit'], 'tests').split(b'\0')):
        metadata, name = entry.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Unsupported original test entry')
        target = product / os.fsdecode(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(snapshots.git_bytes(ROOT, 'cat-file', 'blob', oid))
        target.chmod(0o755 if mode == '100755' else 0o644)
    if variant != 'reference':
        for edit in spec()['controls'][task['id']][variant]:
            path = product / edit['path']
            raw = path.read_text()
            if raw.count(edit['old']) != 1:
                raise ValueError('Control anchor mismatch: '+task['id'])
            path.write_text(raw.replace(edit['old'], edit['new']))
    snapshots.freeze(product)
    return product


def observe(product, task, directory, *, native, seconds):
    result = invoke(product, script(task), directory, trusted=not native, seconds=seconds)
    cases = None
    if result['available'] and result['receipt']['exit_code'] == 0:
        try:
            cases = json.loads(result['receipt']['stdout'])['cases']
            if ([c['id'] for c in cases] != oracles.CASES[task] or
                    any(type(c['passed']) is not bool or c['error'] is not None for c in cases)):
                cases = None
        except (ValueError, KeyError, TypeError):
            pass
    result.update(available=cases is not None, cases=cases,
                  probes_passed=all(c['passed'] for c in cases) if cases is not None else None,
                  correct=None, source_audit='PENDING', model_dispatches=0)
    write_record(directory / 'result.json', result)
    return result


def input_identities():
    names = snapshots.git_bytes(ROOT, 'ls-files', '-z').split(b'\0')
    paths = {ROOT / os.fsdecode(n) for n in names if n and os.fsdecode(n).endswith(('.py', '.json', '.md', '.txt'))}
    paths.update(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return {str(p.relative_to(ROOT)): host.sha256(p.read_bytes()) for p in sorted(paths)}


def controls(output, *, native=False, green_suite=False):
    output.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    deadline = began + spec()['limits']['native_preflight_seconds']
    result = {'study_id': spec()['study_id'], 'status': 'IN_PROGRESS', 'native': native,
              'model_dispatches': 0, 'live_dispatch_allowed': False, 'controls': [],
              'input_sha256': input_identities(), 'source_bindings': {},
              'host': {'system': platform.system(), 'machine': platform.machine(),
                       'macos': platform.mac_ver()[0], 'python': platform.python_version(),
                       'python_path': PYTHON, 'python_sha256': host.sha256(Path(PYTHON).read_bytes())}}
    write_record(output / 'qualification.json', result)
    try:
        if native:
            if platform.system() != 'Darwin' or sys.version_info < (3, 11):
                raise ValueError('Unsupported native host')
            version = host.run_command([CODEX, '--version'], output, 10)
            result['host']['codex_version_receipt'] = version
            result['host']['codex_sha256'] = host.sha256(Path(CODEX).resolve().read_bytes())
            if not host.succeeded(version) or version['stdout'].strip() != 'codex-cli 0.162.1':
                raise ValueError('Unsupported native Codex')
        for task in spec()['tasks']:
            binding = source_binding(task['id'])
            result['source_bindings'][task['id']] = binding
            if binding['structural_preflight']['status'] != 'QUALIFIED':
                raise ValueError('Source binding failed')
            for variant in ('reference', 'alternative', 'defective'):
                folder = output / task['id'] / variant
                product = seed(task, folder / 'product', variant)
                remaining = min(spec()['limits']['control_seconds'], deadline-time.monotonic())
                if remaining <= 0:
                    raise ValueError('Qualification budget exhausted')
                observed = observe(product, task['id'], folder / 'oracle', native=native, seconds=remaining)
                row = {'task': task['id'], 'variant': variant,
                       'candidate_tree': host.git(product, 'rev-parse', 'HEAD^{tree}'),
                       'base_commit': task['base_commit'], 'reference_commit': task['reference_commit'],
                       'matched': observed['available'] and observed['probes_passed'] == (variant != 'defective'),
                       'observation': str((folder / 'oracle/result.json').relative_to(output)),
                       'probes_passed': observed['probes_passed']}
                result['controls'].append(row)
                write_record(output / 'qualification.json', result)
                if not row['matched']:
                    raise ValueError('Control unavailable or disagreed: '+task['id']+' '+variant)
                if green_suite and task['id'] == 'promise-mapping' and variant == 'defective':
                    # Actual complete pre-change suite, separate from the withheld source probes.
                    program = ('import os, subprocess, sys, json\nfrom pathlib import Path\n'
                               "os.environ.update(PATH='/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_EXEC_PATH='/Library/Developer/CommandLineTools/usr/libexec/git-core')\n"
                               "support=Path('suite-support'); support.mkdir()\n"
                               "shim=\"import os; os.defpath='/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin'\\n\"\n"
                               "(support/'sitecustomize.py').write_text(shim)\n"
                               "os.environ['PYTHONPATH']=str(support.resolve())\n"
                               'product=sys.path[0]\n'
                               f'argv=[{PYTHON!r}, "-B", "-m", "unittest", "discover", "-s", "tests"]\n'
                               'p=subprocess.run(argv,cwd=product,capture_output=True,text=True,timeout=150)\n'
                               'print(json.dumps(dict(argv=argv,cwd=product,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,pythonpath=os.environ["PYTHONPATH"],sitecustomize=shim)))\n')
                    historical = bound_module(grader, snapshots=SimpleNamespace(capture_worktree=capture_with_history))
                    suite = historical.invoke(product, program, folder / 'existing-suite', trusted=not native,
                                              seconds=min(spec()['limits']['existing_suite_seconds'], deadline-time.monotonic()))
                    row['existing_suite'] = suite
                    data = json.loads(suite['receipt']['stdout']) if suite['available'] and suite['receipt']['exit_code'] == 0 else None
                    row['green_existing_suite'] = bool(data and data['exit_code'] == 0)
                    if not row['green_existing_suite']:
                        raise ValueError('Original full suite did not establish green omission control')
        if result['input_sha256'] != input_identities():
            raise ValueError('Qualification inputs drifted')
        result['status'] = 'CONTROLS_OBSERVED_REVIEW_REQUIRED'
    except BaseException as error:
        result.update(status='STOPPED_NOT_QUALIFIED', blocker=str(error))
        raise
    finally:
        result['elapsed_seconds'] = time.monotonic()-began
        write_record(output / 'qualification.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['controls'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native', action='store_true', help='Native protected controls; no model calls')
    parser.add_argument('--green-suite', action='store_true', help='Also run the complete original suite on the omission control')
    args = parser.parse_args(argv)
    result = controls(args.output.resolve(), native=args.native, green_suite=args.green_suite)
    print(json.dumps({'status': result['status'], 'controls': len(result['controls']), 'model_dispatches': 0}))


if __name__ == '__main__':
    main()
