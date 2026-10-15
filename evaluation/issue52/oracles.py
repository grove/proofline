"""Finite source-derived probes, withheld from coding workers; no whole-source verdict.

Authored separately from worker attempts. Layout/API compatibility is limited to
this project's existing seams; independent human adjudication is still required.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile

SOURCE = 'Reject blank names.\nAccept Unicode names.\n'
CHECKS = [['/usr/bin/true']]


def mapping():
    return {'schema_version': 1, 'source_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
            'requirements': [{'id': 'R'+str(i), 'statement': text,
                              'source_refs': [{'source_id': 'S1', 'line_start': i,
                                               'line_end': i, 'quote': text}],
                              'checks': [{'index': 0, 'argv': CHECKS[0]}] if i == 1 else []}
                             for i, text in enumerate(SOURCE.splitlines(), 1)]}


def record(value=None, state='PASSED', status='CHECKS PASSED'):
    return {'kind': 'bounded_local_check', 'feedback_version': 1, 'status': status,
            'source_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
            'candidate_commit': 'commit', 'candidate_tree': 'tree', 'snapshot': 'snapshot',
            'checks': CHECKS, 'promise_mapping': value,
            'observations': [{'argv': CHECKS[0], 'status': state, 'returncode': 0 if state == 'PASSED' else 7,
                              'elapsed_seconds': 0.125, 'receipts': [{'exit_code': 7, 'timed_out': False,
                              'stdout': '', 'stderr': 'AssertionError: actual rejection'}]}]}


def rejects(call):
    try:
        call()
    except (ValueError, TypeError):
        return
    raise AssertionError('Untrusted input was accepted')


def feedback_receipts():
    from checks import feedback as f
    rec = record(state='FAILED', status='CHECKS FAILED')
    rec.pop('promise_mapping')
    with tempfile.TemporaryDirectory() as tmp:
        f.save_receipt(rec['observations'][0], Path(tmp), 0)
        assert f.receipts_intact(rec, Path(tmp))
        view = f.summarize(rec)
        row = view['checks'][0]
        assert (row['argv'], row['exit_code'], row['elapsed_seconds']) == (CHECKS[0], 7, 0.125)
        assert view['source_sha256'] == rec['source_sha256'] and view['candidate_commit'] == 'commit'
        assert row['stderr_ref'] and 'actual rejection' in row['stderr_excerpt']
        assert 'caller_annotation' not in row
        Path(tmp, 'receipts/check-000.json').write_text('{}')
        assert not f.receipts_intact(rec, Path(tmp))


def feedback_annotations():
    from checks import feedback as f
    details = f.validate_failure_details([{'index': 0, 'outcome_ids': ['R2'],
                                         'expected': 'acceptance', 'observed': 'invented result'}], CHECKS)
    rec = record(state='FAILED', status='CHECKS FAILED')
    f.attach_details(rec['observations'][0], details, 0)
    row = f.summarize(rec)['checks'][0]
    assert row['outcome_ids'] == ['R2'] and 'caller_annotation' not in row
    rejects(lambda: f.validate_failure_details([{'index': 0, 'expected': 'alone'}], CHECKS))
    details[0]['observed'] = 'actual rejection'
    f.attach_details(rec['observations'][0], details, 0)
    assert 'unverified' in f.summarize(rec)['checks'][0]['caller_annotation']['expected_provenance']


def feedback_states():
    from checks import feedback as f
    for flag in ('timed_out', 'stdout_truncated', 'stderr_truncated', 'error'):
        rec = record(state='UNAVAILABLE', status='CHECKS UNAVAILABLE')
        rec['observations'][0]['receipts'][0][flag] = True
        view = f.summarize(rec)
        assert view['checks'][0]['status'] == 'UNAVAILABLE'
        assert 'caller_annotation' not in view['checks'][0]
        assert view['status'] == 'CHECKS UNAVAILABLE'
    for status in ('STALE CHECKS', 'EXECUTION UNAVAILABLE'):
        assert f.summarize({'status': status})['status'] == status


def feedback_bounded():
    from checks import feedback as f
    rec = record(); rec.pop('promise_mapping')
    assert len(f.format_lines(rec)) <= 2
    rec['status'] = 'CHECKS FAILED'
    rec['observations'] *= 10
    for entry in rec['observations']:
        entry['status'] = 'FAILED'
        entry['receipts'][0]['stderr'] = 'x' * 10000
    assert len('\n'.join(f.format_lines(rec))) < 4000


def mapping_validation():
    from checks import promise_evidence as p
    value = mapping()
    assert p.validate(value, SOURCE, CHECKS)['source_sha256'] == value['source_sha256']
    for kind in ('source', 'quote', 'id', 'argv'):
        bad = copy.deepcopy(value)
        if kind == 'source': bad['source_sha256'] = '0' * 64
        if kind == 'quote': bad['requirements'][0]['source_refs'][0]['quote'] = 'forged'
        if kind == 'id': bad['requirements'][1]['id'] = 'R1'
        if kind == 'argv': bad['requirements'][0]['checks'][0]['argv'] = ['/bin/false']
        rejects(lambda: p.validate(bad, SOURCE, CHECKS))
    rejects(lambda: p.bind_candidate({**value, 'candidate_tree': 'other'}, 'tree'))


def mapping_outcomes():
    from checks import promise_evidence as p
    value = p.validate(mapping(), SOURCE, CHECKS)
    for state, status, expected in [('PASSED', 'CHECKS PASSED', 'LINKED CHECKS PASSED (limited evidence)'),
                                    ('FAILED', 'CHECKS FAILED', 'CHECK FAILED'),
                                    ('UNAVAILABLE', 'CHECKS UNAVAILABLE', 'CHECK UNAVAILABLE')]:
        view = p.summarize(record(value, state, status))
        assert [r['status'] for r in view['requirements']] == [expected, 'NOT DEMONSTRATED']
        assert view['coverage_completeness'] == 'UNKNOWN'
    assert p.summarize(record(value, status='STALE CHECKS'))['requirements'][0]['status'] != 'LINKED CHECKS PASSED (limited evidence)'
    assert p.format_lines({'status': 'CHECKS PASSED'}) == []


def mapping_advisory():
    from checks import promise_evidence as p
    value = mapping(); value['requirements'][1]['oracle'] = 'A proposed Unicode assertion'
    view = p.summarize(record(p.validate(value, SOURCE, CHECKS)))
    assert view['coverage_completeness'] == 'UNKNOWN'
    assert not view['same_agent_review']['reported_performed']
    assert 'unverified' in view['requirements'][1]['oracle_authority']
    assert view['requirements'][1]['status'] == 'NOT DEMONSTRATED'


def package():
    from checks import intentline_advisory as a
    files = {p.name: p.read_bytes() for p in Path('fixtures').iterdir()}
    source = files['source-S1.txt'].decode()
    return a, files, source


def adapter_integrity():
    a, files, source = package()
    a.compile_package(files, source, CHECKS)
    for name in files:
        bad = dict(files); bad[name] += b' '
        rejects(lambda: a.compile_package(bad, source, CHECKS))
    rejects(lambda: a.compile_package(files, source+'changed', CHECKS))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, raw in files.items(): (root / name).write_bytes(raw)
        a.load_export(root, source, CHECKS)
        (root / 'source-S1.txt').unlink()
        (root / 'source-S1.txt').symlink_to(root / 'contract.json')
        rejects(lambda: a.load_export(root, source, CHECKS))


def adapter_links():
    a, files, source = package()
    result = a.compile_package(files, source, CHECKS)
    from checks import promise_evidence as p
    rec = record(result['mapping']); rec['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    rec['intentline_advisory'] = result['metadata']
    assert all(r['status'] == 'NOT DEMONSTRATED' for r in p.summarize(rec)['requirements'])
    assert result['metadata']['coverage_completeness'] == 'UNKNOWN'
    rejects(lambda: a.compile_package(files, source, CHECKS, {'R1': [{'index': 0, 'argv': ['/bin/false']}]}))
    rejects(lambda: a.compile_package(files, source, CHECKS, {'R999': []}))
    assert result['metadata']['execution_authority'] == 'not_established'
    assert result['metadata']['requirements'][0]['planned_evidence']


def hint_actions():
    from checks import promise_evidence as p
    value = mapping(); value['requirements'][1]['oracle'] = 'Unicode normalization boundary'
    rec = record(p.validate(value, SOURCE, CHECKS))
    text = '\n'.join(p.format_lines(rec))
    assert 'R2' in text and 'NOT DEMONSTRATED' in text and 'unverified' in text.lower()
    assert 'Unicode normalization boundary' in text and 'S1:2' in text
    assert 'argv' in text and 'rerun' in text.lower()
    assert '/usr/bin/true' not in text and 'coverage UNKNOWN' in text
    value['requirements'][1].pop('oracle')
    text = '\n'.join(p.format_lines(record(p.validate(value, SOURCE, CHECKS))))
    assert 'No source-grounded check plan supplied' in text
    assert 'Unicode normalization boundary' not in text


def hint_states():
    from checks import promise_evidence as p
    value = p.validate(mapping(), SOURCE, CHECKS)
    for state, status in [('FAILED', 'CHECKS FAILED'), ('UNAVAILABLE', 'CHECKS UNAVAILABLE')]:
        rec = record(value, state, status)
        text = '\n'.join(p.format_lines(rec))
        assert ('CHECK FAILED' if state == 'FAILED' else 'CHECK UNAVAILABLE') in text
    value['requirements'][1]['oracle'] = 'must be suppressed when stale'
    text = '\n'.join(p.format_lines(record(value, status='STALE CHECKS')))
    assert 'must be suppressed' not in text and 'Restore' in text
    assert p.format_lines({'status': 'CHECKS PASSED'}) == []


CASES = {
    'feedback': ['feedback_receipts', 'feedback_annotations', 'feedback_states', 'feedback_bounded'],
    'promise-mapping': ['mapping_validation', 'mapping_outcomes', 'mapping_advisory'],
    'intentline-adapter': ['adapter_integrity', 'adapter_links'],
    'next-check-hints': ['hint_actions', 'hint_states', 'mapping_outcomes'],
}
