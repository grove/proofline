"""Bind a new corpus without editing issue #16's hash-frozen grading machinery."""
import importlib.util
import json
from pathlib import Path
import tempfile
import time

from evaluation.matched import grader as existing
from evaluation.sol_luna import corpus


def bound_module(module, **bindings):
    # Historical modules have fixed globals and must remain byte-for-byte frozen.
    spec = importlib.util.spec_from_file_location(module.__name__+"_issue32", module.__file__)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    native.__dict__.update(bindings)
    return native


native = bound_module(existing, corpus=corpus)


def grade(product, task, directory, **kwargs):
    started=time.monotonic()
    if not (Path(product)/'cli.py').exists():
        return {"available":True,"correct":False,"failures":[{"obligation":"unchanged cli.py","seam":"file bytes"}],
                "receipts":[],"unavailable":[],"repository_tests_passed":None,"elapsed_seconds":time.monotonic()-started}
    result=native.grade(product, task, directory, **kwargs)
    if result['correct'] is True:
        # Python equality conflates true/1 and 1.0/1; JSON output types matter here.
        checks=[]
        for index,(_,_,expected) in enumerate(corpus.CASES[task]):
            if expected!='ValueError':
                checks.extend((3*index+offset,seam,expected) for offset,seam in enumerate(('library','service','cli')))
        first=next((p,e) for _,p,e in corpus.CASES[task] if e!='ValueError')
        batch_start=3*(len(corpus.CASES[task])+1)
        checks.extend([(batch_start,'batch',[]),(batch_start+1,'batch',[first[1],first[1]])])
        for index,seam,expected in checks:
            observed=json.loads(result['receipts'][index]['stdout'])
            actual=observed if seam=='cli' else observed['value']
            if json.dumps(actual,sort_keys=True)!=json.dumps(expected,sort_keys=True):
                result['failures'].append({'obligation':'exact JSON output types','seam':seam,'receipt_index':index})
        result['correct']=not result['failures']
    result['elapsed_seconds']=time.monotonic()-started
    return result


def controls(*, trusted=True, directory=None):
    rows=[]
    with tempfile.TemporaryDirectory(prefix='proofline-issue32-controls-') as temporary:
        root=Path(directory or temporary)
        for task in corpus.REQUESTS:
            variants=('reference','alternative','defective','missing-batch') + (('typed-defective',) if task=='tiered-invoice' else ())
            for variant in variants:
                folder=root/task/variant
                product=corpus.seed(task,folder/'inputs',variant)
                result=grade(product,task,folder/'evaluation',trusted=trusted)
                matched=result['available'] and result['correct']==(variant in ('reference','alternative')) and result['repository_tests_passed']
                rows.append({'task':task,'variant':variant,'matched':matched,'grade':result})
    return {"all_matched":all(r['matched'] for r in rows),"controls":rows,"model_dispatches":0,
            "scope":"bundled trusted controls only" if trusted else "native protected controls"}
