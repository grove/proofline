"""Check existing working candidates; mocked boundaries never qualify a native host."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from checks import candidate_snapshot as snapshot, local_run as runner


class CheckOnlyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='proofline-check-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / 'source'
        self.repo.mkdir()
        (self.repo / 'tiny.py').write_bytes(b'print("base")\n')
        (self.repo / 'deleted.txt').write_text('deleted working file')
        (self.repo / '.gitignore').write_text('ignored/\n')
        runner.host.git(self.repo, 'init', '--quiet', '--template=')
        snapshot.freeze(self.repo)
        (self.repo / 'tiny.py').write_bytes(b'print("staged")\n')
        runner.host.git(self.repo, 'add', 'tiny.py')
        (self.repo / 'tiny.py').write_bytes(b'print("working")\r\n')
        (self.repo / 'deleted.txt').unlink()
        (self.repo / 'new file.bin').write_bytes(b'\x00\xffuntracked')
        (self.repo / 'alias').symlink_to('new file.bin')
        (self.repo / 'ignored').mkdir()
        (self.repo / 'ignored' / 'secret').write_bytes(b'excluded')
        (self.repo / 'tiny.py').chmod(0o755)
        self.before = runner.host.snapshot(self.repo)
        self.output = self.root / 'check'
        self.source = 'Keep the entire original request.\r\nIncluding this line.\r\n'

    def execute(self, checks=None, boundary_ready=True, unavailable=False, mutate=False,
                seconds=30, check_seconds=5, failure_details=None):
        checks = checks or [[sys.executable, 'tiny.py']]
        def boundary(codex, output, inputs, timeout, target):
            for name in ('canary.py', 'canary.json'):
                (inputs / name).write_text('fixture')
            return {'assessment': {'status': 'OBSERVED' if boundary_ready else 'NOT VERIFIED'}}
        def oracle(codex, inputs, private, receipts):
            def execute(argv, *, cwd, timeout):
                if unavailable:
                    raise OSError('native execution unavailable')
                if mutate:
                    (inputs / 'product' / 'tiny.py').write_text('changed')
                result = subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True, text=True)
                receipts.append({'kind': 'process_probe', 'argv': ['sandbox', json.dumps(argv)],
                                 'exit_code': result.returncode, 'timed_out': False,
                                 'stdout': result.stdout, 'stderr': result.stderr})
                return result
            return execute
        with patch.object(runner.platform, 'system', return_value='Darwin'), \
             patch.object(runner.sys, 'version_info', (3, 11)), \
             patch.object(runner.host, 'find_codex', return_value='/fake/codex'), \
             patch.object(runner.host, 'run_command', wraps=runner.host.run_command) as command, \
             patch.object(runner.host, 'probe_boundary', side_effect=boundary), \
             patch.object(runner, 'oracle_runner', side_effect=oracle), \
             patch.object(runner.coding, 'run', side_effect=AssertionError('coding dispatched')) as coding, \
             patch.object(runner.live, 'launch', side_effect=AssertionError('model dispatched')) as launch, \
             patch.object(runner.live, 'preferences', side_effect=AssertionError('model settings read')):
            original = command._mock_wraps
            command.side_effect = lambda argv, *args, **kw: (
                {'stdout': 'codex-cli 0.162.1', 'exit_code': 0, 'timed_out': False}
                if argv == ['/fake/codex', '--version'] else original(argv, *args, **kw))
            result = runner.check(self.repo, self.source, checks, self.output, seconds, check_seconds,
                                  failure_details=failure_details)
            coding.assert_not_called()
            launch.assert_not_called()
        self.assertEqual(runner.host.snapshot(self.repo), self.before)
        self.assertEqual(result['model_dispatches'], 0)
        self.assertEqual(result['limits']['model_dispatches'], 0)
        self.assertEqual(result['stages'], [])
        self.assertFalse(result['published'])
        self.assertFalse(result['merged'])
        return result

    def test_dirty_untracked_deleted_and_ignored_files_preserve_source(self):
        result = self.execute()
        self.assertEqual(result['status'], 'CHECKS PASSED', result)
        product = Path(result['candidate_path'])
        self.assertEqual((product / 'tiny.py').read_bytes(), b'print("working")\r\n')
        self.assertEqual((product / 'tiny.py').stat().st_mode & 0o777, 0o755)
        self.assertEqual((product / 'new file.bin').read_bytes(), b'\x00\xffuntracked')
        self.assertEqual(os.readlink(product / 'alias'), 'new file.bin')
        self.assertFalse((product / 'deleted.txt').exists())
        self.assertFalse((product / 'ignored').exists())
        self.assertEqual((product.parent / 'source.md').read_bytes(), self.source.encode())
        self.assertEqual(runner.inspect(self.output / 'report.json')['status'], 'CHECKS PASSED')
        # Later work in the live source is a different candidate, not a mutation of this evidence.
        (self.repo / 'tiny.py').write_text('new work')
        self.assertEqual(runner.inspect(self.output / 'report.json')['status'], 'CHECKS PASSED')

    def test_failed_unavailable_missing_tool_and_timeout_are_distinct(self):
        cases = [([sys.executable, '-c', 'raise SystemExit(3)'], {}, 'CHECKS FAILED'),
                 ([sys.executable, '-c', 'pass'], {'unavailable': True}, 'CHECKS UNAVAILABLE'),
                 ([str(self.root / 'missing')], {}, 'CHECKS UNAVAILABLE'),
                 ([sys.executable, '-c', 'import time; time.sleep(3)'],
                  {'check_seconds': 0.05}, 'CHECKS UNAVAILABLE')]
        for index, (argv, options, expected) in enumerate(cases):
            with self.subTest(expected=expected, argv=argv):
                self.output = self.root / ('check-' + str(index))
                result = self.execute([argv], **options)
                self.assertEqual(result['status'], expected, result)
                self.assertEqual(runner.inspect(self.output / 'report.json')['status'], expected)

    def test_freeze_source_command_and_receipt_tampering_is_stale(self):
        result = self.execute([[sys.executable, '-c', 'pass']])
        path = self.output / 'report.json'
        for relative in ('inputs/product/tiny.py', 'inputs/source.md', 'inputs/checks.json', 'evidence.json'):
            target = self.output / relative
            original = target.read_bytes()
            mode = target.stat().st_mode & 0o777
            with self.subTest(path=relative):
                self.assertEqual(runner.inspect(path)['status'], 'CHECKS PASSED')
                target.write_bytes(b'tampered')
                self.assertEqual(runner.inspect(path)['status'], 'STALE CHECKS')
                target.unlink()
                self.assertEqual(runner.inspect(path)['status'], 'STALE CHECKS')
                target.write_bytes(original)
                target.chmod(mode)
                self.assertEqual(runner.inspect(path)['status'], 'CHECKS PASSED')
        result['observations'][0]['receipts'][0]['exit_code'] = 17
        path.write_text(json.dumps(result))
        self.assertEqual(runner.inspect(path)['status'], 'STALE CHECKS')

    def test_refuses_unverified_boundary_and_candidate_mutation(self):
        result = self.execute(boundary_ready=False)
        self.assertEqual(result['status'], 'EXECUTION UNAVAILABLE')
        self.assertEqual(result['observations'], [])
        self.output = self.root / 'mutation'
        result = self.execute(mutate=True)
        self.assertEqual(result['status'], 'EXECUTION UNAVAILABLE')
        self.assertIn('Frozen check inputs changed', result['error'])

    def test_output_in_source_and_invalid_inputs_create_nothing(self):
        for output in (self.repo, self.repo / 'new-output'):
            with self.assertRaisesRegex(ValueError, 'outside the source'):
                runner.check(self.repo, self.source, [[sys.executable, '-c', 'pass']], output)
        for budget in (0, -1, float('nan'), float('inf'), 3601, True):
            with self.assertRaises(ValueError):
                runner.check(self.repo, self.source, [[sys.executable, '-c', 'pass']], self.output, budget)
        with self.assertRaises(ValueError):
            runner.check(self.repo, ' ', [[sys.executable, '-c', 'pass']], self.output)
        with self.assertRaises(ValueError):
            runner.check(self.repo, self.source, [['echo', 'relative executable']], self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(runner.host.snapshot(self.repo), self.before)

    def test_unsupported_platform_is_recorded_without_execution(self):
        with patch.object(runner.platform, 'system', return_value='Linux'), \
             patch.object(runner.host, 'find_codex') as codex:
            result = runner.check(self.repo, self.source, [[sys.executable, '-c', 'pass']], self.output)
        codex.assert_not_called()
        self.assertEqual(result['status'], 'EXECUTION UNAVAILABLE')
        self.assertIn('macOS', result['error'])
        self.assertEqual(runner.host.snapshot(self.repo), self.before)

    def test_output_in_external_git_metadata_is_refused_without_writes(self):
        metadata = self.root / 'source-metadata'
        runner.host.git(self.repo, 'init', '--quiet', '--separate-git-dir', str(metadata))
        before = runner.host.snapshot(metadata)
        with self.assertRaisesRegex(ValueError, 'outside source Git metadata'):
            runner.check(self.repo, self.source, [[sys.executable, '-c', 'pass']], metadata / 'check')
        self.assertEqual(runner.host.snapshot(metadata), before)

    def test_existing_evidence_is_never_overwritten(self):
        self.execute()
        before = runner.host.snapshot(self.output)
        with self.assertRaises(FileExistsError):
            runner.check(self.repo, self.source, [[sys.executable, '-c', 'pass']], self.output)
        self.assertEqual(runner.host.snapshot(self.output), before)

    def test_shared_check_loop_stops_at_the_cumulative_budget(self):
        record = {'checks': [[sys.executable, '-c', 'pass']] * 2,
                  'limits': {'seconds': 5, 'check_seconds': 3},
                  'observations': [], 'python': sys.executable, 'snapshot': 'fixture'}
        inputs = self.root / 'inputs'
        inputs.mkdir()
        clock = [0]
        def oracle(*args):
            def execute(argv, *, cwd, timeout):
                self.assertEqual(timeout, 3)
                clock[0] = 5
                return subprocess.CompletedProcess(argv, 0, '', '')
            return execute
        with patch.object(runner, 'oracle_runner', side_effect=oracle) as execute, \
             patch.object(runner.host, 'snapshot', return_value={'sha256': 'fixture'}), \
             patch.object(runner.time, 'monotonic', side_effect=lambda: clock[0]):
            runner.execute_checks(record, inputs, self.root, '/fake/codex', 0, lambda: None)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(record['status'], 'CHECKS UNAVAILABLE')
        self.assertEqual([item['status'] for item in record['observations']], ['PASSED', 'UNAVAILABLE'])

    def test_cumulative_budget_exhaustion_never_dispatches_checks(self):
        ticks = iter([0] + [100] * 1000)
        with patch.object(runner.time, 'monotonic', side_effect=lambda: next(ticks)):
            result = self.execute(seconds=0.001)
        self.assertEqual(result['status'], 'EXECUTION UNAVAILABLE')
        self.assertEqual(result['observations'], [])

    def test_failed_check_has_actionable_feedback_and_host_receipt(self):
        argv = [sys.executable, '-c',
                'import sys;print("Unicode rejected",file=sys.stderr);sys.exit(5)']
        meta = [{'index': 0, 'outcome_ids': ['R2'],
                 'expected': 'Unicode accepted', 'observed': 'Unicode rejected'}]
        result = self.execute([argv], failure_details=meta)
        self.assertEqual(result['status'], 'CHECKS FAILED')
        self.assertEqual(result['model_dispatches'], 0)
        self.assertEqual(result['failure_details'], meta)
        self.assertEqual(result['feedback']['source_sha256'],
                         runner.host.sha256(self.source.encode('utf-8')))
        self.assertEqual(result['feedback']['candidate_commit'], result['candidate_commit'])
        row = result['feedback']['checks'][0]
        self.assertEqual(row['argv'], argv)
        self.assertEqual(row['exit_code'], 5)
        self.assertGreaterEqual(row['elapsed_seconds'], 0.0)
        self.assertIn('Unicode rejected', row['stderr_excerpt'])
        self.assertEqual(row['outcome_ids'], ['R2'])
        self.assertEqual(row['caller_annotation']['expected'], 'Unicode accepted')
        receipt = self.output / row['receipt_ref']
        self.assertTrue(receipt.is_file())
        self.assertEqual(runner.host.sha256(receipt.read_bytes()),
                         result['observations'][0]['receipt_sha256'])
        self.assertEqual(runner.inspect(self.output / 'report.json')['status'], 'CHECKS FAILED')
        self.assertTrue((self.output / 'inputs/failure-details.json').read_text())
        receipt.write_text('{"faked": true}')
        reread = runner.inspect(self.output / 'report.json')
        self.assertEqual(reread['status'], 'STALE CHECKS')
        self.assertIn('stale', reread['feedback']['headline'].lower())

    def test_spoofed_expected_observed_never_becomes_native_evidence(self):
        argv = [sys.executable, '-c',
                'import sys;print("actual assertion failed",file=sys.stderr);sys.exit(3)']
        meta = [{'index': 0, 'outcome_ids': ['R7'],
                 'expected': 'made up expected', 'observed': 'fake observed'}]
        result = self.execute([argv], failure_details=meta)
        self.assertEqual(result['status'], 'CHECKS FAILED')
        self.assertEqual(result['feedback']['checks'][0]['outcome_ids'], ['R7'])
        self.assertNotIn('caller_annotation', result['feedback']['checks'][0])
        self.assertIn('not corroborated', result['feedback']['checks'][0]['annotation_warning'])
        self.assertNotIn('made up expected', '\n'.join(runner.feedback.format_lines(result)))
        self.assertIn('actual assertion failed',
                      result['feedback']['checks'][0]['stderr_excerpt'])

    def test_invalid_metadata_is_refused_before_any_native_or_model_call(self):
        with self.assertRaisesRegex(ValueError, 'Expected and observed'):
            self.execute(failure_details=[{'index': 0, 'expected': 'only one'}])
        self.assertFalse(self.output.exists())
        self.assertEqual(runner.host.snapshot(self.repo), self.before)

    def test_missing_tool_unavailable_feedback_is_not_product_failure(self):
        missing = str(self.root / 'no-such-test-executable')
        result = self.execute([[missing]])
        self.assertEqual(result['status'], 'CHECKS UNAVAILABLE')
        self.assertEqual(result['feedback']['checks'][0]['status'], 'UNAVAILABLE')
        self.assertIn('could not be observed', result['feedback']['checks'][0]['reason'])
        self.assertIn('unavailable', runner.feedback.format_lines(result)[0].lower())
        self.assertEqual(runner.inspect(self.output / 'report.json')['status'], 'CHECKS UNAVAILABLE')

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PROOFLINE_NATIVE_TESTS') == '1',
                         'opt-in macOS native check-only test')
    def test_native_cli_denies_source_writes_candidate_writes_and_network(self):
        source = self.root / 'request.md'
        source.write_bytes(self.source.encode())
        commands = self.root / 'checks.json'
        commands.write_text(json.dumps([[str(Path(sys.executable).resolve()), '-B', '-c',
            'import errno,socket\nfrom pathlib import Path\n'
            'assert Path("tiny.py").read_bytes()==b\'print("working")\\r\\n\'\n'
            'assert Path("new file.bin").read_bytes()==b"\\x00\\xffuntracked"\n'
            f'for p in (Path("tiny.py"),Path({str(self.repo / "tiny.py")!r})):\n'
            ' try: p.write_text("tampered")\n'
            ' except OSError as e: assert e.errno in (errno.EPERM,errno.EACCES,errno.EROFS)\n'
            ' else: raise AssertionError("write permitted")\n'
            'try: socket.socket().connect(("127.0.0.1",9))\n'
            'except OSError as e: assert e.errno in (errno.EPERM,errno.EACCES)\n'
            'else: raise AssertionError("network permitted")\n']]))
        process = subprocess.run([sys.executable, '-B', str(runner.host.ROOT / 'proofline.py'), 'check',
            '--repo', str(self.repo), '--source', str(source), '--checks', str(commands),
            '--output', str(self.output), '--seconds', '30', '--check-seconds', '5'],
            capture_output=True, text=True, timeout=45)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        record = runner.inspect(self.output / 'report.json')
        self.assertEqual(record['model_dispatches'], 0)
        self.assertEqual(record['status'], 'CHECKS PASSED')
        self.assertEqual(runner.host.snapshot(self.repo), self.before)
        self.assertIn('not certified', process.stdout)


if __name__ == '__main__':
    unittest.main()
