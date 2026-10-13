#!/usr/bin/env python3
"""Independent R3/library readback: original promises, no worker/prompt changes."""
import argparse
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6
from s0_live import oracle_runner
p=s6.p

LIBRARY_PROBE='''import copy, importlib, json, sys
from enum import IntEnum
sys.path.insert(0,sys.argv[1])
data=json.loads(sys.argv[2])
for field in json.loads(sys.argv[3]):
    data[field]=IntEnum("Integer", {"operand":data[field]}).operand
class Ordered:
    def __init__(self,value): self.value=value
    def __lt__(self,other): return self.value<other.value
    def __eq__(self,other): raise TypeError("equality is unavailable")
class NoIntegerOperators(int):
    def __lt__(self,other):raise TypeError('instance integer comparison unavailable')
    def __add__(self,other):raise TypeError('instance integer addition unavailable')
    def __int__(self):raise TypeError('instance integer conversion unavailable')
class NoStrip(str):
    def strip(self,*args): raise TypeError("instance strip is unavailable")
class NoIteration(str):
    def __iter__(self): raise TypeError("instance iteration is unavailable")
class NoCount(str):
    def count(self,*args): raise TypeError("instance count is unavailable")
mode=sys.argv[4] if len(sys.argv)>4 else "json"
if mode=="integer-operators":
    for field in ("offset","limit"):
        if type(data.get(field)) is int:data[field]=NoIntegerOperators(data[field])
elif mode in ("text-strip","text-iteration","text-count"):
    data={"text-strip":NoStrip,"text-iteration":NoIteration,"text-count":NoCount}[mode](data)
elif mode!="json":
    for row in data["rows"]:
        for field in ("score","id") if mode=="row-ordering" else ("score",):
            if field in row: row[field]=Ordered(row[field])
def encode(value):
    if isinstance(value,Ordered): return value.value
    raise TypeError("unexpected value")
before=json.dumps(data,sort_keys=True,ensure_ascii=True,default=encode)
try:
    value=importlib.import_module("product").process(data)
    result={"value":value,"error_type":None,"value_error":False,"handled_error":False}
except Exception as error:
    result={"value":None,"error_type":type(error).__name__,"value_error":isinstance(error,ValueError),"handled_error":isinstance(error,(ValueError,KeyError,TypeError))}
result["input_unchanged"]=json.dumps(data,sort_keys=True,ensure_ascii=True,default=encode)==before
print(json.dumps(result,ensure_ascii=True,sort_keys=True,allow_nan=False,default=encode))
'''


