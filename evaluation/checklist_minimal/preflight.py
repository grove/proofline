"""One bounded, model-free prerequisite check; no live dispatch interface."""
import json
from pathlib import Path
import sys
import tarfile
import time

from checks import candidate_snapshot as snapshots, host_probe as host
from checks.native_checks import write_record
from evaluation.recovery.grader import invoke

HERE = Path(__file__).resolve().parent
CODEX = '/opt/homebrew/bin/codex'


def preflight(output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    spec = json.loads((HERE / 'protocol.json').read_text())
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    result = {'study_id': spec['study_id'], 'status': 'STOPPED_NOT_QUALIFIED',
              'freeze_sha256': host.sha256((HERE / 'FREEZE.json').read_bytes()),
              'model_dispatches': 0, 'live_authorization': None,
              'assignments': [{'sequence': i+1, 'task': task, 'arm': arm,
                               'status': 'NOT_EXECUTED', 'model_dispatches': 0,
                               'usage': None, 'total_seconds': None}
                              for i, (task, arm) in enumerate(spec['order'])]}
    deadline = started + spec['limits']['preflight_seconds']
    def remaining():
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise ValueError('Bounded model-free preflight exhausted')
        return min(15, seconds)
    try:
        for name, digest in freeze['sha256'].items():
            if host.sha256((HERE.parent.parent / name).read_bytes()) != digest:
                raise ValueError('Frozen input drift: '+name)
        for name, path in [('python', Path(sys.executable).resolve()),
                           ('codex', Path(CODEX).resolve())]:
            if host.sha256(path.read_bytes()) != freeze['runtime_sha256'][name]:
                raise ValueError('Frozen runtime drift: '+name)
        version = host.run_command([CODEX, '--version'], output, remaining())
        result['version_receipt'] = version
        if not host.succeeded(version) or version['stdout'].strip() != 'codex-cli 0.162.1':
            raise ValueError('Supported Codex CLI unavailable')
        inputs = output / 'boundary-inputs'
        inputs.mkdir()
        product = inputs / 'product'
        product.mkdir()
        task = spec['tasks'][0]
        with tarfile.open(HERE / 'inputs' / (task['id']+'-base.tar')) as archive:
            archive.extractall(product, filter='data')
        host.git(product, 'init', '--quiet', '--template=')
        snapshots.freeze(product)
        if host.git(product, 'rev-parse', 'HEAD^{tree}') != task['trees']['base']:
            raise ValueError('Base archive tree mismatch')
        source = (HERE / task['request_file']).read_bytes()
        (inputs / 'source.md').write_bytes(source)
        (inputs / 'accepted-input.md').write_text(spec['common_guidance'])
        boundary = output / 'boundary'
        boundary.mkdir()
        observation = host.probe_boundary(CODEX, boundary, inputs, remaining(),
                                          product / 'schedule/__init__.py')
        write_record(boundary / 'report.json', observation)
        result['boundary'] = observation['assessment']
        if result['boundary']['status'] != 'OBSERVED':
            raise ValueError('Existing native boundary unavailable')
        # Run original tests unchanged; missing dependencies are prerequisites, not defects.
        script = "import runpy,sys\nsys.argv=['unittest','test_schedule']\nrunpy.run_module('unittest',run_name='__main__')\n"
        tests = invoke(product, script, output / 'original-tests', seconds=remaining())
        result['original_tests'] = tests
        if not tests['available'] or tests['receipt'].get('exit_code') != 0:
            raise ValueError('Unchanged original repository suite cannot run cleanly; no qualification or live dispatch')
        result['blocker'] = 'Prerequisites observed only; independent source assessment, controls, writable role and installation qualification still required'
    except (OSError, ValueError, RuntimeError) as error:
        result['blocker'] = str(error)
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['remaining_qualification'] = ['independent source-to-oracle review',
            'reference/alternative/omission controls', 'typed package build/install',
            'writable worker role', 'model-free catalog readback']
        assert len(result['assignments']) == 8
        assert all(row['status'] == 'NOT_EXECUTED' for row in result['assignments'])
        assert result['model_dispatches'] == 0 and result['live_authorization'] is None
        write_record(output / 'preflight.json', result)
    return result


if __name__ == '__main__':
    result = preflight(Path(sys.argv[1]))
    print(result['status'] + ': ' + result['blocker'])
    raise SystemExit(1)
