"""Reproduce this completed study's compact report; no model or check execution."""
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
import zipfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY.parents[2]))
from checks import host_probe as host
from evaluation.sol_luna_host.accounting import normalize

with zipfile.ZipFile(DIRECTORY/'raw-evidence.zip') as archive:
    raw = archive.read('results.json')
    manifest = json.loads(archive.read('manifest.json'))
    result = normalize(json.loads(raw))
assert result['status'] == 'COMPLETE' and len(result['assignments']) == 20
rates = {'gpt-6-luna': ['2.5', '0.25', '12.5'], 'gpt-6.1-sol': ['50', '2.5', '250']}

def project(tokens, model):
    values = [tokens['input_tokens']-tokens['cached_input_tokens'],
              tokens['cached_input_tokens'], tokens['output_tokens']]
    assert min(values) >= 0
    return sum(Decimal(v)*Decimal(p) for v,p in zip(values,rates[model]))/1000000

assert project({'input_tokens':1000000,'cached_input_tokens':1000000,'output_tokens':0},'gpt-6-luna') == Decimal('0.25')
assert project({'input_tokens':1000000,'cached_input_tokens':0,'output_tokens':1000000},'gpt-6.1-sol') == 300
rows = []
for row in result['assignments']:
    stages = [{k:s.get(k) for k in ('stage','model','reasoning_effort','status','thread_id',
        'elapsed_seconds','usage','observed_session_usage','tool_executions')} for s in row['stages']]
    for stage,original in zip(stages,row['stages']):
        stage['failed_commands'] = sum(c['exit_code'] != 0 for c in original['commands'].values())
        if stage['stage'] == 'verification':
            stage['findings'] = original['report']['findings']
    compact = {k:row.get(k) for k in ('sequence','task','arm','status','total_seconds',
        'workflow_seconds','grading_seconds','model_seconds','plan_status','review_status',
        'initial_candidate','final_candidate','correction','controller_processes',
        'operator_candidate_edits','extra_worker_messages')}
    compact.update(stages=stages, check_seconds=sum(c['elapsed_seconds'] for c in row['checks']),
        check_statuses=[c['status'] for c in row['checks']])
    for phase in ('initial','final'):
        compact[phase+'_grade']={k:row[phase+'_grade'].get(k) for k in
            ('available','correct','failures','repository_tests_passed','elapsed_seconds')}
    rows.append(compact)
phases = {}
projection = {}
family = {}
for arm,metrics in result['metrics']['arms'].items():
    assigned = [r for r in rows if r['arm']==arm]
    phase = {role:sum(s['elapsed_seconds'] for r in assigned for s in r['stages'] if s['stage']==role)
             for role in ('planning','implementation','verification','correction')}
    phase.update(checking=sum(r['check_seconds'] for r in assigned), grading=metrics['grading_seconds'])
    phase['setup_freezing_and_other'] = metrics['total_seconds']-sum(phase.values())
    assert phase['setup_freezing_and_other'] >= 0
    phases[arm] = phase
    components = {m:project(v['tokens'],m) for m,v in metrics['models'].items()}
    successes = metrics['independently_correct_deliveries']
    projection[arm] = {'total':float(sum(components.values())),
        'per_correct_delivery':float(sum(components.values())/successes)}
    family[arm] = [components['gpt-6-luna']/Decimal('2.5')/successes,
                   components['gpt-6.1-sol']/Decimal('50')/successes]
h_l,h_s=family['hybrid'];l_l,_=family['luna'];s_l,s_s=family['sol']
threshold = (l_l-h_l)/h_s
summary = {'study':result['study'],'status':result['status'],
    'freeze_sha256':manifest['identities']['freeze_sha256'],
    'source_result_sha256':host.sha256(raw),'analysis_source_sha256':host.sha256(Path(__file__).read_bytes()),
    'accounting_source_sha256':host.sha256((DIRECTORY.parents[2]/'evaluation/sol_luna_host/accounting.py').read_bytes()),
    'started_at':result['started_at'],'finished_at':result['finished_at'],
    'campaign_seconds':(datetime.fromisoformat(result['finished_at'])-datetime.fromisoformat(result['started_at'])).total_seconds(),
    'preparation_seconds':result['preparation_seconds'],'native_dispatches':result['model_dispatches'],
    'reused_qualification_new_dispatches':0,'observed_dollars':None,'observed_credit_debit':None,
    'metrics':result['metrics'],'phase_seconds':phases,'assignments':rows,
    'pricing_sensitivity':{'label':'Hypothetical standard token-rate projection; NOT observed credits or dollars',
        'source':'https://learn.chatgpt.com/docs/pricing','accessed':'2026-10-13',
        'credits_per_million_input_cached_output':rates,'projected_credits':projection,
        'excludes':'Check compute, preparation/qualification, authoring, human attention and unexposed provider charges',
        'family':'C(r)=L+r*S per correct delivery. Luna cache/input=.1; Sol cache/input=.05; output/input=5. r=Sol/Luna uncached unit price; published standard credit ratio is 20.',
        'components':{a:{'L':float(l),'S':float(s)} for a,(l,s) in family.items()},
        'hybrid_cheaper_than_luna_requires_r_below':float(threshold) if threshold>0 else None,
        'hybrid_vs_sol_positive_break_even_r':float((h_l-s_l)/(s_s-h_s)) if s_s>h_s else None}}
(DIRECTORY/'results-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'phase_seconds':phases,'pricing_sensitivity':summary['pricing_sensitivity']},indent=2))