def inspect(candidate,item,directory,codex=None):
    directory=directory.resolve();directory.mkdir(parents=True,exist_ok=False)
    inputs=directory/'inputs';inputs.mkdir()
    s6.shutil.copytree(candidate,inputs/'product',symlinks=True,ignore=s6.shutil.ignore_patterns('.git','.p2p','__pycache__','*.pyc'))
    p.validate_links(inputs/'product')
    before=p.host.snapshot(inputs)
    local={path.stem for path in (inputs/'product').glob('*.py')} | {path.name for path in (inputs/'product').iterdir() if path.is_dir()}
    foreign=[]
    for path in (inputs/'product').rglob('*.py'):
        try:
            for node in ast.walk(ast.parse(path.read_text())):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.level==0 and node.module else []
                for name in names:
                    if name.split('.')[0] not in sys.stdlib_module_names | local:
                        foreign.append({'path':str(path.relative_to(inputs/'product')),'module':name})
        except (SyntaxError,UnicodeError) as error:
            foreign.append({'path':str(path),'invalid_python':str(error)})
    observations=[];receipts=[]
    cases=[(probe, [], 'json') for probe in item['probes']]
    fields=item.get('library_integer_fields', [])
    if fields:
        cases += [(probe, fields, 'json') for probe in item['probes'] if isinstance(probe['input'], dict)
                  and all(type(probe['input'].get(field)) is int for field in fields)]
    if item['id']=='stable-pagination':
        cases += [(probe, [], mode) for probe in item['probes'] for mode in ('score-ordering','row-ordering','integer-operators')
                  if isinstance(probe['input'],dict) and isinstance(probe['input'].get('rows'),list)]
    modes={'unicode-usernames':('text-strip','text-iteration'),
           'utc-timestamps':('text-count',)}.get(item['id'],())
    cases += [(probe, [], mode) for probe in item['probes'] for mode in modes
              if isinstance(probe['input'],str)]
    for probe, integer_fields, mode in cases:
        with tempfile.TemporaryDirectory(prefix='proofline-s6-library-') as temporary:
            scratch=Path(temporary).resolve()
            runner=oracle_runner(codex,inputs,directory/'private',receipts) if codex else subprocess.run
            observation={'input':probe['input'],'integer_subclass_fields':integer_fields,'ordering_mode':mode,'status':'NOT VERIFIED'}
            try:
                result=runner([str(Path(sys.executable).resolve()),'-I','-B','-S','-c',LIBRARY_PROBE,str(inputs/'product'),json.dumps(probe['input'],ensure_ascii=True),json.dumps(integer_fields),mode],cwd=scratch,timeout=8,capture_output=True,text=True,check=False)
                observation.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
                if codex and 'sandbox-exec: sandbox_apply:' in result.stderr: raise OSError('Native sandbox unavailable')
                try:
                    payload=json.loads(result.stdout)
                    expected=probe['expected']
                    error=isinstance(expected,dict) and expected.get('error') is True
                    requires_value_error='ValueError' in item['requirement'] or error and expected.get('value_error') is True
                    valid_error=payload['value_error'] is True if requires_value_error else payload['handled_error'] is True
                    matched=(valid_error if error else payload['error_type'] is None and s6.same_json(payload['value'],expected))
                    matched=matched and payload['input_unchanged'] is True and result.returncode==0 and not result.stderr and not any(scratch.iterdir())
                except (ValueError,KeyError,TypeError): matched=False
                observation['status']='SATISFIED' if matched else 'VIOLATED'
            except (OSError,subprocess.SubprocessError) as error: observation['error']=str(error)
            observations.append(observation)
    unchanged=p.host.snapshot(inputs)==before
    result={'correct':not foreign and unchanged and all(o['status']=='SATISFIED' for o in observations),
        'observed':unchanged and all(o['status']!='NOT VERIFIED' for o in observations),
        'foreign_imports':foreign,'unchanged':unchanged,'observations':observations,'receipts':receipts}
    p.write_record(directory/'report.json',result)
    return result


def declare(campaign,output):
    manifest,report=s6.verify_declaration(campaign,runtime=False)
    output.mkdir(parents=True,exist_ok=False)
    record={'kind':'s6_original_promise_audit','declared_at':s6.datetime.now(s6.timezone.utc).isoformat(),
        'campaign':str(campaign),'manifest_sha256':report['manifest_sha256'],
        'checker_sha256':p.host.sha256(Path(__file__).read_bytes()),'tasks_sha256':manifest['tasks_sha256'],
        'grader_files':{str(Path(module.__file__).resolve()):p.host.sha256(Path(module.__file__).read_bytes()) for module in (s6,s6.corpus,p,p.host,p.live)},
        'reason':'Public CLI checks alone do not establish the source-promised library input immutability, ValueError semantics or standard-library constraint. Fixed original promises are unchanged; all candidates receive the same added readback.',
        'worker_changes':False,'prompt_changes':False,'oracle_expected_value_changes':False}
    p.write_record(output/'manifest.json',record)
    return record


