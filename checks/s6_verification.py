#!/usr/bin/env python3
"""Freeze and run the candidate-blind remedy's native gate, never efficacy scoring."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6
p=s6.p


def declare(output):
    output.mkdir(parents=True,exist_ok=False)
    root=p.host.ROOT/'.proofline/s6'
    tasks={item['id']:item for item in s6.corpus.TASKS}
    definitions=[
        ('stable-pagination',False,root/'verification-domain-remedy/pagination-defect/prover/inputs/product'),
        ('stable-pagination',True,'good'),
        ('stable-pagination',True,'alternative'),
        ('stable-pagination',False,root/'verification-positive-remedy/candidate-a/prover/inputs/product'),
        ('unicode-usernames',False,root/'verification-short-commands/unicode-library-domain/prover/inputs/product'),
        ('utc-timestamps',False,root/'pilot-v2/runs/9e0144b1b6ca4900a859dcc26b40dbfc/run/implementation/inputs/product'),
    ]
    cases=[]
    for index,(task,positive,origin) in enumerate(definitions):
        folder=output/'frozen'/str(index);folder.mkdir(parents=True)
        item=tasks[task]
        if isinstance(origin,Path):
            shutil.copytree(origin,folder/'product',symlinks=True)
            # The original product tree and history stay intact.
            origin_tree=p.host.git(origin,'rev-parse','HEAD^{tree}')
            if p.host.git(folder/'product','rev-parse','HEAD^{tree}')!=origin_tree:raise ValueError('Preserved candidate drift')
            origins={'path':str(origin),'snapshot':p.host.snapshot(origin)['sha256'],'tree':origin_tree}
        else:
            s6.seed(folder/'product',item,origin)
            origins={'reference':origin,'corpus_sha256':p.host.sha256(Path(s6.corpus.__file__).read_bytes())}
        (folder/'source.md').write_text(s6.corpus.source(item))
        (folder/'accepted-input.md').write_text(s6.corpus.brief(item))
        guidance=s6.MAP+'\nPublic normative context, no private probes or expectations:\n'+s6.corpus.STANDARD_REFERENCES.get(task,'')
        (folder/'execution-map.md').write_text(guidance)
        parents=p.host.git(folder/'product','rev-list','--parents','-n','1','HEAD').split()
        base=parents[1] if len(parents)>1 else parents[0]
        cases.append({'id':index,'task':task,'positive':positive,'origin':origins,'base_commit':base,
                      'frozen':str(folder),'snapshot':p.host.snapshot(folder)['sha256']})
    runtime=[Path(p.__file__),Path(p.live.__file__),Path(p.host.__file__),Path(p.challenges.__file__),
             Path(p.contract_input.__file__),Path(p.publication.__file__),Path(p.intentline_input.__file__),
             Path(s6.__file__),Path(s6.corpus.__file__),Path(__file__).resolve(),
             p.host.ROOT/'checks/s6_acceptance_audit.py',p.host.ROOT/'checks/s6_regression_audit.py',
             p.host.ROOT/'checks/s0_live.py']
    archive=output/'runtime-archive';archive.mkdir()
    files={str(path):p.host.sha256(path.read_bytes()) for path in runtime}
    for index,path in enumerate(runtime):shutil.copyfile(path,archive/str(index))
    codex=p.host.find_codex(None)
    manifest={'kind':'s6_candidate_blind_native_qualification','declared_at':datetime.now(timezone.utc).isoformat(),
              'models':{name:{'model':model,'model_reasoning_effort':'high'} for name,model in s6.MODELS.items()},
              'cases':cases,'tasks':tasks,'files':files,'codex_sha256':p.host.sha256(Path(codex).read_bytes()),
              'python':sys.version,'system':p.platform.platform(),'limits':{'stage_seconds':600,'jobs':4},
              'predictions':'Both verifiers FAIL on independently defective candidates; PASS/PROVEN on both corrected pagination structures. Every positive proof executes frozen probes. No retry of unavailable invocations.',
              'gate':'All declared model judgments and independent native adjudications must match. Qualification is incomplete if any invocation or case is unavailable. No comparison dispatch until this and production recovery qualify.',
              'pricing':None,'operator_attention_seconds':None,'exposure':'All tasks are disclosed exposed regressions, never new efficacy samples.'}
    p.write_record(output/'manifest.json',manifest)
    p.write_record(output/'report.json',{'status':'DECLARED','manifest_sha256':p.host.sha256((output/'manifest.json').read_bytes()),'plans':[],'cases':[]})
    return manifest


def validate(output):
    raw=(output/'manifest.json').read_bytes(); manifest=json.loads(raw)
    if json.loads((output/'report.json').read_text())['manifest_sha256']!=p.host.sha256(raw):raise ValueError('Declaration changed')
    for name,digest in manifest['files'].items():
        if p.host.sha256(Path(name).read_bytes())!=digest:raise ValueError('Frozen runtime changed: '+name)
    for case in manifest['cases']:
        if p.host.snapshot(Path(case['frozen']))['sha256']!=case['snapshot']:raise ValueError('Frozen fixture changed')
    if p.host.sha256(Path(p.host.find_codex(None)).read_bytes())!=manifest['codex_sha256']:raise ValueError('Codex changed')
    return manifest


def run(output):
    manifest=validate(output);report=json.loads((output/'report.json').read_text())
    if report['status']!='DECLARED':raise ValueError('Native qualification is single-use; preserve its results')
    started=time.monotonic();codex=p.host.find_codex(None);seconds=manifest['limits']['stage_seconds']
    report['status']='RUNNING';p.write_record(output/'report.json',report)
    # Adjudicate controls before model verdicts. Oracle material never enters model inputs.
    for case in manifest['cases']:
        evaluation=s6.evaluate(Path(case['frozen'])/'product',manifest['tasks'][case['task']],
                               codex=codex,directory=output/'operator'/('control-'+str(case['id'])))
        report['cases'].append({'id':case['id'],'evaluation':evaluation,'judgments':[]})
        p.write_record(output/'report.json',report)
        if not evaluation['observed'] or evaluation['correct']!=case['positive']:
            report['status']='ADJUDICATION FAILED';p.write_record(output/'report.json',report);return report
    def author(key):
        model,task=key
        case=next(c for c in manifest['cases'] if c['task']==task)
        original=Path(case['frozen']);directory=output/'authors'/model/task;directory.mkdir(parents=True)
        guidance=(original/'execution-map.md').read_text()
        inputs=p.challenges.prepare(directory,original,guidance)
        base=p.host.git(inputs/'product','rev-parse','HEAD');identity=p.identities(inputs,base)
        stage=p.live.run_stage(codex,directory,inputs,identity,'challenger',manifest['models'][model],seconds,
            make_prompt=lambda role,ins,ident,canary=None:p.challenges.prompt(role,ins,ident,canary,ids=['R1','R2','R3'],execution_map=guidance),
            criterion_ids=['R1','R2','R3'],target=inputs/'product/interface.txt',schema=p.challenges.SCHEMA,
            validator=p.challenges.validate_report,denied_reads={'implementation':str(original/'product/product.py')})
        matched=stage['status']=='OBSERVED' and stage['report']['verdict']=='PLANNED'
        if matched:
            try:
                p.challenges.attach(inputs,stage['report'])
                # Attach only to a disposable validation copy, preserving stage snapshot.
            except ValueError:matched=False
            finally:
                if (inputs/'challenges.json').exists():(inputs/'challenges.json').unlink()
                if (inputs/'challenges').exists():shutil.rmtree(inputs/'challenges')
        return {'model':model,'task':task,'stage':stage,'matched':matched}
    keys=[(model,task) for model in manifest['models'] for task in ('stable-pagination','unicode-usernames','utc-timestamps')]
    with ThreadPoolExecutor(max_workers=manifest['limits']['jobs']) as pool:
        for entry in pool.map(author,keys):
            report['plans'].append(entry);p.write_record(output/'report.json',report)
            print('plan',entry['model'],entry['task'],entry['stage']['status'],'matched',entry['matched'],flush=True)
    plans={(e['model'],e['task']):e for e in report['plans']}
    def judge(key):
        model,case,role=key;plan=plans[model,case['task']]
        if not plan['matched']:return {'model':model,'case':case['id'],'role':role,'status':'NOT EXECUTED','matched':False}
        original=Path(case['frozen']);directory=output/'judgments'/model/str(case['id'])/role;directory.mkdir(parents=True)
        inputs=directory/'inputs';shutil.copytree(original,inputs,symlinks=True)
        p.challenges.attach(inputs,plan['stage']['report'])
        identity=p.identities(inputs,case['base_commit']);guidance=(inputs/'execution-map.md').read_text()
        stage=p.live.run_stage(codex,directory,inputs,identity,role,manifest['models'][model],seconds,
            make_prompt=lambda r,ins,ident,canary=None:p.prompt(r,ins,ident,canary,ids=['R1','R2','R3'],execution_map=guidance)+p.challenges.guidance(ins),
            criterion_ids=['R1','R2','R3'],target=inputs/'product/product.py')
        if role=='prover' and stage['status']=='OBSERVED':
            try:p.challenges.validate_execution(stage['report'],stage['commands'],inputs)
            except (ValueError,KeyError,OSError) as exc:
                stage['status']='NOT VERIFIED';stage['error']=str(exc);p.write_record(directory/'stage.json',stage)
        expected=('PASS' if role=='reviewer' else 'PROVEN') if case['positive'] else 'FAIL'
        return {'model':model,'case':case['id'],'role':role,'stage':stage,
                'matched':stage['status']=='OBSERVED' and stage['report']['verdict']==expected}
    keys=[(model,case,role) for model in manifest['models'] for case in manifest['cases'] for role in ('reviewer','prover')]
    with ThreadPoolExecutor(max_workers=manifest['limits']['jobs']) as pool:
        for entry in pool.map(judge,keys):
            report['cases'][entry['case']]['judgments'].append(entry);p.write_record(output/'report.json',report)
            stage=entry.get('stage',{})
            print('judgment',entry['model'],entry['case'],entry['role'],stage.get('status',entry.get('status')),stage.get('report',{}).get('verdict'),'matched',entry['matched'],flush=True)
    report.update(status='NATIVE JUDGMENTS PASSED' if all(e['matched'] for c in report['cases'] for e in c['judgments']) else 'TRUST QUALIFICATION FAILED',
                  elapsed_seconds=time.monotonic()-started,production_recovery='NOT EXECUTED')
    p.write_record(output/'report.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('declare','run'));parser.add_argument('output',type=Path)
    args=parser.parse_args();result=(declare if args.command=='declare' else run)(args.output.resolve())
    if args.command=='run':raise SystemExit(0 if result['status']=='NATIVE JUDGMENTS PASSED' else 2)
