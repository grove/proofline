"""Small private public-interface probes; all other obligations need source review.

No newly invented function/module ABI is required. An undiscovered optional
interface is unknown, never a defect; the frozen source assessment accepts
source-faithful alternatives with actual observations.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main(task):
    product = Path(sys.path[0])
    python = str(Path(sys.executable).resolve())
    receipts, cases = [], []
    os.environ.update(PATH='/Library/Developer/CommandLineTools/usr/bin:'
                      '/opt/homebrew/bin:/usr/bin:/bin', GIT_CONFIG_NOSYSTEM='1',
                      GIT_CONFIG_GLOBAL='/dev/null',
                      GIT_EXEC_PATH='/Library/Developer/CommandLineTools/usr/libexec/git-core')

    def run(argv, cwd=product):
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=40)
        receipts.append({'argv': argv, 'cwd': str(cwd), 'exit_code': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        return result

    def cli(*args):
        # Match #38's native Git mapping inside each child interpreter.
        launch = ('import os,runpy,sys; os.defpath="/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin"; '
                  'sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name="__main__")')
        return run([python, '-B', '-c', launch, str(product / 'proofline.py'), *map(str, args)])

    def case(identifier, passed):
        cases.append({'id': identifier, 'passed': passed})

    case('status-interface', cli('status', '--help').returncode == 0)
    if task == 10:
        case('run-interface', cli('run', '--help').returncode == 0)
        # Follow local imports from the supported entry points, across renamed helpers.
        pending = ['proofline', 'checks.local_run']; seen = set(); forbidden = []
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            path = product / (name.replace('.', '/') + '.py')
            if not path.is_file():
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or '']
                    modules += [(node.module + '.' if node.module else '') + alias.name
                                for alias in node.names]
                for module in modules:
                    if 's6_baseline' in module or 's6_compare' in module:
                        forbidden.append(module)
                    pending.append(module)
        case('no-s6-dependency', not forbidden)
    else:
        help_text = cli('check', '--help')
        case('check-interface', help_text.returncode == 0)
        # The pre-existing run option names are one supported assembly recipe.
        # A different new check interface needs independent source assessment.
        if help_text.returncode or any(flag not in help_text.stdout for flag in
                                      ('--repo', '--source', '--checks', '--output')):
            case('native-check', None)
        else:
            scratch = Path.cwd()
            repo = scratch / 'source'; repo.mkdir()
            (repo / 'app.txt').write_bytes(b'base\n')
            run(['git', 'init', '--quiet', '--template='], repo)
            run(['git', 'add', '.'], repo)
            run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid',
                 'commit', '--quiet', '-m', 'base'], repo)
            (repo / 'app.txt').write_bytes(b'dirty\r\n')
            (repo / 'untracked.bin').write_bytes(b'\x00\xff')
            from checks import host_probe
            before = host_probe.snapshot(repo)
            source = 'Keep this complete original request.\nRetain Unicode: José.\n'
            source_file = scratch / 'source.md'; source_file.write_text(source)
            command = [python, '-B', '-c', 'pass'] if task != 14 else [
                python, '-B', '-c', 'import sys; print("observed failure", file=sys.stderr); raise SystemExit(7)']
            checks_file = scratch / 'checks.json'; checks_file.write_text(json.dumps([command]))
            output = scratch / 'check'
            result = cli('check', '--repo', repo, '--source', source_file,
                         '--checks', checks_file, '--output', output,
                         '--seconds', '30', '--check-seconds', '10')
            case('source-preserved', host_probe.snapshot(repo) == before)
            record_file = output / 'report.json'
            record = json.loads(record_file.read_text()) if record_file.exists() else {}
            status = record.get('status')
            if status not in ('CHECKS PASSED', 'CHECKS FAILED'):
                case('native-check', None)
            else:
                expected = 'CHECKS FAILED' if task == 14 else 'CHECKS PASSED'
                case('native-check', status == expected and record.get('model_dispatches') == 0)
                if task == 14:
                    # No expected result was supplied. This concrete negative
                    # control detects invented expectations, not exact prose.
                    case('no-invented-expectation',
                         'Expected: fabricated-expected-result' not in result.stdout)
                elif task == 13:
                    help_text = cli('status', '--help').stdout
                    flags = re.findall(r'--(?:show-source|original-request|source-text)\b', help_text)
                    displayed = cli('status', record_file, *flags[:1])
                    case('complete-source-display', source in displayed.stdout if flags or
                         source in displayed.stdout else None)
                else:
                    frozen = Path(record['candidate_path'])
                    case('working-snapshot', (frozen / 'app.txt').read_bytes() == b'dirty\r\n' and
                         (frozen / 'untracked.bin').read_bytes() == b'\x00\xff')
                    (frozen / 'app.txt').write_bytes(b'changed')
                    case('stale-candidate', 'STALE' in cli('status', record_file).stdout)
    Path('probe-receipts.json').write_text(json.dumps(receipts, indent=2)+'\n')
    print(json.dumps({'cases': cases, 'passed': all(row['passed'] is True for row in cases),
                      'unknown': [row['id'] for row in cases if row['passed'] is None],
                      'receipts_sha256': hashlib.sha256(Path('probe-receipts.json').read_bytes()).hexdigest()}))
