"""Source preflight and protected regression observations, never model feedback.

Regression failures need the frozen source audit before becoming product defects:
the original requests permit alternatives to the reference implementation's CLI
spellings, documentation wording and packaging. Tests cannot overrule that.
"""
import json
from pathlib import Path
import time

from checks import host_probe as host
from checks.native_checks import write_record
from evaluation.recovery.grader import invoke
from evaluation.source_preflight import qualify

HERE = Path(__file__).resolve().parent

LAUNCH = '''import hashlib, importlib.util, io, json, os, sys, unittest
from pathlib import Path
product = Path(sys.argv[1])
sys.path.insert(0, str(product))
# Use the already-qualified native Git tools, rather than Apple's discovery shim.
git_dir = '/Library/Developer/CommandLineTools/usr/bin'
os.defpath = git_dir + ':/usr/bin:/bin'
os.environ.update(PATH=os.defpath, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                  GIT_EXEC_PATH='/Library/Developer/CommandLineTools/usr/libexec/git-core')
spec = importlib.util.spec_from_file_location('private_regressions', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = product
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
log = stream.getvalue().encode()
Path('regressions.log').write_bytes(log)
def bounded(items):
    return [(str(t)[:150], text[-200:]) for t,text in items[:20]]
print(json.dumps({'ran': result.testsRun, 'failures': bounded(result.failures),
                  'errors': bounded(result.errors), 'failure_count': len(result.failures),
                  'error_count': len(result.errors), 'log_sha256': hashlib.sha256(log).hexdigest(),
                  'skipped': [(str(t), why) for t,why in result.skipped],
                  'passed': result.wasSuccessful()}))
'''


def script(task):
    tests = (HERE / 'oracles' / f'issue{task}.py').read_text()
    # Keep the private suite outside the candidate; only this read-only grader sees it.
    return ('import sys\nfrom pathlib import Path\n'
            "suite_file=Path('private_regressions.py')\n"
            f'suite_file.write_text({tests!r})\n'
            "sys.argv=[sys.argv[0],sys.path[0],str(suite_file.resolve())]\n" + LAUNCH)


def preflight(task):
    declaration = json.loads((HERE / 'expectations.json').read_text())[str(task)]
    inventory = json.loads((HERE / 'inventory.json').read_text())[str(task)]
    return qualify(declaration, source=(HERE / 'requests' / f'issue-{task}.md').read_bytes(),
                   oracle_text=script(task), inventory=inventory)


def observe(product, task, directory, *, trusted=False, seconds=120):
    began = time.monotonic()
    qualification = preflight(task)
    if qualification['status'] != 'QUALIFIED':
        raise ValueError('Source-to-oracle preflight failed: '+str(qualification['problems']))
    invocation = invoke(product, script(task), directory, trusted=trusted, seconds=seconds)
    observed = None
    if invocation['available'] and invocation['receipt'].get('exit_code') == 0:
        try:
            observed = json.loads(invocation['receipt']['stdout'])
            if type(observed['passed']) is not bool or not observed['ran'] or observed['skipped']:
                raise ValueError('Incomplete regression observation')
            if host.sha256((directory / 'scratch/regressions.log').read_bytes()) != observed['log_sha256']:
                raise ValueError('Diagnostic log changed')
        except (ValueError, KeyError, TypeError):
            invocation['available'] = False
    else:
        invocation['available'] = False
    result = {'qualification': qualification, 'invocation': invocation, 'observed': observed,
              'elapsed_seconds': time.monotonic()-began, 'model_dispatches': 0,
              'status': 'SOURCE AUDIT REQUIRED' if invocation['available'] else 'ORACLE UNAVAILABLE',
              'correct': None}
    write_record(directory / 'observation.json', result)
    return result


def visible(product, modules, directory, *, seconds=30, trusted=False):
    """Keep actual original-suite argv/cwd/status separate from source correctness."""
    program = ('import json, subprocess, sys\nfrom pathlib import Path\n'
               'product=Path(sys.path[0])\n'
               f'argv=[{str(Path(__import__("sys").executable).resolve())!r}, "-B", "-m", "unittest", *{modules!r}]\n'
               'receipt={"argv":argv,"cwd":str(product),"exit_code":None,"timed_out":False}\n'
               'try:\n'
               ' result=subprocess.run(argv,cwd=product,capture_output=True,text=True,timeout=20)\n'
               ' receipt.update(exit_code=result.returncode,stdout=result.stdout[:8192],stderr=result.stderr[:8192],\n'
               '                stdout_truncated=len(result.stdout)>8192,stderr_truncated=len(result.stderr)>8192)\n'
               'except subprocess.TimeoutExpired:\n receipt["timed_out"]=True\n'
               'print(json.dumps(receipt))\n')
    result = invoke(product, program, directory, trusted=trusted, seconds=seconds)
    suite = None
    if result['available'] and result['receipt'].get('exit_code') == 0:
        try:
            suite = json.loads(result['receipt']['stdout'])
        except (ValueError, TypeError):
            pass
    available = suite is not None and suite.get('exit_code') is not None and not any(
        suite.get(key) for key in ('timed_out', 'stdout_truncated', 'stderr_truncated'))
    result.update(repository_tests_passed=suite['exit_code'] == 0 if available else None,
                  repository_tests_status='PASSED' if available and suite['exit_code'] == 0 else 'FAILED' if available else 'UNAVAILABLE',
                  repository_tests_receipt=suite)
    write_record(directory / 'suite.json', result)
    return result
