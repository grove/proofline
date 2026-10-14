"""Offline cache-expiry v2 oracle controls; never invoke a coding model.

This is a *future-only* demonstrator, not a replacement for the frozen v1
oracle or an authorization to repeat the exposed #34 experiment.
"""
import json
from pathlib import Path

from checks.native_checks import write_record
from evaluation.recovery import corpus, grader
from evaluation.source_preflight import qualify

SOURCE = corpus.REQUESTS["cache-expiry"].encode("utf-8")
EXCEPTIONS = {"TypeError": TypeError, "ValueError": ValueError}
CASE_SPECS = {
    "compatibility": {"kind": "compatibility", "cases": ["legacy compatibility"]},
    "actions": {"kind": "output", "cases": ["action example and seams"]},
    "expiry": {"kind": "output", "cases": ["expiry and no-ttl behavior"]},
    "copies": {"kind": "negative", "cases": ["no aliased cache data"]},
    "invalidation": {"kind": "output", "cases": ["invalidate expired and clear"]},
    "invalid_ttl": {"kind": "exception", "cases": [
        "reject TTL True", "reject TTL -1", "reject TTL nan",
        "reject TTL inf", "reject TTL string",
    ]},
    "loader_failure": {"kind": "negative", "cases": ["loader failure does not populate cache"]},
}

PRELUDE = corpus.code(r"""
    import copy, json, math, subprocess, sys, time
    from pathlib import Path
    from cache import Cache
    from app import process
    from service import handle

    cases = []
    def check(label, fn):
        try:
            fn()
            cases.append({'label':label,'passed':True})
        except Exception as error:
            cases.append({'label':label,'passed':False,
                          'error':type(error).__name__+': '+str(error)})
    def eq(actual, expected):
        assert actual == expected, (actual, expected)
    def rejects(call):
        try:
            call()
        except ALLOWED:
            return
        except Exception as error:
            raise AssertionError('unexpected TTL exception: '+type(error).__name__) from error
        raise AssertionError('invalid TTL was accepted')

    def compatibility():
        cache = Cache(lambda:0)
        assert cache.get('old',lambda:1)==1
        assert cache.get('old',lambda:2)==1
        payload = {'actions':[{'op':'get','key':'x','value':1}]}
        eq(process(payload),{'values':[1],'loads':1})
        eq(handle(payload),{'values':[1],'loads':1})
        exe = str(Path(sys.modules['app'].__file__).resolve().parent/'cli.py')
        command = subprocess.run([sys.executable,'-B',exe,'--version'],
                                 capture_output=True,text=True,timeout=5)
        assert (command.returncode,command.stdout,command.stderr)==(0,'repo-v1\n','')
        command = subprocess.run([sys.executable,'-B',exe,'--unknown'],
                                 capture_output=True,text=True,timeout=5)
        assert command.returncode==2
    check('legacy compatibility', compatibility)

    def actions():
        payload = {'actions':[{'op':'get','key':'x','value':1,'at':0,'ttl':2},
                              {'op':'get','key':'x','value':2,'at':2,'ttl':2},
                              {'op':'clear'}]}
        expected = {'values':[1,2,1],'loads':2}
        original = copy.deepcopy(payload)
        eq(process(payload),expected)
        eq(handle(payload),expected)
        assert payload==original
    check('action example and seams',actions)

    def expiry():
        clock=[10]; calls=[]; cache=Cache(lambda:clock[0])
        def loader():
            calls.append(1)
            return len(calls)
        assert cache.get('finite',loader,2)==1
        clock[0]=11; assert cache.get('finite',loader)==1 and len(calls)==1
        clock[0]=12; assert cache.get('finite',loader,2)==2
        clock[0]=20; assert cache.get('zero',loader,0)==3
        assert cache.get('zero',loader,0)==4
        cache.get('infinite',loader)
        clock[0]=1e6
        assert cache.get('infinite',loader)==5 and len(calls)==5
    check('expiry and no-ttl behavior',expiry)

    def copies():
        cache=Cache(lambda:0)
        input_value={'nested':[1]}
        first=cache.get('x',lambda:input_value)
        first['nested'].append(2)
        input_value['nested'].append(3)
        assert cache.get('x',lambda:None)=={'nested':[1]}
        second=cache.get('x',lambda:None)
        second['nested'].append(4)
        assert cache.get('x',lambda:None)=={'nested':[1]}
    check('no aliased cache data',copies)

    def invalidation():
        clock=[0]; cache=Cache(lambda:clock[0])
        cache.get('expired',lambda:1,1)
        clock[0]=2
        assert cache.invalidate('expired') is True
        assert cache.invalidate('expired') is False
        cache.get('a',lambda:2); cache.get('b',lambda:3)
        assert cache.clear()==2 and cache.clear()==0
    check('invalidate expired and clear',invalidation)

    for label, value in [
        ('reject TTL True',True),('reject TTL -1',-1),
        ('reject TTL nan',float('nan')),('reject TTL inf',float('inf')),
        ('reject TTL string','2'),
    ]:
        def invalid(value=value):
            calls=[]
            cache=Cache(lambda:0)
            cache.get('hit',lambda:1)
            rejects(lambda: cache.get('hit',lambda: calls.append(1),value))
            assert calls==[], 'invalid TTL invoked loader'
            rejects(lambda: cache.get('miss',lambda: calls.append(2),value))
            assert calls==[], 'invalid TTL invoked loader on miss'
        check(label,invalid)

    def loader_failure():
        cache=Cache(lambda:0)
        loads=[]
        def failing():
            loads.append('fail')
            raise RuntimeError('loader')
        try:
            cache.get('key',failing)
        except Exception:
            pass  # Request promises no cache population, not an exception class.
        result=cache.get('key',lambda:loads.append('success') or 9)
        assert result==9 and loads==['fail','success']
    check('loader failure does not populate cache',loader_failure)
""")

