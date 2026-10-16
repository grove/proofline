"""Fresh model-free host/worker/grader/producer qualification using #16 controls."""
import argparse
import json
from pathlib import Path
import time

from checks import codex_catalog, host_probe as host
from checks.native_checks import write_record
from evaluation.issue52 import qualify
from evaluation.matched import study as boundaries
from evaluation.matched_v3 import preflight, study as producer
from evaluation.sol_luna.grader import bound_module


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    result = {'status': 'IN_PROGRESS', 'model_dispatches': 0, 'live_dispatch_allowed': False,
              'input_sha256': qualify.input_identities(), 'boundaries': {}}
    write_record(output / 'results.json', json.loads((qualify.HERE / 'results-template.json').read_text()))
    sibling = output / 'qualification/sibling.txt'
    sibling.parent.mkdir()
    sibling.write_text('Private sibling canary; forbidden to the worker.\n')
    runner = bound_module(boundaries, ROOT=qualify.ROOT, STORE=output, CODEX=qualify.CODEX)
    runner.read_protocol = lambda: {'model': qualify.spec()['model_proposal']}
    try:
        catalog = output / 'model-catalog.json'
        catalog.write_bytes((Path.home() / '.codex/models_cache.json').read_bytes())
        result['catalog'] = codex_catalog.readback(qualify.CODEX, catalog,
                           {'study': qualify.spec()['model_proposal']}, output, timeout=60)
        result['catalog_sha256'] = host.sha256(catalog.read_bytes())
        result['producer_sha256'] = {name: host.sha256(path.read_bytes())
                                    for name, path in producer.producer_files().items()}
        inputs = output / 'boundary-inputs'
        (inputs / 'product').mkdir(parents=True)
        (inputs / 'product/app.py').write_text('Original read-only grader canary.\n')
        host.git(inputs / 'product', 'init', '--quiet', '--template=')
        qualify.snapshots.freeze(inputs / 'product')
        (inputs / 'source.md').write_text('Complete original request canary.\n')
        result['boundaries']['grader'] = runner.boundary(inputs, output / 'grader-boundary')
        result['boundaries']['worker'] = runner.boundary(inputs, output / 'worker-boundary', worker=True)
        preflight.check_adapter_roundtrip(output / 'roundtrip', producer.install_tool,
                                         producer.selected_checks, runner.boundary, codex=qualify.CODEX)
        report = output / 'roundtrip/qualification.json'
        result['roundtrip_sha256'] = host.sha256(report.read_bytes())
        result['roundtrip'] = json.loads(report.read_text())
        if result['input_sha256'] != qualify.input_identities():
            raise ValueError('Qualification input drift')
        if result['producer_sha256'] != {name: host.sha256(path.read_bytes())
                                         for name, path in producer.producer_files().items()}:
            raise ValueError('Producer drift')
        result['status'] = 'NATIVE_CONTROLS_OBSERVED_REVIEW_REQUIRED'
    except BaseException as error:
        result.update(status='STOPPED_NOT_QUALIFIED', blocker=str(error))
        raise
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        write_record(output / 'qualification.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.output.resolve())
    print(json.dumps({'status': result['status'], 'model_dispatches': 0}))


if __name__ == '__main__':
    main()
