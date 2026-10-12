#!/usr/bin/env python3
"""Freeze, execute, and independently score a four-way local pilot and model experiment."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proofline as p
from checks import s3_compare as s3, s6_corpus as corpus, s6_baseline as baseline
from s0_live import oracle_runner, positive_seconds

MODELS = {"sol": "gpt-6.1-sol", "luna": "gpt-6-luna"}
MAP = f'Use {Path(sys.executable).resolve()} -I -B app.py <JSON> as the public CLI (run from product directory). product.process(data) is the library entry point. Existing tests: {Path(sys.executable).resolve()} -B -m unittest discover. Standard library only. Build output belongs in scratch.'


def digest(value):
    return p.host.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode())


def same_json(actual, expected):
    if type(actual) in (int, float) and type(expected) in (int, float):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(same_json(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(same_json(a, b) for a, b in zip(actual, expected))
    return actual == expected


def seed(directory, item, variant="seed"):
    directory.mkdir(parents=True)
    (directory / "app.py").write_text(corpus.APP)
    (directory / "product.py").write_text(item[variant])
    (directory / "README.md").write_text('JSON component CLI. Run app.py with one JSON argument; --version prints pilot-tool 1.0. Fix product.py while preserving the public interface.\n')
    (directory / "test_app.py").write_text('import subprocess, sys, unittest\nclass Compatibility(unittest.TestCase):\n    def test_version(self):\n        result=subprocess.run([sys.executable,"-B","app.py","--version"],capture_output=True,text=True)\n        self.assertEqual((result.returncode,result.stdout),(0,"pilot-tool 1.0\\n"))\n')
    (directory / ".gitignore").write_text('/.p2p/\n__pycache__/\n*.pyc\n')
    p.host.git(directory, "init", "--quiet", "--template=")
    p.freeze(directory)


def evaluate(candidate, item, *, codex=None, directory):
    """Answer keys come only from predeclared source expectations, never candidate tests."""
    directory, candidate = directory.resolve(), candidate.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    inputs = directory / "inputs"
    inputs.mkdir()
    shutil.copytree(candidate, inputs / "product", symlinks=True,
                    ignore=shutil.ignore_patterns('.git', '.p2p', '__pycache__', '*.pyc'))
    p.validate_links(inputs / "product")
    before = p.host.snapshot(inputs)
    observations, receipts = [], []
    large_csv = item['id'] == 'quoted-csv' and any(len(json.dumps(probe['expected'])) > 12000 for probe in item['probes'])
    regular = {**item, 'probes': [probe for probe in item['probes'] if not large_csv or len(json.dumps(probe['expected'])) <= 12000]}
    cases = [( [json.dumps(probe['input'], ensure_ascii=True)], probe['expected']) for probe in regular['probes']]
    cases += [(['--version'], {'version': 'pilot-tool 1.0\n'}), ([], {'error': True}), (['{'], {'error': True}), (['{}', '{}'], {'error': True})]
    for arguments, expected in cases:
        with tempfile.TemporaryDirectory(prefix='proofline-s6-oracle-') as temporary:
            scratch = Path(temporary).resolve()
            runner = oracle_runner(codex, inputs, directory / "private", receipts) if codex else subprocess.run
            # -I excludes product from sys.path; the trusted launcher restores only its frozen directory.
            argv = [str(Path(sys.executable).resolve()), '-I', '-B', '-c',
                    'import runpy,sys;sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[2:];runpy.run_path(sys.argv[0],run_name="__main__")',
                    str(inputs / 'product'), str(inputs / 'product/app.py'), *arguments]
            observation = {'arguments': arguments, 'expected': expected, 'status': 'NOT VERIFIED'}
            try:
                result = runner(argv, cwd=scratch, timeout=8, capture_output=True, text=True, check=False)
                observation.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
                if codex and 'sandbox-exec: sandbox_apply:' in result.stderr:
                    raise OSError('Native sandbox could not initialize; no product observation established')
                if isinstance(expected, dict) and expected.get('error') is True:
                    matched = result.returncode == 2 and result.stdout == '' and bool(result.stderr.strip())
                elif isinstance(expected, dict) and 'version' in expected:
                    matched = result.returncode == 0 and result.stdout == expected['version'] and not result.stderr
                else:
                    try:
                        matched = result.returncode == 0 and not result.stderr and same_json(json.loads(result.stdout), expected)
                    except (ValueError, TypeError):
                        matched = False
                matched = matched and not any(scratch.iterdir())
                observation['status'] = 'SATISFIED' if matched else 'VIOLATED'
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                observation['error'] = str(error)
            observations.append(observation)
    from checks.s6_acceptance_audit import inspect
    library = inspect(candidate, regular, directory / "library", codex)
    extra = {'correct': True, 'observed': True}
    if large_csv:
        from checks.s6_regression_audit import evaluate as large_field_check
        extra = large_field_check(candidate, item, codex, directory / 'large-csv')
    unchanged = p.host.snapshot(inputs) == before
    return {'correct': extra['correct'] and library['correct'] and unchanged and all(o['status'] == 'SATISFIED' for o in observations),
            'observed': extra['observed'] and library['observed'] and unchanged and all(o['status'] != 'NOT VERIFIED' for o in observations),
            'candidate_sha256': before['sha256'], 'unchanged': unchanged,
            'observations': observations, 'receipts': receipts, 'library': library, 'large_csv': extra if large_csv else None}


def controls(tasks, directory, codex=None):
    results = []
    variants = [(item, variant, expected) for item in tasks for variant, expected in
                (('good', True), ('alternative', True), ('seed', False)) if item[variant] is not None]
    item = tasks[1]
    mutation = item['good'].replace('def process(', 'def original_process(') + '\ndef process(data):\n    result=original_process(data)\n    data["unrequested"]=1\n    return result\n'
    variants += [({**item, 'mutating-valid-output': mutation}, 'mutating-valid-output', False),
                 ({**item, 'unused-foreign-import': item['good']+'\nif False:\n    import unrequested_vendor_extension\n'}, 'unused-foreign-import', False)]
    item = tasks[0]
    alternative = 'class ValidationError(ValueError):\n    pass\n\n'+item['good'].replace('raise ValueError(', 'raise ValidationError(')
    variants.append(({**item, 'valid-error-subclass': alternative}, 'valid-error-subclass', True))
    for index, (item, variant, expected) in enumerate(variants):
        root = directory / str(index)
        seed(root / 'product', item, variant)
        result = evaluate(root / 'product', item, codex=codex, directory=root / 'evaluation')
        results.append({'task': item['id'], 'variant': variant, 'expected': expected, 'evaluation': result})
        p.write_record(root / 'control.json', results[-1])
        if not result['observed'] or result['correct'] != expected:
            raise ValueError(f'Evaluator control failed: {item["id"]}/{variant}')
    return results


def declare(output, p2p_repo, *, models=MODELS, seconds=900, stage_seconds=240, dispatches=12, jobs=4, repetitions=1, rates=None):
    if (any(type(n) is not int for n in (jobs, repetitions, dispatches)) or
            jobs < 1 or repetitions < 1 or dispatches < 3 or
            not math.isfinite(seconds) or not math.isfinite(stage_seconds) or seconds <= 120 or stage_seconds <= 0):
        raise ValueError('Positive concurrency/repetitions, three dispatches, and verification capacity required')
    if set(models) != {'sol', 'luna'} or len(set(models.values())) != 2 or not all(isinstance(v, str) and v.strip() for v in models.values()):
        raise ValueError('Declare exact Sol and Luna model IDs')
    if rates is not None:
        if set(rates) != set(models.values()) or any(set(row) != {'input', 'cached', 'output'} or any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in row.values()) for row in rates.values()):
            raise ValueError('Rates must declare finite nonnegative USD per million input/cached/output tokens for both models')
    output.mkdir(parents=True, exist_ok=False)
    operator = output / 'operator'
    operator.mkdir()
    (operator / 'oracle-canary').write_text('private S6 answers')
    p.write_record(operator / 'tasks.json', corpus.TASKS)
    p.write_record(operator / 'rates.json', rates)
    packages = [Path(__file__), Path(corpus.__file__), Path(baseline.__file__), Path(s3.__file__), Path(s3.s3_p2p_transport.__file__), Path(p.__file__), Path(p.live.__file__), Path(p.host.__file__), Path(p.contract_input.__file__), Path(p.publication.__file__), Path(__file__).with_name("s6_acceptance_audit.py"), Path(__file__).with_name("s6_regression_audit.py"), p2p_repo / s3.SCRIPT]
    planning = p2p_repo / 'skills/productivity/plan-acceptance'
    packages += [planning / 'SKILL.md', planning / 'references/acceptance-contract-protocol.md']
    packages += [Path(sys.modules[oracle_runner.__module__].__file__)]
    packages += list((p2p_repo / 'skills/productivity/deliver-issue/scripts').glob('p2p_*.py'))
    packages += [p2p_repo / 'skills/productivity' / name / 'SKILL.md' for name in ('deliver-issue', 'implement-contract', 'review-implementation', 'prove', 'diagnose-issue', 'fix-implementation') if (p2p_repo / 'skills/productivity' / name / 'SKILL.md').exists()]
    stages = {'plan-acceptance', 'deliver-issue', 'implement-contract', 'review-implementation', 'prove', 'diagnose-issue', 'fix-implementation'}
    for name in p.git_bytes(p2p_repo, 'ls-files', '-z', 'skills/productivity').decode().split('\0'):
        parts = Path(name).parts
        if len(parts) > 2 and parts[2] in stages and (p2p_repo / name).is_file():
            packages.append(p2p_repo / name)
    files = {str(path.resolve()): p.host.sha256(path.read_bytes()) for path in packages}
    archive = operator / 'runtime-archive'
    archive.mkdir()
    archives = {}
    for index, (name, expected) in enumerate(files.items()):
        target = archive / str(index)
        shutil.copyfile(name, target)
        if p.host.sha256(target.read_bytes()) != expected:
            raise ValueError('Runtime changed during declaration: ' + name)
        archives[name] = str(target.relative_to(operator))
    codex = p.host.find_codex(None)
    preferences = p.live.preferences()
    effort = preferences.get('model_reasoning_effort', 'high')
    assignments = []
    # Rotating order prevents one method consistently benefiting from a warm host.
    for repeat in range(repetitions):
        for index, item in enumerate(corpus.TASKS):
            mode = 'raw-request' if index % 2 == 0 else 'shared-preplanned'
            cohorts = list(s3.COHORTS)
            cohorts = cohorts[index % 4:] + cohorts[:index % 4]
            arms = [('sol', cohort) for cohort in cohorts] + [('luna', cohort) for cohort in ('ordinary-agent', 'proofline')]
            random.Random(6000 + index + repeat * 20).shuffle(arms)
            for model, cohort in arms:
                assignments.append({'id': uuid.uuid4().hex, 'task': item['id'], 'input_mode': mode,
                    'model': model, 'cohort': cohort, 'repeat': repeat, 'outcome': 'NOT EXECUTED'})
    manifest = {'kind': 's6_pilot', 'schema_version': 1, 'declared_at': datetime.now(timezone.utc).isoformat(),
        'models': {name: {'model': value, 'model_reasoning_effort': effort} for name, value in models.items()},
        'p2p_repo': str(p2p_repo.resolve()), 'p2p_commit': p.git_bytes(p2p_repo, 'rev-parse', 'HEAD').decode().strip(),
        'proofline_commit': p.host.git(p.host.ROOT, 'rev-parse', 'HEAD'), 'files': files, 'runtime_archive': archives,
        'tasks_sha256': p.host.sha256((operator / 'tasks.json').read_bytes()),
        'rates_sha256': p.host.sha256((operator / 'rates.json').read_bytes()),
        'limits': {'seconds': seconds, 'stage_seconds': stage_seconds, 'dispatches': dispatches,
                   'verification_reserve': 120, 'jobs': jobs, 'repetitions': repetitions},
        'delivery_target': 'local', 'remote_target_coverage': 'NOT EXECUTED: no remote effect grant in this pilot',
        'host': {'python': sys.version, 'codex_sha256': p.host.sha256(Path(codex).read_bytes()) if codex else None,
                 'system': p.platform.platform()},
        'human_preparation_seconds': None, 'shared_plan_authoring_seconds': None,
        'hypothesis': {'minimum_median_reduction': .25, 'maximum_false_blocking_rate': .10,
                       'quality_noninferiority': 'no fewer satisfactory deliveries on paired assignments',
                       'minimum_tasks_per_input_mode': 10},
        'assignment_order_seed': 6000, 'assignments': assignments,
        'limits_of_inference': ['Synthetic standard-library component tasks; not large production repositories.',
            'Held-out tags mean excluded from prompt tuning, not unknown to the corpus author.',
            'Single host, fixed declared concurrency; repeated runs are not independent task samples.',
            'P2P raw planning uses its current local planning instructions under a benchmark source-preserving mandate.',
            'Shared plans are independently authored synthetic agreements; authoring attention/cost is unknown.',
            'Baselines use native Codex with a minimal completion/review response; transport overhead is included.',
            'Standalone coding gets the whole episode; coding plus review reserves one stage for review. P2P/Proofline use their stage limits.']}
    p.write_record(operator / 'manifest.json', manifest)
    p.write_record(operator / 'report.json', {'manifest_sha256': p.host.sha256((operator / 'manifest.json').read_bytes()),
        'status': 'DECLARED', 'assignments': assignments, 'setup_seconds': None})
    return manifest


def verify_declaration(output, *, runtime=True):
    operator = output / 'operator'
    manifest = json.loads((operator / 'manifest.json').read_text())
    report = json.loads((operator / 'report.json').read_text())
    if report['manifest_sha256'] != p.host.sha256((operator / 'manifest.json').read_bytes()):
        raise ValueError('Predeclaration changed')
    for path, expected in manifest['files'].items():
        if path in manifest.get('runtime_archive', {}) and p.host.sha256((operator / manifest['runtime_archive'][path]).read_bytes()) != expected:
            raise ValueError('Declared runtime archive changed: ' + path)
        if runtime and p.host.sha256(Path(path).read_bytes()) != expected:
            raise ValueError('Declared runtime/instruction changed: ' + path)
    if p.host.sha256((operator / 'tasks.json').read_bytes()) != manifest['tasks_sha256'] or p.host.sha256((operator / 'rates.json').read_bytes()) != manifest['rates_sha256']:
        raise ValueError('Declared evaluator or pricing changed')
    expected = [{k: v for k, v in row.items() if k != 'outcome'} for row in manifest['assignments']]
    actual = [{k: row.get(k) for k in template} for row, template in zip(report['assignments'], expected)]
    if len(report['assignments']) != len(expected) or actual != expected:
        raise ValueError('Assignment population changed')
    return manifest, report


def validate_p2p_plan(text, inputs, controller):
    sources = re.findall(r'^Source: ([^\r\n]+)\r?$', text, re.MULTILINE)
    if len(sources) != 1 or p.contract_input.local_links(sources[0], inputs) != [(inputs / 'source.md').resolve()]:
        raise ValueError('Planner must retain the recoverable original source')
    sys.path.insert(0, str(controller.parent))
    import p2p_delivery
    p2p_delivery.parse_contract(text.encode())


def prepare_raw(item, repo, output, preferences, controller, codex, timeout):
    """Run actual P2P planning guidance; never provide private answer keys."""
    started = time.monotonic()
    inputs, scratch, private = (output / name for name in ('inputs', 'scratch', 'private'))
    inputs.mkdir(parents=True); scratch.mkdir(); private.mkdir()
    (inputs / 'source.md').write_text(corpus.source(item))
    shutil.copytree(repo, inputs / 'product', symlinks=True)
    (inputs / 'response.schema.json').write_text(json.dumps(p.live.object_schema({'contract': p.live.STRING})))
    planning = controller.parents[2] / 'plan-acceptance'
    shutil.copyfile(planning / 'SKILL.md', inputs / 'planning.md')
    shutil.copyfile(planning / 'references/acceptance-contract-protocol.md', inputs / 'protocol.md')
    before = p.host.snapshot(inputs)
    prompt = f'''Use the current P2P planning instructions {inputs / 'planning.md'} and protocol {inputs / 'protocol.md'} to prepare the local source {inputs / 'source.md'} against repository {inputs / 'product'}.
This is an enclosing local benchmark workflow with a standing source-preserving planning mandate: retain R1,R2,R3 and the complete original outcomes, don't invent or narrow obligations. No tracker effects, approval invention, implementation, publication, or skill continuation. Return exact proposed Markdown in the contract property; storage/readback is owned by the enclosing benchmark. Use a Source link [Original request](source.md), heading '# Acceptance contract: {item['id']}', revision v1, Parent None, Prerequisites None and the established eight-column matrix. Public commands: {MAP}.
The original source stays binding even if the proposed plan is incomplete. Source gaps will count against delivery; a synthetic benchmark mandate does not claim historical approval.'''
    receipt = p.live.launch(p.live.command(codex, inputs, scratch, private, preferences), prompt, private, timeout)
    stage = {'role': 'planning', 'receipt': receipt, 'usage': None, 'status': 'NOT VERIFIED'}
    try:
        observed = p.live.read_events(receipt)
        stage.update(usage=observed['usage'], thread_id=observed['thread_id'])
        text = observed['report']['contract']
        path = inputs / 'contract.md'
        if p.host.snapshot(inputs) != before:
            raise ValueError('Planner changed binding inputs')
        path.write_text(text)
        validate_p2p_plan(text, inputs, controller)
        stage.update(status='OBSERVED', contract_sha256=p.host.sha256(text.encode()), elapsed_seconds=time.monotonic()-started)
        return text, stage
    except (ValueError, KeyError, OSError, TypeError) as error:
        stage.update(error=str(error), elapsed_seconds=time.monotonic()-started)
        return None, stage


def classify(accepted, evaluation, delivery):
    if not evaluation['observed']:
        return 'NOT VERIFIED'
    if accepted:
        return 'ACCEPTED CORRECTLY' if evaluation['correct'] else 'FALSE ACCEPTED'
    stages = delivery.get('stages', [])
    # False rejection measures an actual rejection of correct code even when later repaired.
    if delivery.get('status') == 'BUDGET EXHAUSTED' or delivery.get('controller_receipt', {}).get('timed_out') or any(s.get('receipt', {}).get('timed_out') or s.get('receipt', {}).get('outcome') in {'timeout', 'interrupted'} for s in stages):
        return 'BUDGET EXHAUSTED'
    if evaluation['correct'] and s3.judgment_observed(stages):
        return 'FALSE BLOCKED'
    return 'FAILED'


def account_delivery(delivery):
    """Include a terminated native attempt even when its handoff was incomplete."""
    delivery = {**delivery, 'stages': list(delivery.get('stages', []))}
    active = delivery.get('active_stage')
    if active:
        folder = Path(active['directory'])
        path = folder / 'stage.json'
        worker = folder / 'private/worker.json'
        if path.is_file() and worker.is_file():
            stage = json.loads(path.read_text())
            lifecycle = json.loads(worker.read_text())
            receipt = stage.get('receipt', {})
            if (lifecycle.get('state') != 'finished' or lifecycle.get('receipt') != receipt
                    or stage.get('role') != active['role'] or stage.get('binding') != active['binding']):
                raise ValueError('Incomplete stage measurement does not match protected native receipt')
            for name in ('events.jsonl', 'stderr.txt'):
                if p.host.sha256((folder / 'private' / name).read_bytes()) != receipt[name + '_sha256']:
                    raise ValueError('Incomplete stage host evidence changed')
            if not any(s.get('receipt', {}).get('invocation_id') == receipt.get('invocation_id') for s in delivery['stages']):
                delivery['stages'].append(stage)
                delivery['measurement_readback'] = {'path': str(path), 'sha256': p.host.sha256(path.read_bytes())}
    if 'controller_status' in delivery:
        delivery['correction_rounds'] = sum(s.get('role') == 'repair' for s in delivery['stages'])
    return delivery


def rejection_scores(delivery, cohort, item, directory, codex):
    scores = []
    for index, stage in enumerate(delivery.get('stages', [])):
        report = stage.get('report')
        if (cohort != 'proofline' or stage.get('role') not in {'reviewer', 'prover'}
                or not isinstance(report, dict) or report.get('verdict', report.get('status')) not in {'FAIL', 'NOT VERIFIED', 'BLOCKED', 'REJECTED'}):
            continue
        events = stage.get('receipt', {}).get('events_path')
        if not events:
            continue
        candidate = Path(events).parent.parent / 'inputs/product'
        if candidate.is_dir():
            score = evaluate(candidate, item, codex=codex, directory=directory / f'rejection-{index}')
            scores.append({'stage': index, 'role': stage['role'],
                           'false_rejection': score['correct'] and score['observed'], 'evaluation': score})
    return scores


def worker(output, assignment_id):
    manifest, report = verify_declaration(output)
    assignment = next(a for a in manifest['assignments'] if a['id'] == assignment_id)
    tasks = json.loads((output / 'operator/tasks.json').read_text())
    item = next(t for t in tasks if t['id'] == assignment['task'])
    directory = output / 'runs' / assignment_id
    directory.mkdir(parents=True, exist_ok=False)
    p.write_record(directory / 'worker.json', {'pid': os.getpid(), 'state': 'running', 'started_at': datetime.now(timezone.utc).isoformat()})
    result = dict(assignment)
    started = time.monotonic()
    preferences = manifest['models'][assignment['model']]
    codex = p.host.find_codex(None)
    repo = directory / 'source'
    seed(repo, item)
    limits = manifest['limits']
    planning = []
    controller = Path(manifest['p2p_repo']) / s3.SCRIPT
    source, brief = corpus.source(item), corpus.contract(item) if assignment['input_mode'] == 'shared-preplanned' else corpus.brief(item)
    try:
        preparation_started = time.monotonic()
        if assignment['cohort'] == 'p2p' and assignment['input_mode'] == 'raw-request':
            brief, stage = prepare_raw(item, repo, directory / 'preparation', preferences, controller, codex, min(limits['stage_seconds'], limits['seconds'] - 120))
            planning.append(stage)
            result['preparation_seconds'] = time.monotonic() - preparation_started
            if brief is None:
                raise ValueError('Raw P2P plan not ready; retained planning failure')
        preparation_seconds = time.monotonic() - preparation_started
        result['preparation_seconds'] = preparation_seconds
        remaining = limits['seconds'] - (time.monotonic() - started)
        slots = limits['dispatches'] - len(planning)
        if remaining <= 120 or slots < 3:
            raise ValueError('No delivery verification capacity after preparation')
        with patch.object(p.live, 'preferences', return_value=preferences):
            if assignment['cohort'] == 'p2p':
                # Controller discovery is host-native; workers retain its actual stage packages.
                delivery = s3.p2p_run(repo, brief, source, directory / 'run', controller,
                    output / 'operator', codex, seconds=remaining, stage_seconds=limits['stage_seconds'],
                    dispatches=slots, repairs=3, preferences=preferences,
                    fixed_plan=assignment['input_mode'] == 'shared-preplanned')
            elif assignment['cohort'] == 'proofline':
                raw = p.deliver(repo, source, brief, directory / 'run', remaining,
                    limits['stage_seconds'], 120, execution_map=MAP, dispatches=slots)
                delivery = {**raw, 'accepted': raw['status'] == 'LOCAL ACCEPTED', 'candidate': raw.get('candidate_path', str(repo))}
                if delivery['accepted']:
                    delivery['accepted'] = p.inspect_record(directory / 'run/report.json')['status'] == 'LOCAL ACCEPTED'
            else:
                delivery = baseline.run(repo, source, brief, directory / 'run', assignment['cohort'] == 'agent-plus-review',
                    codex, preferences, remaining, limits['stage_seconds'], MAP)
        delivery = account_delivery(delivery)
        result['delivery'] = delivery
        result['planning_stages'] = planning
        result['end_to_end_seconds'] = time.monotonic() - started
        result['evaluation'] = evaluate(Path(delivery['candidate']), item, codex=codex, directory=directory / 'operator/final')
        result['outcome'] = classify(delivery['accepted'], result['evaluation'], delivery)
        result['judgment_errors'] = rejection_scores(delivery, assignment['cohort'], item, directory / 'operator', codex)
        result['human_interventions'] = 0
        result['human_attention_seconds'] = 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        timed_out = any(stage.get('receipt', {}).get('timed_out') for stage in planning)
        result.update(outcome='BUDGET EXHAUSTED' if timed_out else 'FAILED', error=str(error), planning_stages=planning,
                      end_to_end_seconds=time.monotonic()-started, human_interventions=0, human_attention_seconds=0)
    result['total_observation_seconds'] = time.monotonic() - started
    p.write_record(directory / 'result.json', result)
    p.write_record(directory / 'worker.json', {'pid': os.getpid(), 'state': 'finished'})
    return result


def execute(output):
    """Separate processes keep model selection and live module state isolated."""
    operator = output / 'operator'
    with (operator / 'campaign.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest, report = verify_declaration(output)
        if report['status'] == 'TRUST GATE FAILED':
            raise ValueError('False acceptance stops further automation; repair boundary and declare a new campaign')
        started = time.monotonic()
        codex = p.host.find_codex(None)
        if not codex or p.host.run_command([codex, '--version'], operator)['stdout'].strip() != 'codex-cli 0.162.1':
            raise ValueError('Qualified Codex 0.162.1 required')
        if not report.get('controls'):
            try:
                report['controls'] = controls(json.loads((operator / 'tasks.json').read_text()), operator / ('controls-' + uuid.uuid4().hex), codex)
            except (OSError, ValueError) as error:
                report.update(status='EVALUATOR GATE FAILED', error=str(error), setup_seconds=time.monotonic()-started)
                p.write_record(operator / 'report.json', report)
                raise
            report['setup_seconds'] = time.monotonic() - started
            p.write_record(operator / 'report.json', report)
        # Never rerun an uncertain assignment or replace a recorded failure.
        for assignment in report['assignments']:
            result_path = output / 'runs' / assignment['id'] / 'result.json'
            if result_path.exists():
                assignment.update(json.loads(result_path.read_text()))
            elif (output / 'runs' / assignment['id']).exists():
                assignment.update(outcome='INTERRUPTED', error='Uncertain previous worker; reconcile before any explicit new campaign')
        if any(a['outcome'] == 'INTERRUPTED' for a in report['assignments']):
            report['status'] = 'RECONCILIATION REQUIRED'
            p.write_record(operator / 'report.json', report)
            return summarize(manifest, report, json.loads((operator / 'rates.json').read_text()))
        pending = [a for a in report['assignments'] if a['outcome'] == 'NOT EXECUTED']
        report['status'] = 'RUNNING'
        p.write_record(operator / 'report.json', report)
        def launch(assignment):
            logs = operator / 'logs'
            logs.mkdir(exist_ok=True)
            with (logs / (assignment['id'] + '.log')).open('xb') as stream:
                child = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), 'worker', str(output), assignment['id']], stdout=stream, stderr=subprocess.STDOUT, check=False)
            path = output / 'runs' / assignment['id'] / 'result.json'
            return json.loads(path.read_text()) if path.exists() else {**assignment, 'outcome': 'INTERRUPTED', 'error': f'Worker exited {child.returncode}; consumed time and calls unknown'}
        # Fixed batches make declared host contention equal across approaches and bound a trust stop.
        with ThreadPoolExecutor(max_workers=manifest['limits']['jobs']) as pool:
            for offset in range(0, len(pending), manifest['limits']['jobs']):
                batch = pending[offset:offset + manifest['limits']['jobs']]
                futures = {pool.submit(launch, assignment): assignment for assignment in batch}
                for future in as_completed(futures):
                    assignment = futures[future]
                    assignment.update(future.result())
                    print(assignment['task'], assignment['model'], assignment['cohort'], assignment['outcome'], flush=True)
                    p.write_record(operator / 'report.json', report)
                if any(a['cohort'] == 'proofline' and a['outcome'] == 'FALSE ACCEPTED' for a in batch):
                    report['status'] = 'TRUST GATE FAILED'
                    break
                if any(a['outcome'] == 'INTERRUPTED' for a in batch):
                    report['status'] = 'RECONCILIATION REQUIRED'
                    break
        if report['status'] not in {'TRUST GATE FAILED', 'RECONCILIATION REQUIRED'}:
            report['status'] = 'COMPLETE' if all(a['outcome'] != 'NOT EXECUTED' for a in report['assignments']) else 'INCOMPLETE'
        report['known_campaign_seconds'] = report.get('known_campaign_seconds', 0) + time.monotonic()-started
        p.write_record(operator / 'report.json', report)
        result = summarize(manifest, report, json.loads((operator / 'rates.json').read_text()))
        p.write_record(operator / 'summary.json', result)
        (operator / 'results.md').write_text(render(result))
        return result


def stage_usage(stages, dispatches):
    known, unknown = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0}, max(0, dispatches-len(stages))
    for stage in stages:
        usage = stage.get('usage')
        if not isinstance(usage, dict) or any(type(usage.get(key)) is not int or usage[key] < 0 for key in known) or usage['cached_input_tokens'] > usage['input_tokens']:
            unknown += 1
        else:
            for key in known: known[key] += usage[key]
    return known, unknown


def summarize(manifest, report, rates=None):
    rows, pairs = {}, []
    for assignment in report['assignments']:
        key = '/'.join(assignment[name] for name in ('model', 'input_mode', 'cohort'))
        row = rows.setdefault(key, {'input_mode': assignment['input_mode'], 'assigned': 0, 'outcomes': {}, 'satisfactory': 0, 'end_to_end_times': [],
            'successful_times': [], 'tokens_per_attempt': [], 'known_seconds': 0, 'unknown_seconds': 0,
            'known_calls': 0, 'unknown_calls': 0, 'known_tokens': {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0},
            'unknown_usage_calls': 0, 'known_cost_usd': 0 if rates else None, 'unknown_cost_attempts': 0,
            'human_interventions': 0, 'unknown_human_interventions': 0, 'human_attention_seconds': 0,
            'unknown_human_attention': 0, 'false_rejections': 0, 'rejection_judgments_scored': 0, 'unscored_rejection_judgments': 0,
            'roles': {}, 'repair_rounds': 0, 'upstream_planning_seconds': 0, 'input_preparation_seconds': 0,
            'correct_but_undelivered': 0, 'unknown_input_preparation_attempts': 0})
        row['assigned'] += 1
        label = assignment['outcome']
        row['outcomes'][label] = row['outcomes'].get(label, 0)+1
        satisfactory = label == 'ACCEPTED CORRECTLY'
        row['satisfactory'] += satisfactory
        row['correct_but_undelivered'] += bool(not satisfactory and assignment.get('evaluation', {}).get('observed') and assignment['evaluation']['correct'])
        seconds = assignment.get('end_to_end_seconds')
        if seconds is None:
            row['unknown_seconds'] += 1
        else:
            row['known_seconds'] += seconds
            row['end_to_end_times'].append(seconds)
            if satisfactory: row['successful_times'].append(seconds)
        for name in ('human_interventions', 'human_attention_seconds'):
            value = assignment.get(name)
            if value is None:
                row['unknown_human_interventions' if name == 'human_interventions' else 'unknown_human_attention'] += 1
            else: row[name] += value
        delivery = assignment.get('delivery', {})
        planning = assignment.get('planning_stages', [])
        stages = planning + delivery.get('stages', [])
        calls = delivery.get('model_dispatches', len(delivery.get('stages', []))) + len(planning) if 'delivery' in assignment or planning else None
        if label == 'NOT EXECUTED': calls = 0
        if calls is None: row['unknown_calls'] += 1; calls = len(stages)
        row['known_calls'] += calls
        tokens, missing = stage_usage(stages, calls)
        if label not in {'NOT EXECUTED'} and 'delivery' not in assignment and not planning:
            missing += 1
        row['unknown_usage_calls'] += missing
        for name, value in tokens.items(): row['known_tokens'][name] += value
        row['tokens_per_attempt'].append(None if missing else tokens['input_tokens']+tokens['output_tokens'])
        rate = (rates or {}).get(manifest['models'][assignment['model']]['model'])
        if rate and label != 'NOT EXECUTED':
            row['known_cost_usd'] += ((tokens['input_tokens']-tokens['cached_input_tokens'])*rate['input']+tokens['cached_input_tokens']*rate['cached']+tokens['output_tokens']*rate['output'])/1_000_000
        if (not rate or missing) and label != 'NOT EXECUTED': row['unknown_cost_attempts'] += 1
        row['repair_rounds'] += delivery.get('correction_rounds', 0)
        row['input_preparation_seconds'] += assignment.get('preparation_seconds', 0)
        row['unknown_input_preparation_attempts'] += bool(planning and 'preparation_seconds' not in assignment)
        for stage in stages:
            role = row['roles'].setdefault(stage.get('role', 'unknown'), {'calls': 0, 'known_seconds': 0, 'unknown_seconds': 0})
            role['calls'] += 1
            value = stage.get('receipt', {}).get('elapsed_seconds')
            if value is None: role['unknown_seconds'] += 1
            else: role['known_seconds'] += value
            if stage.get('role') == 'planning' and value is not None: row['upstream_planning_seconds'] += value
        judgments = assignment.get('judgment_errors', [])
        row['false_rejections'] += sum(j.get('false_rejection', False) for j in judgments)
        row['rejection_judgments_scored'] += len(judgments)
        row['unscored_rejection_judgments'] += sum(1 for stage in delivery.get('stages', []) if stage.get('role') in {'reviewer', 'prover', 'review', 'proof'} and isinstance(stage.get('report'), dict) and stage['report'].get('verdict', stage['report'].get('status')) in {'FAIL', 'NOT VERIFIED', 'BLOCKED', 'REJECTED'}) - len(judgments)
        pairs.append({name: assignment.get(name) for name in ('task', 'model', 'input_mode', 'cohort', 'repeat', 'outcome', 'end_to_end_seconds', 'human_interventions', 'human_attention_seconds')} | {'tokens': None if missing else tokens, 'delivery_seconds': delivery.get('elapsed_seconds'), 'preparation_seconds': assignment.get('preparation_seconds'), 'evaluation': assignment.get('evaluation', {}).get('correct'), 'errors': assignment.get('error'), 'judgment_errors': judgments})
    for row in rows.values():
        n = row['satisfactory']
        complete = not row['unknown_seconds'] and not row['outcomes'].get('NOT EXECUTED')
        row['reliability'] = n / row['assigned']
        row['false_acceptances'] = row['outcomes'].get('FALSE ACCEPTED', 0)
        row['false_acceptance_rate_among_accepted'] = row['false_acceptances']/(n+row['false_acceptances']) if n+row['false_acceptances'] else None
        row['false_blocked'] = row['outcomes'].get('FALSE BLOCKED', 0)
        row['median_successful_seconds'] = statistics.median(row['successful_times']) if row['successful_times'] else None
        row['median_attempt_seconds'] = statistics.median(row['end_to_end_times']) if complete and row['end_to_end_times'] else None
        row['max_attempt_seconds'] = max(row['end_to_end_times'], default=None)
        row['seconds_per_satisfactory_delivery'] = row['known_seconds']/n if n and complete else None
        row['satisfactory_deliveries_per_hour'] = 3600*n/row['known_seconds'] if complete and row['known_seconds'] else None
        tokens = sum(row['known_tokens'][key] for key in ('input_tokens', 'output_tokens'))
        row['tokens_per_satisfactory_delivery'] = tokens/n if n and not row['unknown_usage_calls'] and complete else None
        row['cost_per_satisfactory_delivery_usd'] = row['known_cost_usd']/n if rates and n and not row['unknown_cost_attempts'] and complete else None
        row['satisfactory_deliveries_per_dollar'] = n/row['known_cost_usd'] if rates and row['known_cost_usd'] and not row['unknown_cost_attempts'] and complete else None
        row['full_request_seconds_per_satisfactory_delivery'] = row['seconds_per_satisfactory_delivery'] if row['input_mode'] == 'raw-request' else None
        values = row['tokens_per_attempt']
        row['median_attempt_tokens'] = statistics.median(values) if values and all(v is not None for v in values) and complete else None
        for name in ('end_to_end_times', 'successful_times', 'tokens_per_attempt'): row.pop(name)
    hypotheses = []
    for mode in ('raw-request', 'shared-preplanned'):
        d, c = (rows.get(f'sol/{mode}/{cohort}') for cohort in ('proofline', 'p2p'))
        if d is None or c is None: continue
        matched = len({a['task'] for a in pairs if a['model']=='sol' and a['input_mode']==mode and a['cohort']=='proofline'})
        finished = not any(r['outcomes'].get(label, 0) for r in (d,c) for label in ('NOT EXECUTED', 'INTERRUPTED', 'NOT VERIFIED'))
        quality = finished and d['satisfactory'] > 0 and c['satisfactory'] > 0 and not d['false_acceptances'] and d['satisfactory'] >= c['satisfactory'] and d['false_blocked']/d['assigned'] <= manifest['hypothesis']['maximum_false_blocking_rate']
        reductions = {}
        for metric in ('median_successful_seconds', 'median_attempt_tokens', 'seconds_per_satisfactory_delivery', 'tokens_per_satisfactory_delivery'):
            a, b = d[metric], c[metric]
            reductions[metric] = 1-a/b if a is not None and b else None
        # Success-only medians cannot establish the target with different completed task sets.
        successes = [{a['task'] for a in pairs if a['model']=='sol' and a['input_mode']==mode and a['cohort']==cohort and a['outcome']=='ACCEPTED CORRECTLY'} for cohort in ('proofline','p2p')]
        target = quality and successes[0] == successes[1] and bool(successes[0]) and any(reductions[m] is not None and reductions[m] >= .25 for m in ('median_successful_seconds','median_attempt_tokens'))
        hypotheses.append({'input_mode': mode, 'matched_distinct_tasks': matched, 'quality_gate': quality,
            'reductions': reductions, '25_percent_target': 'SUPPORTED ON PILOT' if target and matched >= 10 else 'NOT SUPPORTED' if finished and quality and matched >= 10 and successes[0]==successes[1] else 'INCONCLUSIVE',
            'interpretation': 'Directional pilot hypothesis only; no statistical superiority claim. Full-request shared planning/human cost remains unknown.'})
    proofline_rows = [row for key,row in rows.items() if key.endswith('/proofline')]
    if any(row['false_acceptances'] for row in proofline_rows):
        decision = 'STRENGTHEN VERIFICATION BEFORE EXPANDING: independently observed false acceptance'
    elif any(row['false_blocked']/row['assigned'] > .10 for row in proofline_rows):
        decision = 'SIMPLIFY OR REPAIR EVIDENCE: chronic false blocking; preserve the promise'
    elif report['status'] != 'COMPLETE' or any(row['unknown_seconds'] for row in rows.values()):
        decision = 'INCONCLUSIVE: finish or reconcile the declared population; preserve every failure'
    elif any(h['25_percent_target'] == 'SUPPORTED ON PILOT' for h in hypotheses):
        decision = 'CONTINUE CAUTIOUSLY: pilot target observed; validate on unfamiliar production repositories'
    else:
        decision = 'RECONSIDER OR SIMPLIFY: no demonstrated quality-gated efficiency advantage'
    cross_model = []
    for mode in ('raw-request','shared-preplanned'):
        selected = {f'{model}/{cohort}': rows.get(f'{model}/{mode}/{cohort}') for model,cohort in [('luna','ordinary-agent'),('luna','proofline'),('sol','ordinary-agent'),('sol','proofline')]}
        cross_model.append({'input_mode': mode, 'arms': selected, 'interpretation': 'Compare satisfactory deliveries, throughput and whole-episode cost; unknown price prevents a cheaper-model claim.'})
    return {'kind':'s6_summary', 'status':report['status'], 'manifest_sha256':report['manifest_sha256'],
            'cohorts':rows, 'paired_per_task':pairs, 'hypotheses':hypotheses, 'model_experiment':cross_model,
            'decision':decision, 'known_campaign_seconds':report.get('known_campaign_seconds'),
            'setup_seconds':report.get('setup_seconds'), 'shared_plan_authoring_seconds':None,
            'human_preparation_seconds':None, 'pricing':'operator-declared USD/million token rates' if rates else 'UNKNOWN: no declared rates',
            'provider_request_count': None, 'call_measurement': 'native stage dispatches; internal provider requests unavailable',
            'limits_of_inference':manifest['limits_of_inference'], 'remote_target_coverage':manifest['remote_target_coverage']}


def render(summary):
    lines = ['# S6 measured pilot', '', f'Status: {summary["status"]}. {summary["decision"]}.', '',
        'These are measured outcomes only where native runs and private observations exist. Unknown costs are not zero. Failed and unexecuted assignments remain in the denominator.', '',
        '| Model / input / approach | Correct / assigned | False accepted | False blocked | Seconds per correct delivery | Tokens per correct delivery | USD per correct delivery |',
        '|---|---:|---:|---:|---:|---:|---:|']
    def display(value): return 'unknown' if value is None else f'{value:.3f}' if isinstance(value,float) else str(value)
    for key,row in summary['cohorts'].items():
        lines.append(f'| {key} | {row["satisfactory"]}/{row["assigned"]} | {row["false_acceptances"]} | {row["false_blocked"]} | {display(row["seconds_per_satisfactory_delivery"])} | {display(row["tokens_per_satisfactory_delivery"])} | {display(row["cost_per_satisfactory_delivery_usd"])} |')
    lines += ['', '| Task | Model | Input | Approach | Outcome | End-to-end seconds |', '|---|---|---|---|---|---:|']
    for row in summary['paired_per_task']:
        lines.append('| ' + ' | '.join(display(row[key]) for key in ('task','model','input_mode','cohort','outcome','end_to_end_seconds')) + ' |')
    lines += ['', *[f'- {h["input_mode"]}: 25% target {h["25_percent_target"]}; quality gate {h["quality_gate"]}.' for h in summary['hypotheses']], '', *[f'- {limit}' for limit in summary['limits_of_inference']], '', f'Pricing: {summary["pricing"]}. Remote targets: {summary["remote_target_coverage"]}.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    declaration = commands.add_parser('declare')
    declaration.add_argument('--output', type=Path, required=True)
    declaration.add_argument('--p2p-repo', type=Path, required=True)
    declaration.add_argument('--sol', default=MODELS['sol'])
    declaration.add_argument('--luna', default=MODELS['luna'])
    declaration.add_argument('--seconds', type=positive_seconds, default=900)
    declaration.add_argument('--stage-seconds', type=positive_seconds, default=240)
    declaration.add_argument('--dispatches', type=int, default=12)
    declaration.add_argument('--jobs', type=int, default=4)
    declaration.add_argument('--repetitions', type=int, default=1)
    declaration.add_argument('--rates', type=Path, help='Declared USD per million token category; never infer unknown prices')
    for name in ('run','summary'):
        commands.add_parser(name).add_argument('output', type=Path)
    internal = commands.add_parser('worker', help=argparse.SUPPRESS)
    internal.add_argument('output', type=Path); internal.add_argument('assignment')
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if args.command == 'declare':
            declare(output, args.p2p_repo.resolve(), models={'sol':args.sol,'luna':args.luna}, seconds=args.seconds,
                    stage_seconds=args.stage_seconds, dispatches=args.dispatches, jobs=args.jobs,
                    repetitions=args.repetitions, rates=json.loads(args.rates.read_text()) if args.rates else None)
            print('DECLARED: ' + str(output / 'operator/manifest.json'))
        elif args.command == 'worker': worker(output,args.assignment)
        elif args.command == 'run':
            result = execute(output)
            return 0 if result['status'] == 'COMPLETE' else 2
        else:
            manifest, report = verify_declaration(output, runtime=False)
            summary = summarize(manifest,report,json.loads((output / 'operator/rates.json').read_text()))
            p.write_record(output / 'operator/summary.json',summary)
            (output / 'operator/results.md').write_text(render(summary))
            print(summary['decision'])
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print('NOT VERIFIED: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