SUITE = corpus.code(r"""
    import app
    product_dir = str(Path(app.__file__).resolve().parent)
    argv = [sys.executable,'-B','-m','unittest','discover','-s','tests']
    receipt = {'argv':argv,'cwd':product_dir,'exit_code':None,
               'stdout':'','stderr':'','timed_out':False,
               'stdout_truncated':False,'stderr_truncated':False}
    start = time.monotonic()
    try:
        completed = subprocess.run(argv,cwd=product_dir,capture_output=True,
                                   text=True,timeout=10)
        receipt['exit_code']=completed.returncode
        for name in ('stdout','stderr'):
            value=getattr(completed,name)
            receipt[name]=value[:8192]
            receipt[name+'_truncated']=len(value)>8192
    except subprocess.TimeoutExpired as error:
        receipt['timed_out']=True
        for name in ('stdout','stderr'):
            value=getattr(error,name,None) or b''
            if isinstance(value,bytes):
                value=value.decode('utf-8',errors='replace')
            receipt[name]=value[:8192]
            receipt[name+'_truncated']=len(value)>8192
    except OSError as error:
        receipt['error']=type(error).__name__+': '+str(error)
    receipt['elapsed_seconds']=round(time.monotonic()-start,6)
    unavailable = (receipt['exit_code'] is None or receipt['timed_out'] or
                   receipt.get('error') or receipt['stdout_truncated'] or
                   receipt['stderr_truncated'])
    status = ('UNAVAILABLE' if unavailable else
              'PASSED' if receipt['exit_code']==0 else 'FAILED')
    print(json.dumps({'cases':cases,'repository_tests':{
        'status':status,'passed':True if status=='PASSED' else
        False if status=='FAILED' else None,'receipt':receipt}},sort_keys=True))
""")


