"""Native Codex baselines without Proofline's acceptance or correction protocol."""
import json
from pathlib import Path
import shutil
import time

import proofline as p


def run(repo, source, guidance, output, review, codex, preferences, seconds, review_seconds, execution_map):
    started = time.monotonic()
    inputs = output / 'implementation/inputs'
    inputs.mkdir(parents=True)
    (inputs / 'source.md').write_text(source)
    (inputs / 'guidance.md').write_text(guidance)
    _, base = p.capture_base(repo, inputs / 'product')
    boundary = output / 'preflight'; boundary.mkdir()
    observed = p.host.probe_boundary(codex, boundary, inputs, 15, inputs / 'product/app.py')
    if observed['assessment']['status'] != 'OBSERVED':
        return {'accepted':False,'candidate':str(inputs/'product'),'stages':[],
                'elapsed_seconds':time.monotonic()-started,'model_dispatches':0,'error':'Native baseline boundary unavailable'}
    for name in ('canary.py','canary.json'):(inputs/name).unlink()
    stages=[]
    exhausted=False
    for role in ('implementer','reviewer') if review else ('implementer',):
        directory = output / ('implementation' if role=='implementer' else 'reviewer')
        current = inputs
        if role=='reviewer':
            current=directory/'inputs'
            shutil.copytree(inputs,current,symlinks=True)
        scratch,private=directory/'scratch',directory/'private'
        scratch.mkdir();private.mkdir()
        (current/'response.schema.json').write_text(json.dumps(p.live.object_schema({
            'completed' if role=='implementer' else 'passed':{'type':'boolean'},'summary':p.live.STRING})))
        p.host.write_diff(current/'product',base,current/'change.diff')
        protected={str(path.relative_to(current)):p.host.sha256(path.read_bytes())
                   for path in current.iterdir() if path.is_file()}
        before=p.host.snapshot(current) if role=='reviewer' else p.host.snapshot(current/'product/.git')
        remaining=seconds-(time.monotonic()-started)
        allowance=min(review_seconds,remaining) if role=='reviewer' else remaining-(min(review_seconds,seconds/2) if review else 0)
        if allowance<=0:
            exhausted=True
            break
        task=(f'Implement the original request in {current/"product"} using your normal coding approach and useful checks. '
              'Only product code is writable; do not commit. Return completed=true when the whole original task is finished, otherwise false, with a short summary.'
              if role=='implementer' else
              f'Independently review the code and diff in {current/"product"} against the original request. Inspect scope, correctness and regressions; run useful checks. '
              'Inputs are read-only; use scratch for artifacts. Return passed=true only if you find no material unmet requirement or regression, otherwise false, with a short summary. Do not correct the implementation.')
        prompt=task+f'\nOriginal request: {current/"source.md"}. Optional planning guidance: {current/"guidance.md"}. Diff: {current/"change.diff"}. '
        prompt+=execution_map+f'\nYou have {allowance:.1f} seconds including checks and your final response.\n'
        receipt=p.live.launch(p.live.command(codex,current,scratch,private,preferences,implementer=role=='implementer'),prompt,private,allowance)
        stage={'role':role,'status':'NOT VERIFIED','receipt':receipt,'usage':None}
        try:
            unchanged=before==(p.host.snapshot(current) if role=='reviewer' else p.host.snapshot(current/'product/.git'))
            unchanged=unchanged and all(p.host.sha256((current/name).read_bytes())==expected for name,expected in protected.items())
            if not unchanged:raise ValueError('Protected baseline inputs changed')
            native=p.live.read_events(receipt)
            stage.update(usage=native['usage'],thread_id=native['thread_id'],commands=native['commands'])
            flag='completed' if role=='implementer' else 'passed'
            report=native['report']
            if set(report)!={flag,'summary'} or type(report[flag]) is not bool or not isinstance(report['summary'],str):
                raise ValueError('Invalid native baseline completion response')
            if stages and native['thread_id']==stages[0].get('thread_id'):raise ValueError('Reviewer context is not independent')
            stage.update(status='OBSERVED',report=report)
        except (OSError,ValueError,KeyError,TypeError) as error:
            stage['error']=str(error)
        stages.append(stage)
        p.write_record(directory/'stage.json',stage)
        if stage['status']!='OBSERVED' or not stage['report'][flag]:break
        if role=='implementer':p.freeze(inputs/'product')
    return {'accepted':len(stages)==(2 if review else 1) and all(s['status']=='OBSERVED' and
            s['report'].get('completed',s['report'].get('passed')) is True for s in stages),
            'candidate':str(inputs/'product'),'stages':stages,'model_dispatches':len(stages),
            'status':'BUDGET EXHAUSTED' if exhausted else 'FINISHED',
            'elapsed_seconds':time.monotonic()-started,'transport':'native Codex; minimal completion/review response, no criterion/binding/command-citation protocol'}
