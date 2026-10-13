"""Bounded, model-free native catalog qualification (no thread or turn)."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from checks import codex_live as live, host_probe as host
from checks.native_checks import write_record


def readback(codex, catalog, required, directory, *, timeout=60):
    directory, catalog = Path(directory), Path(catalog)
    record_path = directory / 'catalog-readback.json'
    if record_path.exists():
        raise ValueError('Refusing to overwrite catalog evidence')
    argv = [codex, '--no-daemon', 'app-server', '--listen', 'stdio://', '--strict-config',
            '-c', 'model_catalog_json='+host.toml(str(catalog)),
            '-c', 'sqlite_home='+host.toml(str(directory/'catalog-state')),
            '-c', 'mcp_servers={}', '-c', 'apps._default.enabled=false']
    started = time.monotonic()
    record = {'status': 'NOT VERIFIED', 'model_dispatches': 0, 'argv': argv,
              'catalog_sha256': host.sha256(catalog.read_bytes()), 'responses': [],
              'phase': 'initialize', 'timeout_seconds': timeout, 'stderr': ''}
    process = None
    stderr = bytearray()
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=directory, start_new_session=True)
        def send(value):
            process.stdin.write((json.dumps(value)+'\n').encode())
            process.stdin.flush()
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {
            'name': 'proofline_catalog', 'title': 'Proofline catalog qualification', 'version': '1'}}})
        request_id = 1
        buffer = b''
        size = 0
        models = []
        cursors = set()
        with selectors.DefaultSelector() as reader:
            reader.register(process.stdout, selectors.EVENT_READ, 'stdout')
            reader.register(process.stderr, selectors.EVENT_READ, 'stderr')
            while record['status'] != 'OBSERVED':
                remaining = timeout-(time.monotonic()-started)
                if remaining <= 0:
                    raise ValueError('Native catalog timeout during '+record['phase'])
                ready = reader.select(remaining)
                if not ready:
                    raise ValueError('Native catalog timeout during '+record['phase'])
                for key, _ in ready:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        reader.unregister(key.fileobj)
                        if key.data == 'stdout':
                            raise ValueError('Native catalog EOF during '+record['phase'])
                        continue
                    size += len(chunk)
                    if size > live.MAX_EVENTS_BYTES:
                        raise ValueError('Oversized native catalog output')
                    if key.data == 'stderr':
                        stderr.extend(chunk[:max(0, host.MAX_LOG_BYTES-len(stderr))])
                        continue
                    buffer += chunk
                    while b'\n' in buffer:
                        raw, buffer = buffer.split(b'\n', 1)
                        item = json.loads(raw)
                        if not isinstance(item, dict):
                            raise ValueError('Invalid native catalog message')
                        record['responses'].append(item)
                        if 'id' not in item:  # Notifications are not RPC responses.
                            continue
                        if item['id'] != request_id or 'result' not in item or 'error' in item:
                            raise ValueError('Native catalog RPC failed during '+record['phase'])
                        if request_id == 1:
                            record['initialization_seconds'] = time.monotonic()-started
                            send({'method': 'initialized', 'params': {}})
                            record['phase'] = 'model/list'
                            params = {'includeHidden': True, 'limit': 100}
                        else:
                            result = item['result']
                            models.extend(result['data'])
                            cursor = result.get('nextCursor')
                            if cursor is None:
                                for config in required.values():
                                    matches = [m for m in models if m['id'] == config['model'] and m['model'] == config['model']]
                                    if len(matches) != 1 or config['model_reasoning_effort'] not in [r['reasoningEffort'] for r in matches[0]['supportedReasoningEfforts']]:
                                        raise ValueError('Native catalog lacks exact model/effort: '+config['model'])
                                record.update(status='OBSERVED', phase='complete',
                                    access='NOT QUALIFIED: a completed inference turn is required')
                                break
                            if not isinstance(cursor, str) or cursor in cursors:
                                raise ValueError('Invalid native catalog pagination')
                            cursors.add(cursor)
                            params = {'includeHidden': True, 'limit': 100, 'cursor': cursor}
                        request_id += 1
                        send({'id': request_id, 'method': 'model/list', 'params': params})
        return record
    except Exception as error:
        record['error'] = host.redact(str(error))
        raise
    finally:
        if process is not None:
            record['exit_before_cleanup'] = process.poll()
            # Reap the whole group even if the server exited before its helpers.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            record['exit_code'] = process.returncode
            process.stdin.close(); process.stdout.close(); process.stderr.close()
        record.update(elapsed_seconds=time.monotonic()-started,
                      stderr=host.redact(stderr.decode(errors='replace')))
        write_record(record_path, record)
