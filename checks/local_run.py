"""One bounded coding attempt and caller-selected checks; no acceptance verdict."""
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

from checks import codex_live as live, host_probe as host
from checks import coding_attempt as coding
from checks.native_checks import oracle_runner, write_record

LAUNCHER='import json,os,sys;os.chdir(sys.argv[1]);os.environ["PYTHONDONTWRITEBYTECODE"]="1";os.execvpe(json.loads(sys.argv[2])[0],json.loads(sys.argv[2]),os.environ)'


def check_argv(python,inputs,argv):
    return [python,'-I','-B','-c',LAUNCHER,str(inputs/'product'),json.dumps(argv)]


def validate_checks(checks):
    if (not isinstance(checks,list) or not checks or
            any(not isinstance(argv,list) or not argv or
                any(not isinstance(arg,str) or '\0' in arg for arg in argv) or not argv[0]
                for argv in checks)):
        raise ValueError('Checks must be a nonempty JSON list of argument lists; no shell parsing')
    return checks


def run(repo,source,checks,output,seconds=900,stage_seconds=600,check_seconds=120):
    validate_checks(checks)
    if (not source.strip() or any(type(value) not in (int,float) or not math.isfinite(value)
            or value<=0 for value in (seconds,stage_seconds,check_seconds)) or seconds<=check_seconds):
        raise ValueError('Source and positive finite budgets with time reserved for checks are required')
    if platform.system()!='Darwin' or sys.version_info<(3,11):
        raise ValueError('The supported native boundary is macOS with Python 3.11+')
    output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    record={'schema_version':1,'kind':'bounded_local_run','status':'EXECUTION UNAVAILABLE',
            'assurance':'Only the listed command exit statuses are observed; full source correctness is not certified.',
            'limits':{'seconds':seconds,'stage_seconds':stage_seconds,'check_seconds':check_seconds,'model_dispatches':1},
            'checks':checks,'observations':[],'model_dispatches':0,'stages':[],'published':False,'merged':False,
            'python':str(Path(sys.executable).resolve())}
    def save():
        record['elapsed_seconds']=time.monotonic()-started
        write_record(output/'report.json',record)
    save()
    try:
        codex=host.find_codex(None)
        if not codex:raise ValueError('Supported Codex CLI unavailable')
        version=host.run_command([codex,'--version'],output)
        record['version_receipt']=version
        if not host.succeeded(version) or version['stdout'].strip()!='codex-cli 0.162.1':
            raise ValueError('This boundary requires Codex CLI 0.162.1')
        record['model_preferences']=live.preferences()
        allowance=min(stage_seconds,seconds-(time.monotonic()-started)-check_seconds)
        if allowance<=0:raise ValueError('Implementation budget unavailable')
        delivery=coding.run(repo,source,'Caller-selected checks: '+json.dumps(checks),
                            output/'coding',codex,record['model_preferences'],allowance,
                            'Run useful checks. The host will run the caller-selected commands afterward; their results do not certify the complete request.')
        record.update(stages=delivery['stages'],model_dispatches=delivery['model_dispatches'],candidate_path=delivery['candidate'])
        if not delivery['accepted']:
            record['implementation_handoff']='unavailable or reported incomplete'
            save();return record
        inputs=Path(record['candidate_path']).parent
        (inputs/'checks.json').write_text(json.dumps(checks))
        record['snapshot']=host.snapshot(inputs)['sha256']
        record['candidate_commit']=host.git(inputs/'product','rev-parse','HEAD')
        record['status']='RUNNING CHECKS';save()
        for index,argv in enumerate(checks):
            remaining=seconds-(time.monotonic()-started)
            entry={'argv':argv,'status':'UNAVAILABLE','receipts':[],'elapsed_seconds':0.0};record['observations'].append(entry)
            if remaining<=0:
                entry['error']='Cumulative budget exhausted';record['status']='CHECKS UNAVAILABLE';break
            scratch=output/('check-'+str(index));scratch.mkdir()
            check_started=time.monotonic()
            try:
                result=oracle_runner(codex,inputs,output/'private',entry['receipts'])(
                    check_argv(record['python'],inputs,argv),
                    cwd=scratch,timeout=min(check_seconds,remaining))
                if 'sandbox-exec: sandbox_apply:' in result.stderr:raise OSError('Native sandbox initialization unavailable')
                entry.update(returncode=result.returncode,status='PASSED' if result.returncode==0 else 'FAILED')
            except (OSError,subprocess.SubprocessError) as error:
                entry['error']=str(error)
            finally:
                entry['elapsed_seconds']=max(0.0,time.monotonic()-check_started)
            if host.snapshot(inputs)['sha256']!=record['snapshot']:raise ValueError('Frozen check inputs changed')
            save()
        if any(x['status']=='UNAVAILABLE' for x in record['observations']):record['status']='CHECKS UNAVAILABLE'
        elif any(x['status']=='FAILED' for x in record['observations']):record['status']='CHECKS FAILED'
        else:record['status']='CHECKS PASSED'
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        record['status']='EXECUTION UNAVAILABLE';record['error']=str(error) or type(error).__name__
    finally:save()
    return record


def inspect(path):
    record=json.loads(path.read_text())
    if record.get('kind')!='bounded_local_run' or record.get('schema_version')!=1:
        raise ValueError('Unsupported bounded run record')
    validate_checks(record['checks'])
    if record['status']=='CHECKS PASSED':
        inputs=Path(record['candidate_path']).parent
        if (host.snapshot(inputs)['sha256']!=record['snapshot'] or
                json.loads((inputs/'checks.json').read_text())!=record['checks']):
            record['status']='STALE CHECKS'
        elif (len(record['observations'])!=len(record['checks']) or
              any(entry['argv']!=argv or entry['status']!='PASSED' or entry['returncode']!=0
                  or len(entry['receipts'])!=1 or not host.succeeded(entry['receipts'][0])
                  or any(entry['receipts'][0].get(key) for key in ('stdout_truncated','stderr_truncated'))
                  or json.loads(entry['receipts'][0]['argv'][-1])!=check_argv(record['python'],inputs,argv)
                  for entry,argv in zip(record['observations'],record['checks']))):
            raise ValueError('Incomplete successful command observations')
    return record