def audit(campaign,output,codex=None):
    declaration=json.loads((output/'manifest.json').read_text())
    if declaration['checker_sha256']!=p.host.sha256(Path(__file__).read_bytes()): raise ValueError('Audit checker changed')
    for name,expected in declaration['grader_files'].items():
        if p.host.sha256(Path(name).read_bytes())!=expected: raise ValueError('Audit grader changed: '+name)
    operator=campaign/'operator'
    tasks=json.loads((operator/'tasks.json').read_text())
    if declaration['manifest_sha256']!=p.host.sha256((operator/'manifest.json').read_bytes()) or declaration['tasks_sha256']!=p.host.sha256((operator/'tasks.json').read_bytes()): raise ValueError('Original promises changed')
    path=output/'report.json'
    record=json.loads(path.read_text()) if path.exists() else {'status':'RUNNING','controls':[],'assignments':[]}
    started=time.monotonic()
    if not record['controls']:
        for item in tasks:
            for variant,expected in [('good',True),('alternative',True),('seed',False)]:
                if item[variant] is None:continue
                directory=output/'controls'/item['id']/variant
                s6.seed(directory/'source',item,variant)
                observed=inspect(directory/'source',item,directory/'evaluation',codex)
                # Some defective seeds are purely R1 issues; API controls catch them too.
                record['controls'].append({'task':item['id'],'variant':variant,'expected':expected,'result':observed})
                if not observed['observed'] or observed['correct']!=expected:raise ValueError('Library control failed: '+item['id']+'/'+variant)
        item=tasks[1]
        for variant,code in [('mutating-valid-output',item['good'].replace('def process(', 'def original_process(')+'\ndef process(data):\n    result=original_process(data)\n    data["unrequested"]=1\n    return result\n'),('unused-foreign-import',item['good']+'\nif False:\n    import unrequested_vendor_extension\n')]:
            directory=output/'controls'/variant
            s6.seed(directory/'source',dict(item,good=code),'good')
            observed=inspect(directory/'source',item,directory/'evaluation',codex)
            record['controls'].append({'task':item['id'],'variant':variant,'expected':False,'result':observed})
            if not observed['observed'] or observed['correct']:raise ValueError('R3 negative control failed: '+variant)
        item=tasks[0]
        directory=output/'controls'/'valid-error-subclass'
        code='class ValidationError(ValueError):\n    pass\n\n'+item['good'].replace('raise ValueError(', 'raise ValidationError(')
        s6.seed(directory/'source',dict(item,good=code),'good')
        observed=inspect(directory/'source',item,directory/'evaluation',codex)
        record['controls'].append({'task':item['id'],'variant':'valid-error-subclass','expected':True,'result':observed})
        if not observed['observed'] or not observed['correct']:raise ValueError('Valid exception subclass falsely blocked by audit')
        p.write_record(path,record)
    ledger=json.loads((operator/'report.json').read_text())
    seen={a['id'] for a in record['assignments']}
    for assignment in ledger['assignments']:
        result_path=campaign/'runs'/assignment['id']/'result.json'
        if assignment['id'] in seen or not result_path.exists():continue
        raw=json.loads(result_path.read_text())
        original_outcome=raw['outcome']
        delivery=s6.account_delivery(raw['delivery']) if raw.get('delivery') else None
        if not delivery:
            if any(stage.get('receipt',{}).get('timed_out') for stage in raw.get('planning_stages',[])):
                raw['outcome']='BUDGET EXHAUSTED'
            record['assignments'].append({**raw,'original_outcome':original_outcome,'observed':False,'reason':'No delivery candidate; planning/environment failure retained'})
            continue
        item=next(t for t in tasks if t['id']==raw['task'])
        observed=s6.evaluate(Path(delivery['candidate']),item,directory=output/'assignments'/raw['id']/'final',codex=codex)
        if observed['candidate_sha256']!=raw['evaluation']['candidate_sha256']:
            raise ValueError('Historical candidate changed: '+raw['id'])
        outcome=s6.classify(delivery['accepted'],observed,delivery)
        judgments=s6.rejection_scores(delivery,raw['cohort'],item,output/'assignments'/raw['id'],codex)
        record['assignments'].append({**raw,'outcome':outcome,'original_outcome':original_outcome,
            'observed':observed['observed'],'evaluation':observed,'delivery':delivery,'judgment_errors':judgments})
        p.write_record(path,record)
        print(raw['task'],raw['model'],raw['cohort'],outcome,flush=True)
    record['known_audit_seconds']=record.get('known_audit_seconds',0)+time.monotonic()-started
    if ledger['status'] not in {'DECLARED','RUNNING'}:
        seen={a['id'] for a in record['assignments']}
        record['assignments'] += [a for a in ledger['assignments'] if a['id'] not in seen]
    record['status']='TRUST GATE FAILED' if any(a.get('cohort')=='proofline' and a['outcome']=='FALSE ACCEPTED' for a in record['assignments']) else ledger['status']
    p.write_record(path,record)
    manifest,_=s6.verify_declaration(campaign,runtime=False)
    summary=s6.summarize(manifest,{**ledger,**record},json.loads((operator/'rates.json').read_text()))
    p.write_record(output/'summary.json',summary)
    (output/'results.md').write_text(s6.render(summary))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('declare','audit'))
    parser.add_argument('campaign',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.command=='declare':declare(args.campaign.resolve(),args.output.resolve())
    else:
        result=audit(args.campaign.resolve(),args.output.resolve(),p.host.find_codex(None))
        raise SystemExit(2 if result['status']=='TRUST GATE FAILED' else 0)
