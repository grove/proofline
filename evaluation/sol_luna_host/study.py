"""Continue issue #32 using its frozen runner and corrected catalog qualification."""
import inspect
import json
import os
from pathlib import Path
import time
import zipfile

from checks import codex_catalog
from checks.native_checks import write_record
from evaluation.sol_luna import grader, study as original

HERE = Path(__file__).resolve().parent
STORE = original.ROOT / '.proofline/issue32-sol-luna-high-lenient'
runner = grader.bound_module(original, HERE=HERE, STORE=STORE)
runner.native_boundary = grader.bound_module(original.infrastructure,
    corpus=original.corpus, grader=grader, STORE=STORE)


def catalog_readback(directory):
    # The denial canary needs a real result file; the old runner writes it only in finally.
    write_record(directory/'results.json', {'status': 'PREPARING', 'model_dispatches': 0,
                                          'assignments': runner.ledger()})
    return codex_catalog.readback(runner.CODEX, HERE/'model-catalog.json',
                                 runner.protocol()['models'], directory)


runner.catalog_readback = catalog_readback


def validate_handoff(control):
    stages = control['stages']
    expected = [('planning','gpt-6.1-sol'), ('implementation','gpt-6-luna'),
                ('verification','gpt-6.1-sol'), ('correction','gpt-6-luna')]
    if (control['status'] != 'OBSERVED' or len(stages) != 4 or
            any((stage['stage'],stage['model']) != identity or stage['status'] != 'OBSERVED' or
                stage['reasoning_effort'] != 'high' for stage,identity in zip(stages,expected)) or
            len({stage['thread_id'] for stage in stages[:3]}) != 3 or
            stages[1]['thread_id'] != stages[3]['thread_id']):
        raise ValueError('Prior native handoff does not qualify exact models and independent/same-Luna threads')


def handoff_control():
    # Reuse the completed native control, not the interrupted primary assignment.
    prior = runner.ROOT/'evaluation/results/issue32-qualified-stopped'
    result = json.loads((prior/'results.json').read_text())
    control = result['handoff_qualification']
    validate_handoff(control)
    folder = STORE/'qualification/handoff'
    folder.mkdir(parents=True, exist_ok=False)
    write_record(folder/'result.json', {
        'status':'OBSERVED', 'stages':[], 'model_dispatches':0,
        'scope':'Reused exact previously completed native control; no new efficacy observation or inference',
        'source_declaration':result['study'],
        'source_freeze_sha256':json.loads((prior/'manifest.json').read_text())['identities']['freeze_sha256'],
        'source_control':control,
        'elapsed_seconds':0, 'cost_usd':None})


# Historical execution is frozen; change only its three declared budget expressions.
episode_source = inspect.getsource(original.episode)
for before,after in (
    ('allowance(120)', "allowance(protocol()['limits']['planning_seconds'])"),
    ('allowance(120, reserve=90)', "allowance(protocol()['limits']['verification_seconds'], reserve=90)"),
    ('allowance(600 - model_seconds - (240 if verification else 0), reserve=180)',
     "allowance(protocol()['limits']['model_seconds'] - model_seconds - (protocol()['limits']['verification_model_reserve_seconds'] if verification else 0), reserve=180)")):
    if episode_source.count(before) != 1:
        raise ValueError('Frozen episode budget seam changed')
    episode_source = episode_source.replace(before,after)
exec(compile(episode_source, str(HERE/'study.py')+':declared_episode', 'exec'), runner.__dict__)


def approved():
    """Authorization binds this freeze and its actual declared campaign limit."""
    approval = json.loads((STORE/'approval.json').read_text()) if (STORE/'approval.json').exists() else {}
    limits = runner.protocol()['limits']
    if (approval.get('freeze_sha256') != runner.identities()['freeze_sha256'] or
            approval.get('study_id') != runner.protocol()['study_id'] or
            approval.get('max_native_dispatches') != limits['max_native_dispatches'] or
            approval.get('max_seconds') != limits['max_campaign_seconds'] or
            not isinstance(approval.get('user_authorization'),str) or not approval['user_authorization'].strip()):
        raise ValueError('Explicit authorization required for this fresh freeze and declared live limits')
    return approval


def publish_record(destination):
    """Archive the continuation freeze under its own path, retaining the original."""
    destination.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(destination/'raw-evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(STORE.rglob('*')):
            name = path.relative_to(STORE)
            if 'catalog-state' in name.parts:
                continue
            if path.is_symlink():
                entry = zipfile.ZipInfo(str(name))
                entry.create_system = 3
                entry.external_attr = 0o120777 << 16
                archive.writestr(entry,os.readlink(path))
            elif path.is_file():
                archive.write(path,str(name))
                if path.parent == STORE and path.suffix == '.json':
                    (destination/path.name).write_bytes(path.read_bytes())
    with zipfile.ZipFile(destination/'frozen-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in json.loads((HERE/'FREEZE.json').read_text())['sha256']:
            archive.write(runner.ROOT/name,name)
        archive.write(HERE/'FREEZE.json',str((HERE/'FREEZE.json').relative_to(runner.ROOT)))
        for name,path in runner.infrastructure.producer_files().items():
            archive.write(path,'intentline/'+name)
        archive.write(runner.infrastructure.PRODUCER/'LICENSE','intentline/LICENSE')
    write_record(destination/'hashes.json',{str(p.relative_to(destination)):runner.host.sha256(p.read_bytes())
        for p in destination.rglob('*') if p.is_file()})


runner.handoff_control = handoff_control
runner.approved = approved
runner.publish_record = publish_record


if __name__ == '__main__':
    raise SystemExit(runner.main())
