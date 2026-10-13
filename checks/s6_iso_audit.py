#!/usr/bin/env python3
"""Independent UTC readback from published clauses; never a full ISO qualification."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks import s6_compare as s6
p=s6.p

PROBES=[
    ('2016-12-31T23:59:60Z','2016-12-31T23:59:60Z','actual leap-second identity'),
    ('2017-01-01T00:59:60+01:00','2016-12-31T23:59:60Z','leap-second offset and date rollover'),
    ('2016-12-31T18:59:60-05:00','2016-12-31T23:59:60Z','leap-second negative offset'),
    ('2017-01-01T05:44:60+05:45','2016-12-31T23:59:60Z','leap-second non-hour offset'),
    ('2024-02-29T12.5Z','2024-02-29T12:30:00Z','fractional hour'),
    ('2024-02-29T12,5+05:45','2024-02-29T06:45:00Z','decimal comma, hour fraction and non-hour offset'),
    ('20240229T1230.5Z','2024-02-29T12:30:30Z','basic-format fractional minute'),
    ('2024-02-29T12:30,5+01:00','2024-02-29T11:30:30Z','extended fractional minute and offset'),
    ('2024-02-29T12.9999Z','2024-02-29T12:59:59Z','fraction converted before subsecond truncation'),
]


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    retained=p.host.ROOT/'.proofline/s6/source-contracts-v1'
    old=json.loads((retained/'manifest.json').read_text())
    selected=[x for x in old['cases'] if x['task']=='utc-timestamps'];cases=[]
    for case in selected:
        original=Path(case['frozen'])
        if p.host.snapshot(original)['sha256']!=case['snapshot']:raise ValueError('Retained fixture changed')
        target=output/'frozen'/str(case['id']);target.parent.mkdir(exist_ok=True)
        shutil.copytree(original,target,symlinks=True)
        cases.append({**case,'frozen':str(target),'prior_declared_positive':case['positive']})
    files={str(Path(module.__file__).resolve()):p.host.sha256(Path(module.__file__).read_bytes())
           for module in (sys.modules[__name__],s6,s6.corpus,p,p.host,p.live)}
    for relative in ('checks/s0_live.py','checks/s6_acceptance_audit.py','checks/s6_regression_audit.py'):
        path=p.host.ROOT/relative;files[str(path)]=p.host.sha256(path.read_bytes())
    archive=output/'runtime-archive';archive.mkdir()
    for index,name in enumerate(files):shutil.copyfile(name,archive/str(index))
    manifest={'kind':'s6_iso_source_readback','declared_at':datetime.now(timezone.utc).isoformat(),
        'cases':cases,'probes':PROBES,'files':files,'codex':p.host.find_codex(None),'python':sys.version,
        'source_basis':[
            {'url':'https://cdn.standards.iteh.ai/samples/70907/5e8d00e639cf4f849462bd63062f4cd8/ISO-8601-1-2019.pdf',
             'availability':'13 PDF pages, ending at printed page 5; clause 5 grammar absent.',
             'clause':'3.1.1.24','fact':'A positive leap second can be represented by second 60 after UTC 23:59:59.'},
            {'url':'https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf',
             'clause':'5.3.1.4','fact':'The lowest included hour, minute or second can have a decimal fraction; lower components are omitted.'},
            {'url':'https://datacenter.iers.org/data/16/bulletinc-052.txt','fact':'An actual positive UTC leap second occurred at the end of 2016.'}],
        'adjudication':'Expected conversions use exact unit arithmetic and published UTC offset meaning, not Python parser results. Fractions are converted to seconds before subsecond precision is dropped.',
        'prediction':'Both previously defective UTC candidates are expected to fail the added source obligations; no positive qualification or model outcome is inferred.',
        'limits':{'native_probe_seconds':8},'model_dispatches':0,'complete_grammar_available':False}
    manifest['codex_sha256']=p.host.sha256(Path(manifest['codex']).read_bytes())
    p.write_record(output/'manifest.json',manifest)
    report={'status':'RUNNING','manifest_sha256':p.host.sha256((output/'manifest.json').read_bytes()),'cases':[]}
    p.write_record(output/'report.json',report);started=time.monotonic()
    for case in cases:
        item=copy.deepcopy(old['tasks']['utc-timestamps'])
        item['probes']=[{'input':value,'expected':expected} for value,expected,_ in PROBES]
        result=s6.evaluate(Path(case['frozen'])/'product',item,codex=manifest['codex'],
                           directory=output/'operator'/str(case['id']))
        report['cases'].append({'id':case['id'],'prior_declared_positive':case['positive'],'evaluation':result})
        p.write_record(output/'report.json',report)
    for name,digest in files.items():
        if p.host.sha256(Path(name).read_bytes())!=digest:raise ValueError('Audit runtime changed')
    for case in cases:
        if p.host.snapshot(Path(case['frozen']))['sha256']!=case['snapshot']:raise ValueError('Audit fixture changed')
    if p.host.sha256(Path(manifest['codex']).read_bytes())!=manifest['codex_sha256']:raise ValueError('Codex changed')
    report.update(status='READBACK OBSERVED' if all(x['evaluation']['observed'] for x in report['cases']) else 'READBACK UNAVAILABLE',
                  elapsed_seconds=time.monotonic()-started,integrity='PASSED',model_dispatches=0,
                  qualification='NOT ESTABLISHED: complete ISO grammar remains unavailable')
    p.write_record(output/'report.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    result=run(parser.parse_args().output.resolve())
    print(result['status'])
    raise SystemExit(0 if result['status']=='READBACK OBSERVED' else 2)
