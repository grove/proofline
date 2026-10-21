import json
import subprocess
from pathlib import Path

# The invoke shim binds p to the frozen candidate. Generated fixtures stay in scratch.
Path('good.py').write_text('from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer\ns = URLSafeSerializer("secret")\ns.loads(s.dumps("value"))\nt = URLSafeTimedSerializer("secret")\nt.loads(t.dumps("value"), max_age=60, return_timestamp=True)\n')
Path('bad.py').write_text('from itsdangerous import URLSafeSerializer\ns = URLSafeSerializer("secret")\ns.loads(s.dumps("value"), max_age=-1)\n')
Path('pyrightconfig.json').write_text(json.dumps({
    'include': ['good.py', 'bad.py'], 'extraPaths': [str(p / 'src')],
    'pythonVersion': '3.10', 'typeCheckingMode': 'standard',
}))
result = subprocess.run(['/opt/homebrew/bin/node', '/private/tmp/proofline-issue38-final/deps/pyright/dist/index.js', '--pythonpath', __import__('sys').executable, '--project', 'pyrightconfig.json', '--outputjson'], capture_output=True, text=True, timeout=30)
assert result.returncode in (0, 1), result.stderr
data = json.loads(result.stdout)
errors = [d for d in data['generalDiagnostics'] if d['severity'] == 'error']
bad_errors = [d for d in errors if d['file'].endswith('/bad.py') and d['range']['start']['line'] == 2]
good_errors = [d for d in errors if d['file'].endswith('/good.py')]
cases = [{'label': 'type-checker-flags-untimed-max-age', 'passed': bool(bad_errors)}, {'label': 'type-checker-allows-existing-timed-and-untimed-calls', 'passed': not good_errors}]
print(json.dumps({'cases': cases, 'diagnostics': data, 'subprocess_exit_code': result.returncode, 'stderr': result.stderr}))
assert all(c['passed'] for c in cases)
