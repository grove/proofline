#!/usr/bin/env python3
"""Single-use native source-contract qualification; calibration precedes model judgments."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_source_contracts as specs, s6_verification as previous
from checks import s6_utc_references as utc, s6_iso_audit as iso_audit
from checks.s6_challenges import qualify as recovery
p=specs.p


def clarify(target):
    source=target/'source.md';brief=target/'accepted-input.md'
    for path in (source,brief):
        original=target/('original-'+path.name)
        if not original.exists():shutil.copyfile(path,original)
    if utc.CLARIFICATION not in source.read_text():
        with source.open('a') as stream:stream.write('\n'+utc.CLARIFICATION+'\n')
    lines=brief.read_text().splitlines()
    rows=[index for index,line in enumerate(lines) if line.startswith('| R1 |')]
    if len(rows)!=1:raise ValueError('Clarification needs the original R1 brief row')
    index=rows[0]
    if utc.CLARIFICATION not in lines[index]:
        lines[index]=lines[index].rstrip().removesuffix('|')+utc.CLARIFICATION+' |'
        brief.write_text('\n'.join(lines)+'\n')


def declare(output):
    output.mkdir(parents=True,exist_ok=False)
    old=p.host.ROOT/'.proofline/s6/source-challenges-v3'
    original=json.loads((old/'manifest.json').read_text())
    tasks=copy.deepcopy(original['tasks'])
    pagination=tasks['stable-pagination']
    username=tasks['unicode-usernames']
    for task in (pagination,username):
        repaired=next(item for item in specs.s6.corpus.TASKS if item['id']==task['id'])
        task.update(good=repaired['good'],alternative=repaired['alternative'])
    timestamp=tasks['utc-timestamps']
    timestamp.update(good=utc.program('good'),alternative=utc.program('alternative'))
    timestamp['probes'] += [{'input':value,'expected':expected} for value,expected,_ in iso_audit.PROBES]
    for width in (4,5,6,7,10,30):
        year='2024'.zfill(width)
        timestamp['probes'] += [{'input':value,'expected':'2024-04-01T00:00:00Z'} for value in (
            '+'+year+'-04-01T00:00:00Z','+'+year+'0401T000000Z','+'+year+'W141T000000Z')]
    timestamp['probes'] += [{'input':value,'expected':{'error':True,'value_error':True}} for value in (
        '+0020240101T000000Z','+00020240101T000000Z','+0000010101T000000Z')]
    timestamp['probes'] += [{'input':value,'expected':{'error':True}} for value in (
        '2024-01-01T00:00:00-00:00','20240101T000000-00','-0000-04-01T00:00:00Z')]
    timestamp['probes'] += [{'input':value,'expected':'2024-03-01T00:30:00Z'} for value in (
        '2024-02-29T23:30:00\u221201:00','2024\u201002\u201029T23:30:00\u221201:00',
        '20240229T233000\u22120100')]
    timestamp['probes'] += [{'input':value,'expected':'2016-12-31T23:59:60Z'} for value in (
        '+0020161231T235960Z','+0020170101T005960+0100','+020161231T235960.5Z',
        '2016-12-31T23:59.99Z','20161231T2359,99Z','2017-01-01T00:59.99+01:00',
        '20161231T23.9999Z')]
    timestamp['probes'] += [{'input':'2017-01-01T00.9+00:15','expected':'2017-01-01T00:38:59Z'},
                            {'input':'+0020161231T235959Z','expected':{'error':True,'value_error':True}}]
    cases=[]
    for item in original['cases']:
        # Retain the defective former positive as a negative, with its prediction history.
        item={**item,'prior_declared_positive':item['positive'],
              'positive':False if item['id'] in (1,2,6,7,8) else item['positive']}
        source=Path(item['frozen'])
        if p.host.snapshot(source)['sha256']!=item['snapshot']:raise ValueError('Preserved fixture changed')
        target=output/'frozen'/str(item['id']);target.parent.mkdir(exist_ok=True)
        shutil.copytree(source,target,symlinks=True)
        cases.append({**item,'frozen':str(target),'origin_snapshot':item['snapshot']})
    retained=output.parent/'source-contracts-v3'
    preceding=json.loads((retained/'manifest.json').read_text())
    for ident in (9,10):
        item=preceding['cases'][ident];source=Path(item['frozen'])
        if p.host.snapshot(source)['sha256']!=item['snapshot']:raise ValueError('Retained provisional UTC changed')
        index=len(cases);target=output/'frozen'/str(index);shutil.copytree(source,target,symlinks=True)
        cases.append({**item,'id':index,'positive':False,'prior_declared_positive':item['positive'],
            'frozen':str(target),'origin_snapshot':item['snapshot'],
            'origin':{'qualification_manifest_sha256':p.host.sha256((retained/'manifest.json').read_bytes()),'case':ident,
                      'adjudication':['complete-timestamp-readback-v1','leap-unit-readback-v1']}})
    text_run=output.parent/'representation-qualification-v1'
    text_manifest=json.loads((text_run/'manifest.json').read_text())
    for ident in (11,12,13,14):
        item=text_manifest['cases'][ident];source=Path(item['frozen'])
        if p.host.snapshot(source)['sha256']!=item['snapshot']:raise ValueError('Retained scalar-domain fixture changed')
        index=len(cases);target=output/'frozen'/str(index);shutil.copytree(source,target,symlinks=True)
        cases.append({**item,'id':index,'positive':False,'prior_declared_positive':item['positive'],
            'frozen':str(target),'origin_snapshot':item['snapshot'],
            'origin':{'qualification_manifest_sha256':p.host.sha256((text_run/'manifest.json').read_bytes()),
                      'case':ident,'adjudication':['utc-text-readback-v1'] if ident in (11,12) else ['integer-protocol-readback-v1']}})
    for task in (timestamp,pagination,username):
        for variant in ('good','alternative'):
            index=len(cases);target=output/'frozen'/str(index);target.mkdir()
            specs.s6.seed(target/'product',task,variant)
            (target/'source.md').write_text(specs.s6.corpus.source(task))
            (target/'accepted-input.md').write_text(specs.s6.corpus.brief(task))
            base=p.host.git(target/'product','rev-parse','HEAD')
            cases.append({'id':index,'task':task['id'],'positive':True,'origin':{'reference':variant},
                          'base_commit':base,'frozen':str(target)})
    context='''Public domain facts, not private evaluator inputs or answers:
Decimal hours/minutes/seconds represent fractions of their lowest included unit; conversion precedes dropping subsecond precision (ISO 8601-1:2019/Amd 1:2022, clause 5.3.1.4).
IERS Leap_Second.dat, updated through Bulletin C 72 (July 2026), records leap-second effective dates; no leap second is announced for December 2026. The public metadata is time-dependent, frozen here, not a narrowing of the promise.
Sources: https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf
https://hpiers.obspm.fr/iers/bul/bulc/Leap_Second.dat
https://hpiers.obspm.fr/iers/bul/bulc/bulletinc.dat
ISO 8601-1:2019 clauses 5.2.2.3 and 5.2.3.2 make expanded year widths agreement-dependent; the six-digit examples do not fix the width. The source retains the actual user's clarification: without an agreement reject ambiguous strings and accept unambiguous forms. Do not silently invent a width or use Python's year range as the domain.
Clause 3.2.4 assigns PLUS to positive or zero values and MINUS to negative values. Zero UTC offsets use PLUS or Z. Clauses 3.2.1 and 3.2.4 define graphic signs and separators independently of a character encoding.
Final 2019 text reproduction: https://previewnorm.com/iso/ISO%208601%201%20WG-2019%20PDF.pdf
'''
    for case in cases:
        target=Path(case['frozen']);mapping=target/'execution-map.md'
        if case['task']=='utc-timestamps':clarify(target)
        evidence=specs.contract(case['task'],(target/'source.md').read_text(),p.host.git(target/'product','rev-parse',case['base_commit']+'^{tree}'))
        (target/'source-evidence.json').write_bytes(p.challenges.encoded(evidence));p.challenges.attach(target,evidence)
        mapping.write_text((mapping.read_text() if mapping.exists() else previous.interface_map())+'\n'+context)
        if case['task']=='utc-timestamps':
            with mapping.open('a') as stream:stream.write('ISO clock-unit duration can change at an inserted leap second (3.1.2.3 through 3.1.2.6 and 4.2.3). Decimal units must preserve the actual instant. Test ambiguity after complete timestamp validity; date-only alternatives can have different time validity. These are source implications, not private expected outputs.\n')
        case['snapshot']=p.host.snapshot(target)['sha256']
        case['contract_sha256']=p.host.sha256(p.challenges.encoded(evidence))
    runtime={Path(module.__file__).resolve() for module in (p,p.host,p.live,p.challenges,p.contract_input,
             p.intentline_input,p.publication,specs,specs.metamorphic,previous,specs.s6,specs.s6.corpus,utc,iso_audit)}
    runtime|={Path(__file__).resolve(),p.host.ROOT/'checks/s6_challenges.py',p.host.ROOT/'checks/s0_live.py',
              p.host.ROOT/'checks/s6_acceptance_audit.py',p.host.ROOT/'checks/s6_regression_audit.py'}
    archive=output/'runtime-archive';archive.mkdir()
    files={str(path):p.host.sha256(path.read_bytes()) for path in sorted(runtime)}
    for index,path in enumerate(sorted(runtime)):shutil.copyfile(path,archive/str(index))
    codex=p.host.find_codex(None)
    manifest={'kind':'s6_source_contract_native_qualification','declared_at':datetime.now(timezone.utc).isoformat(),
        'models':original['models'],'cases':cases,'tasks':tasks,'files':files,
        'codex_sha256':p.host.sha256(Path(codex).read_bytes()),'python':sys.version,'system':p.platform.platform(),
        'limits':{'jobs':4,'stage_seconds':600,'probe_seconds':30},
        'verification_remedy':{'transport':'Production source-evidence-v1; unchanged three-stage acceptance and strict native citations.',
            'mechanism':'Source-declared ordering, text and integer representation relations compiled into sealed executable evidence. Independently vary ordering capabilities and optional text/integer instance methods; compare normalized outcomes and error families without task answer keys.',
            'necessity':'Repeated native false acceptances share untested optional-operator assumptions with public probes. Source-declared ordering, text and integer representations now remove capabilities systematically; integer readback additionally disproved two unexecuted proposed positives before dispatch.',
            'limits':'The caller must justify each relation and its valid samples from the source. Representation invariance cannot establish baseline correctness or complete source coverage; independent source invariants and native adjudication remain mandatory.',
            'prior_trust_stop':'representation-qualification-v1 and all earlier runs remain stopped and retained. This new scalar-capability declaration does not resume them or reuse favorable judgments; another false acceptance stops dispatch.'},
        'source_basis':{'interface':'Original app.py mapping and original seed public behavior, not restrictions of preserved candidates.',
            'normative_references':[
                {'url':'https://science.data.nasa.gov/fits/documentation/iso-time','fact':'ISO time notation includes second 60 during an inserted leap second.'},
                {'url':'https://datacenter.iers.org/data/16/bulletinc-052.txt','fact':'IERS Bulletin C 52 records the UTC sequence 2016-12-31 23:59:59, 23:59:60, then 2017-01-01 00:00:00.'},
                {'url':'https://docs.python.org/3.14/library/datetime.html','fact':'Python datetime has no leap-second representation; fractional hours/minutes are unsupported.'},
                {'url':'https://www.unicode.org/Public/18.0.0/ucd/PropList.txt','fact':'Unicode White_Space property supplies the username rejection predicate.'}],
            'interpretation':'Public primary facts, final 2019 text and the actual user clarification support the domain interpretation. No standard PDF possession requirement or Python-parser subset is substituted.',
            'user_clarification':{'date':'2026-10-12','question':'The original UTC task supplies no agreement for expanded year widths. For example, `+0020240101T000000Z` can denote 2024-01-01 with a six-digit calendar year, or year 20240, ordinal day 101 with a seven-digit year. Should ambiguous strings without an agreement raise ValueError, while unambiguous ISO forms remain accepted, or does the project have a convention that resolves them?',
                'answer':'I follow your recommendation','source_note':utc.CLARIFICATION,
                'scope':'New qualification only. Original requests are retained separately and historical outcomes remain unchanged.'},
            'new_context':context},
        'gate':'All independent controls and invariant expectations match, every full-source contract is ready, both models reject defects and accept positives/alternatives, and both production recovery sets pass. Any gap stops before comparisons.',
        'predictions':'Both models reject all fifteen retained defective candidates, including former pagination, username and UTC positives, and accept all six proposed corrected controls/structural alternatives. Independent native preflight precedes model judgments; unavailable invocations remain gaps.',
        'conditional_judgments':len(cases)*len(original['models'])*2,'conditional_recovery':{'models':list(original['models']),'task':'interval-union',
            'cases':['third-implementation','weak-evidence','valid-alternative'],'seconds':2400,'stage_seconds':600,'dispatches':12,
            'justification':'Prior third-implementation recovery used 1635.4 seconds. Preserve equal prospective headroom for source-invariant execution and checking; limits frozen before scoring.'},
        'exposure':'All tasks are exposed regressions, not efficacy samples. Source invariants contain no private grader probes/results.',
        'pricing':None,'operator_attention_seconds':None}
    p.write_record(output/'manifest.json',manifest)
    p.write_record(output/'report.json',{'status':'DECLARED','manifest_sha256':p.host.sha256((output/'manifest.json').read_bytes()),
        'controls':[],'readiness':[],'judgments':[],'recovery':[],'model_dispatches':0})
    return manifest


def run(output):
    manifest=previous.validate(output);report=json.loads((output/'report.json').read_text())
    if report['status']!='DECLARED':raise ValueError('Qualification is single-use; preserve its result')
    started=time.monotonic();report['status']='RUNNING';p.write_record(output/'report.json',report)
    codex=p.host.find_codex(None)
    for case in manifest['cases']:
        inputs=Path(case['frozen']);contract=json.loads((inputs/'source-evidence.json').read_text())
        try:
            p.challenges.validate_contract(contract,(inputs/'source.md').read_text(),['R1','R2','R3'],
                                          p.host.git(inputs/'product','rev-parse',case['base_commit']+'^{tree}'))
            ready={'case':case['id'],'ready':True}
        except ValueError as exc:ready={'case':case['id'],'ready':False,'gap':str(exc)}
        report['readiness'].append(ready)
        independent=specs.s6.evaluate(inputs/'product',manifest['tasks'][case['task']],codex=codex,
                                     directory=output/'operator'/('independent-'+str(case['id'])))
        replay=previous.probe_control(output,case,{'model':'source-contract','stage':{'report':contract}},codex,
                                      manifest['limits']['probe_seconds'])
        report['controls'].append({'case':case['id'],'declared_positive':case['positive'],
            'independent':independent,'invariants':replay,
            'matched':independent['observed'] and independent['correct']==case['positive'] and replay['matched']})
        p.write_record(output/'report.json',report)
        print('control',case['id'],case['task'],'matched',report['controls'][-1]['matched'],'ready',ready['ready'],flush=True)
        previous.validate(output)
    calibrated=all(x['matched'] for x in report['controls']) and all(x['ready'] for x in report['readiness'])
    def judge(key):
        model,case,role=key
        folder=output/'judgments'/model/str(case['id'])/role;folder.mkdir(parents=True)
        inputs=folder/'inputs';shutil.copytree(case['frozen'],inputs,symlinks=True)
        identity=p.identities(inputs,case['base_commit'])
        stage=p.live.run_stage(codex,folder,inputs,identity,role,manifest['models'][model],manifest['limits']['stage_seconds'],
            make_prompt=lambda r,i,b,canary=None:p.prompt(r,i,b,canary,ids=['R1','R2','R3'],
                execution_map=(inputs/'execution-map.md').read_text())+p.challenges.guidance(i),
            criterion_ids=['R1','R2','R3'],target=inputs/'product/product.py')
        if role=='prover' and stage['status']=='OBSERVED':
            try:p.challenges.validate_execution(stage['report'],stage['commands'],inputs)
            except (ValueError,KeyError,OSError) as exc:
                stage.update(status='NOT VERIFIED',error=str(exc));p.write_record(folder/'stage.json',stage)
        expected=('PASS' if role=='reviewer' else 'PROVEN') if case['positive'] else 'FAIL'
        return {'model':model,'case':case['id'],'role':role,'stage':stage,
                'matched':stage['status']=='OBSERVED' and stage['report']['verdict']==expected}
    keys=[(model,case,role) for model in manifest['models'] for case in manifest['cases'] for role in ('reviewer','prover')]
    trust_stop=False
    for start in range(0,len(keys),manifest['limits']['jobs']):
        batch=keys[start:start+manifest['limits']['jobs']]
        with ThreadPoolExecutor(max_workers=manifest['limits']['jobs']) as pool:
            entries=list(pool.map(judge,batch)) if calibrated and not trust_stop else [
                {'model':m,'case':c['id'],'role':r,'status':'NOT EXECUTED','matched':False} for m,c,r in batch]
        report['judgments'].extend(entries);report['model_dispatches']+=sum('stage' in x for x in entries)
        for entry in entries:
            stage=entry.get('stage',{})
            if not manifest['cases'][entry['case']]['positive'] and stage.get('status')=='OBSERVED' and stage['report']['verdict'] in ('PASS','PROVEN'):
                trust_stop=True
        p.write_record(output/'report.json',report);previous.validate(output)
    if calibrated and all(x['matched'] for x in report['judgments']):
        config=manifest['conditional_recovery']
        for model in config['models']:
            result=recovery(output/'recovery'/model,manifest['models'][model]['model'],config['seconds'],
                            config['stage_seconds'],config['task'],source_evidence=True,execution_map=previous.interface_map())
            report['recovery'].append({'model':model,'report':result});report['model_dispatches']+=sum(x['dispatches'] for x in result['cases'])
            p.write_record(output/'report.json',report);previous.validate(output)
            if result['status']!='OBSERVED':break
    passed=calibrated and all(x['matched'] for x in report['judgments']) and len(report['recovery'])==len(manifest['models']) and all(x['report']['status']=='OBSERVED' for x in report['recovery'])
    report.update(status='TRUST QUALIFIED' if passed else 'TRUST QUALIFICATION FAILED',
                  elapsed_seconds=time.monotonic()-started,calibrated=calibrated,trust_stop=trust_stop,
                  integrity='PASSED' if previous.validate(output) else 'FAILED')
    p.write_record(output/'report.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('declare','run'));parser.add_argument('output',type=Path)
    args=parser.parse_args();result=(declare if args.command=='declare' else run)(args.output.resolve())
    if args.command=='run':raise SystemExit(0 if result['status']=='TRUST QUALIFIED' else 2)
