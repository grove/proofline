#!/usr/bin/env python3
"""Uniform readback of source-required regressions found by native reviewers."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6


def probe(tasks=s6.corpus.TASKS):
    item = copy.deepcopy(next(t for t in tasks if t['id'] == 'quoted-csv'))
    value = 'x' * 131073
    item['probes'] = [{'input': 'name\n' + value + '\n', 'expected': [{'name': value}]}]
    return item


def timestamp_probe(tasks=s6.corpus.TASKS):
    item = copy.deepcopy(next(t for t in tasks if t['id'] == 'utc-timestamps'))
    item['probes'] = [{'input': '2024-061T00:15:30+05:45', 'expected': '2024-02-29T18:30:30Z'}]
    return item


def version_probe(tasks=s6.corpus.TASKS):
    item = copy.deepcopy(next(t for t in tasks if t['id'] == 'version-order'))
    version = '1' * 5000 + '.0.0'
    item['probes'] = [{'input': [version, '9.0.0'], 'expected': ['9.0.0', version]}]
    item['good'] = '''import re
def process(data):
    if any(not re.fullmatch(r"[0-9]+\\.[0-9]+\\.[0-9]+", v) for v in data): raise ValueError("invalid version")
    def key(version):
        parts = [part.lstrip("0") or "0" for part in version.split(".")]
        return tuple((len(part), part) for part in parts)
    return sorted(data, key=key)
'''
    return item


LARGE_CSV_CHECK = '''import importlib,json,subprocess,sys
sys.path.insert(0,sys.argv[1])
value="x"*131073; data="name\\n"+value+"\\n"; expected=[{"name":value}]
try: library=importlib.import_module("product").process(data)==expected
except Exception: library=False
# Linux caps each OS argument; pass the same CLI argument through a trusted launcher.
launcher='import runpy,sys;sys.path.insert(0,sys.argv[1]);sys.argv=[sys.argv[1]+"/app.py",sys.stdin.read()];runpy.run_path(sys.argv[0],run_name="__main__")'
cli=subprocess.run([sys.executable,"-I","-B","-S","-c",launcher,sys.argv[1]],input=json.dumps(data),capture_output=True,text=True,timeout=5)
try: output=json.loads(cli.stdout)==expected
except ValueError: output=False
print(json.dumps({"library_correct":library,"cli_correct":output and cli.returncode==0 and not cli.stderr}))
'''


def evaluate(candidate, item, codex, directory):
    if item['id'] != 'quoted-csv':
        return s6.evaluate(candidate, item, codex=codex, directory=directory)
    # Native process receipts cap stdout; compare the large value inside the sandbox.
    directory.mkdir(parents=True, exist_ok=False)
    inputs = directory / 'inputs'
    inputs.mkdir()
    s6.shutil.copytree(candidate, inputs / 'product', symlinks=True, ignore=s6.shutil.ignore_patterns('.git', '.p2p', '__pycache__', '*.pyc'))
    s6.p.validate_links(inputs / 'product')
    before = s6.p.host.snapshot(inputs)
    receipts = []
    from s0_live import oracle_runner
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary).resolve()
        runner = oracle_runner(codex, inputs, directory / 'private', receipts) if codex else subprocess.run
        result = {'observed': False, 'correct': False, 'receipts': receipts}
        try:
            actual = runner([sys.executable, '-I', '-B', '-S', '-c', LARGE_CSV_CHECK, str(inputs / 'product')], cwd=scratch, timeout=8, capture_output=True, text=True, check=False)
            payload = json.loads(actual.stdout)
            result.update(observed=actual.returncode == 0 and not actual.stderr,
                          correct=actual.returncode == 0 and not actual.stderr and all(payload.values()) and not any(scratch.iterdir()), observations=payload)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            result['error'] = str(error)
    result['unchanged'] = s6.p.host.snapshot(inputs) == before
    result['correct'] &= result['unchanged']
    result['observed'] &= result['unchanged']
    s6.p.write_record(directory / 'report.json', result)
    return result


def audit(campaign, output):
    started = time.monotonic()
    manifest, original = s6.verify_declaration(campaign, runtime=False)
    output.mkdir(parents=True, exist_ok=False)
    tasks = json.loads((campaign / 'operator/tasks.json').read_text())
    items = [probe(tasks), timestamp_probe(tasks), version_probe(tasks)]
    archive = output / 'source-archive'
    archive.mkdir()
    for source in (Path(__file__), Path(s6.__file__), Path(s6.corpus.__file__)):
        (archive / source.name).write_bytes(source.read_bytes())
    s6.p.write_record(output / 'manifest.json', {
        'original_manifest_sha256': original['manifest_sha256'],
        'runner_sha256': s6.p.host.sha256(Path(__file__).read_bytes()),
        'sources': [s6.corpus.source(item) for item in items], 'probes': [item['probes'] for item in items],
        'reason': 'Native reviewers found an inherited CSV field limit, rejection of valid ISO-8601 ordinal dates, and rejection of valid long numeric version components.',
        'basis': 'https://science.data.nasa.gov/fits/documentation/iso-time',
        'scope': 'All approaches and models, final candidates and preserved scored rejection candidates; original scores retained.'})
    codex = s6.p.host.find_codex(None)
    controls = []
    for item in items:
        original_code = {'quoted-csv': 'import csv,io\ndef process(data):\n    rows=list(csv.reader(io.StringIO(data)))\n    return [dict(zip(rows[0],row)) for row in rows[1:]]\n',
                         'utc-timestamps': 'from datetime import datetime,timezone\ndef process(data):\n    return datetime.fromisoformat(data).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")\n',
                         'version-order': 'def process(data):\n    return sorted(data, key=lambda v:tuple(map(int,v.split("."))))\n'}[item['id']]
        corrected = item['good'].replace('def process(data):', 'def process(data):\n    csv.field_size_limit(max(csv.field_size_limit(), len(data)))') if item['id'] == 'quoted-csv' else item['good']
        for name, code, expected in [('limited', original_code, False), ('corrected', corrected, True)]:
            root = output / 'controls' / item['id'] / name
            s6.seed(root / 'product', {**item, 'good': code}, 'good')
            result = evaluate(root / 'product', item, codex, root / 'evaluation')
            assert result['observed'] and result['correct'] == expected, name
            controls.append({'task': item['id'], 'name': name, 'expected': expected, 'evaluation': result})
    s6.p.write_record(output / 'controls.json', controls)
    report = copy.deepcopy(original)
    amended = []
    for assignment in report['assignments']:
        item = next((t for t in items if t['id'] == assignment['task']), None)
        if not item or 'delivery' not in assignment:
            continue
        candidate = Path(assignment['delivery']['candidate'])
        result = evaluate(candidate, item, codex, output / assignment['id'] / 'final')
        before = assignment['outcome']
        assignment['evaluation']['correct'] &= result['correct']
        assignment['evaluation']['observed'] &= result['observed']
        assignment['outcome'] = s6.classify(assignment['delivery']['accepted'], assignment['evaluation'], assignment['delivery'])
        for index, judgment in enumerate(assignment.get('judgment_errors', [])):
            stage = assignment['delivery']['stages'][judgment['stage']]
            events = stage.get('receipt', {}).get('events_path')
            rejected = Path(events).parent.parent / 'inputs/product' if events else None
            if rejected and rejected.is_dir():
                extra = evaluate(rejected, item, codex, output / assignment['id'] / f'rejection-{index}')
                judgment['false_rejection'] &= extra['observed'] and extra['correct']
                judgment['supplemental_observation'] = str(output / assignment['id'] / f'rejection-{index}')
        amended.append({'id': assignment['id'], 'task': assignment['task'], 'model': assignment['model'], 'cohort': assignment['cohort'],
                        'original_outcome': before, 'outcome': assignment['outcome'], 'evaluation': result})
    report['supplemental_regression_readback'] = str(output)
    report['regression_readback_seconds'] = time.monotonic() - started
    if any(a['cohort'] == 'proofline' and a['outcome'] == 'FALSE ACCEPTED' for a in report['assignments']):
        report['status'] = 'TRUST GATE FAILED'
    s6.p.write_record(output / 'adjudications.json', amended)
    s6.p.write_record(output / 'report.json', report)
    summary = s6.summarize(manifest, report, json.loads((campaign / 'operator/rates.json').read_text()))
    s6.p.write_record(output / 'summary.json', summary)
    (output / 'results.md').write_text(s6.render(summary))
    print('Regression readback:', [(a['task'], a['model'], a['cohort'], a['original_outcome'], a['outcome']) for a in amended])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.campaign.resolve(), args.output.resolve())
    raise SystemExit(2 if result['status'] == 'TRUST GATE FAILED' else 0)