def script(allowed_exceptions=("ValueError", "TypeError")):
    """Build a bounded policy; never interpolate arbitrary names or code."""
    if (not isinstance(allowed_exceptions, (list, tuple)) or
            not allowed_exceptions or len(set(allowed_exceptions)) != len(allowed_exceptions) or
            any(name not in EXCEPTIONS for name in allowed_exceptions)):
        raise ValueError("Unsupported exception policy")
    return ("ALLOWED = (" + ",".join(allowed_exceptions) + ",)\n"
            + PRELUDE + SUITE)


def _qualified_script(declaration, source):
    """Resolve immutable oracle code and preflight without a product or model."""
    requested = None
    if isinstance(declaration, dict) and isinstance(declaration.get("expectations"), list):
        for item in declaration["expectations"]:
            if isinstance(item, dict) and item.get("id") == "invalid_ttl":
                requested = item.get("allowed_exceptions")
                break
    try:
        generated = script(requested)
    except (ValueError, TypeError):
        generated = script()
    qualification = qualify(declaration, source=source, oracle_text=generated,
                            inventory=CASE_SPECS)
    return generated, qualification


def preflight(declaration, *, source=SOURCE):
    """Call this at study preparation, *before* any possible model dispatch."""
    return _qualified_script(declaration, source)[1]


def grade(product, declaration, directory, *, source=SOURCE, trusted=True):
    """Fail closed on the same preflight before any offline oracle execution."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    generated, qualification = _qualified_script(declaration, source)
    write_record(directory/"qualification.json", qualification)
    if qualification["status"] != "QUALIFIED":
        result = {"status":"NOT QUALIFIED", "correct":None, "cases":[],
                  "repository_tests_passed":None,"model_dispatches":0,
                  "qualification":qualification}
        write_record(directory/"result.json",result)
        return result

    invoked = grader.invoke(Path(product), generated, directory/"oracle",
                            trusted=trusted)
    result = {"status":"ORACLE UNAVAILABLE", "correct":None, "cases":[],
              "repository_tests_passed":None,"repository_tests_status":"UNAVAILABLE",
              "model_dispatches":0,"qualification":qualification,
              "invocation":invoked}
    if invoked["available"] and invoked["receipt"].get("exit_code")==0:
        try:
            observed=json.loads(invoked["receipt"]["stdout"])
            cases=observed["cases"]
            expected=[label for spec in CASE_SPECS.values() for label in spec["cases"]]
            if ([case["label"] for case in cases]!=expected or
                    any(type(case.get("passed")) is not bool for case in cases)):
                raise ValueError("Oracle case inventory mismatch")
            suite=observed["repository_tests"]
            receipt=suite["receipt"]
            if (suite["status"] not in ("PASSED","FAILED","UNAVAILABLE") or
                    suite["passed"] is not (True if suite["status"]=="PASSED" else
                                            False if suite["status"]=="FAILED" else None) or
                    receipt["argv"] != [str(Path(__import__("sys").executable).resolve()),
                                        "-B","-m","unittest","discover","-s","tests"] or
                    receipt["cwd"] != str((directory/"oracle/inputs/product").resolve()) or
                    (suite["status"]=="PASSED") != (receipt["exit_code"]==0) or
                    (suite["status"]=="FAILED") !=
                        (receipt["exit_code"] is not None and receipt["exit_code"]!=0) or
                    (suite["status"]!="UNAVAILABLE" and any(receipt.get(k) for k in
                        ("timed_out","error","stdout_truncated","stderr_truncated")))):
                raise ValueError("Repository-test receipt unavailable or inconsistent")
            result.update(status="PASSED" if all(c["passed"] for c in cases) else "FAILED",
                          correct=all(c["passed"] for c in cases), cases=cases,
                          repository_tests_passed=suite["passed"],
                          repository_tests_status=suite["status"],
                          repository_tests_receipt=receipt)
        except (TypeError,KeyError,ValueError,AttributeError):
            pass
    write_record(directory/"result.json",result)
    return result
