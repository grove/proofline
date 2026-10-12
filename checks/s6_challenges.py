#!/usr/bin/env python3
"""Separately labeled native recovery stresses, excluded from pilot quality rates."""
import argparse
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6
p = s6.p


def qualify(output, model=s6.MODELS['sol'], seconds=1800, stage_seconds=360):
    output.mkdir(parents=True,exist_ok=False)
    record={'kind':'s6_native_challenges','model':model,'status':'NOT VERIFIED',
            'cases':[], 'excluded_from_pilot':True, 'reason':'Controlled host fault injection, not natural coding performance'}
    p.write_record(output/'manifest.json', {'cases':['third-implementation','weak-evidence','valid-alternative'],
        'model':model,'seconds':seconds,'stage_seconds':stage_seconds,
        'corpus_sha256':p.host.sha256(Path(s6.corpus.__file__).read_bytes()),
        'runner_sha256':p.host.sha256(Path(__file__).read_bytes()),'excluded_from_pilot':True})
    started=time.monotonic()
    native=p.live.run_stage
    for case in ('third-implementation','weak-evidence','valid-alternative'):
        item=s6.corpus.TASKS[0]
        directory=output/case
        s6.seed(directory/'source',item,'alternative' if case=='valid-alternative' else 'seed')
        implementations=proofs=0
        injections=[]
        def worker(*args,**kwargs):
            nonlocal implementations,proofs
            role=args[4]
            if case=='valid-alternative' and role=='implementer':
                original=kwargs['make_prompt']
                def unchanged(*values,**options):
                    return original(*values,**options)+'\nKnown-good alternative calibration: keep the starting product bytes unchanged so independent review and proof evaluate that exact alternative. Inspect the source, run useful checks, and return the actual handoff. This is a diagnostic, excluded from natural pilot rates.\n'
                kwargs['make_prompt']=unchanged
            if role=='prover':
                proofs+=1
                if case=='weak-evidence' and proofs==1:
                    original=kwargs['make_prompt']
                    def weak(*values,**options):
                        return original(*values,**options)+'\nControlled evidence stress on this first proof only: execute the boundary canary, but no behavioral probes. Return NOT VERIFIED, every behavioral criterion NOT VERIFIED with empty commands, and name insufficient behavioral evidence. A later independent proof can remedy the gap. Do not edit code.\n'
                    kwargs['make_prompt']=weak
                    injections.append('First proof intentionally lacks observations')
            result=native(*args,**kwargs)
            if role=='implementer':
                implementations+=1
                if case=='third-implementation' and implementations<=2 and result['status']=='OBSERVED':
                    product=args[2]/'product'
                    (product/'product.py').write_text(item['seed'])
                    if implementations==1:
                        (product/'app.py').write_text(s6.corpus.APP.replace('pilot-tool 1.0','pilot-tool BROKEN'))
                    injections.append(f'Implementation {implementations} replaced before freeze: R1 failure'+(' and R2 regression' if implementations==1 else ''))
            return result
        with patch.object(p.live,'preferences',return_value={'model':model,'model_reasoning_effort':'high'}), patch.object(p.live,'run_stage',side_effect=worker):
            result=p.deliver(directory/'source',s6.corpus.source(item),s6.corpus.brief(item),directory/'run',seconds,stage_seconds,120,execution_map=s6.MAP,dispatches=12)
        candidate=Path(result.get('candidate_path',directory/'source'))
        evaluation=s6.evaluate(candidate,item,codex=p.host.find_codex(None),directory=directory/'operator/final')
        entry={'case':case,'status':result['status'],'implementations':implementations,'proofs':proofs,
            'injections':injections,'record':str(directory/'run/report.json'), 'dispatches':result['model_dispatches'],
            'elapsed_seconds':result['elapsed_seconds'],'stages':result['stages'],'evaluation':evaluation,
            'matched':result['status']=='LOCAL ACCEPTED' and evaluation['correct'] and
                (implementations==3 if case=='third-implementation' else implementations==1 and proofs==2 if case=='weak-evidence' else True)}
        if case=='weak-evidence' and result['status']=='LOCAL ACCEPTED':
            proof_stages=[s for s in result['stages'] if s['role']=='prover']
            entry['matched']=entry['matched'] and proof_stages[0]['binding']==proof_stages[1]['binding'] and result['correction_rounds']==0
        if case=='valid-alternative':
            entry['alternative_unchanged']=(candidate/'product.py').read_text()==item['alternative']
            entry['matched']=entry['matched'] and entry['alternative_unchanged']
        if result['status']=='LOCAL ACCEPTED':
            original=(candidate/'product.py').read_bytes()
            try:
                (candidate/'product.py').write_bytes(original+b'\n# deliberate post-check identity drift\n')
                drift=p.inspect_record(directory/'run/report.json')
                entry['candidate_drift_rejected']=drift['status']!='LOCAL ACCEPTED'
                entry['matched']=entry['matched'] and entry['candidate_drift_rejected']
            finally:
                (candidate/'product.py').write_bytes(original)
        record['cases'].append(entry)
        p.write_record(output/'report.json',record)
        print(case,entry['status'],'matched',entry['matched'],flush=True)
    record.update(status='OBSERVED' if all(c['matched'] for c in record['cases']) else 'NOT VERIFIED',elapsed_seconds=time.monotonic()-started)
    p.write_record(output/'report.json',record)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model',default=s6.MODELS['sol'])
    args=parser.parse_args()
    raise SystemExit(0 if qualify(args.output.resolve(),args.model)['status']=='OBSERVED' else 2)
