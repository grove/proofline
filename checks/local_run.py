"""Model-free checks or one coding attempt; no full-promise acceptance verdict."""
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

from checks import codex_live as live, host_probe as host
from checks import coding_attempt as coding
from checks import feedback
from checks import promise_evidence
from checks.native_checks import oracle_runner, write_record
from checks.candidate_snapshot import capture_worktree, git_bytes

LAUNCHER = """import json,os,sys
try:
    os.chdir(sys.argv[1])
    os.environ["PYTHONDONTWRITEBYTECODE"]="1"
    argv=json.loads(sys.argv[2])
    os.execvpe(argv[0],argv,os.environ)
except OSError as error:
    print("Proofline check launch unavailable: "+str(error),file=sys.stderr)
    sys.exit(127)
"""


def check_argv(python,inputs,argv):
    return [python,'-I','-B','-c',LAUNCHER,str(inputs/'product'),json.dumps(argv)]


def validate_checks(checks):
    if (not isinstance(checks,list) or not checks or
            any(not isinstance(argv,list) or not argv or
                any(not isinstance(arg,str) or '\0' in arg for arg in argv) or not argv[0]
                or not Path(argv[0]).is_absolute() for argv in checks)):
        raise ValueError('Checks require nonempty argument lists with absolute executable paths; no shell parsing')
    return checks


def run(repo,source,checks,output,seconds=900,stage_seconds=600,check_seconds=120, failure_details=None):
    validate_checks(checks)
    failure_details=feedback.validate_failure_details(failure_details,checks)
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
            'python':str(Path(sys.executable).resolve()),'feedback_version':1,
        'failure_details':failure_details,'source_sha256':host.sha256(source.encode('utf-8'))}
    def save():
        record['elapsed_seconds']=time.monotonic()-started
        record['feedback']=feedback.summarize(record)
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
        if failure_details:
            (inputs/'failure-details.json').write_text(json.dumps(failure_details,ensure_ascii=False))
        record['snapshot']=host.snapshot(inputs)['sha256']
        record['candidate_commit']=host.git(inputs/'product','rev-parse','HEAD')
        record['candidate_tree']=host.git(inputs/'product','rev-parse','HEAD^{tree}')
        record['status']='RUNNING CHECKS';save()
        execute_checks(record,inputs,output,codex,started,save)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        record['status']='EXECUTION UNAVAILABLE';record['error']=str(error) or type(error).__name__
    finally:save()
    return record


def execute_checks(record,inputs,output,codex,started,save):
    for index,argv in enumerate(record['checks']):
        remaining=record['limits']['seconds']-(time.monotonic()-started)
        entry={'argv':argv,'status':'UNAVAILABLE','receipts':[],'elapsed_seconds':0.0};record['observations'].append(entry)
        if remaining<=0:
            entry['error']='Cumulative budget exhausted';record['status']='CHECKS UNAVAILABLE'
            feedback.attach_details(entry,record.get('failure_details',[]),index)
            break
        scratch=output/('check-'+str(index));scratch.mkdir()
        check_started=time.monotonic()
        try:
            result=oracle_runner(codex,inputs,output/'private',entry['receipts'])(
                check_argv(record['python'],inputs,argv),
                cwd=scratch,timeout=min(record['limits']['check_seconds'],remaining))
            if 'sandbox-exec: sandbox_apply:' in result.stderr:
                raise OSError('Native sandbox initialization unavailable')
            if 'Proofline check launch unavailable:' in result.stderr:
                raise OSError(result.stderr.strip())
            entry.update(returncode=result.returncode,status='PASSED' if result.returncode==0 else 'FAILED')
        except (OSError,subprocess.SubprocessError) as error:
            entry['error']=str(error)
        finally:
            entry['elapsed_seconds']=max(0.0,time.monotonic()-check_started)
            feedback.save_receipt(entry,output,index)
            feedback.attach_details(entry,record.get('failure_details',[]),index)
        if host.snapshot(inputs)['sha256']!=record['snapshot']:raise ValueError('Frozen check inputs changed')
        save()
    if any(x['status']=='UNAVAILABLE' for x in record['observations']):record['status']='CHECKS UNAVAILABLE'
    elif any(x['status']=='FAILED' for x in record['observations']):record['status']='CHECKS FAILED'
    else:record['status']='CHECKS PASSED'


def check(repo,source,checks,output,seconds=900,check_seconds=120,
          failure_details=None, promise_mapping=None):
    """Freeze an existing working candidate and observe commands without model dispatch."""
    validate_checks(checks)
    failure_details=feedback.validate_failure_details(failure_details,checks)
    if promise_mapping is not None:
        promise_mapping=promise_evidence.validate(promise_mapping,source,checks,failure_details)
    if (not source.strip() or any(type(value) not in (int,float) or not math.isfinite(value)
            or not 0<value<=3600 for value in (seconds,check_seconds))):
        raise ValueError('Source and positive finite budgets of at most 3600 seconds are required')
    repo,output=repo.resolve(),output.resolve()
    if output==repo or repo in output.parents:
        raise ValueError('Check output must be outside the source repository')
    started=time.monotonic()
    try:
        if git_bytes(repo,'rev-parse','--show-toplevel').decode().strip()!=str(repo):
            raise ValueError('--repo must name the Git repository root')
        metadata=[(repo/raw.decode().strip()).resolve() for raw in
                  (git_bytes(repo,'rev-parse','--absolute-git-dir'),
                   git_bytes(repo,'rev-parse','--git-common-dir'))]
    except (OSError,subprocess.SubprocessError) as error:
        raise ValueError('--repo must name an existing Git repository root') from error
    if any(output==path or path in output.parents for path in metadata):
        raise ValueError('Check output must be outside source Git metadata')
    output.mkdir(parents=True,exist_ok=False)
    record={'schema_version':1,'kind':'bounded_local_check','status':'EXECUTION UNAVAILABLE',
            'assurance':'Only the listed command exit statuses are observed; full source correctness is not certified.',
            'limits':{'seconds':seconds,'check_seconds':check_seconds,'model_dispatches':0},
            'checks':checks,'observations':[],'model_dispatches':0,'stages':[],
            'published':False,'merged':False,'python':str(Path(sys.executable).resolve()),
        'feedback_version':1,'failure_details':failure_details,
        'source_sha256':host.sha256(source.encode('utf-8'))}
    if promise_mapping is not None:
        record['promise_mapping']=promise_mapping
        record['original_source_ref']='inputs/source.md'
    def save():
        record['elapsed_seconds']=time.monotonic()-started
        record['feedback']=feedback.summarize(record)
        if promise_mapping is not None:
            record['promise_evidence']=promise_evidence.summarize(record)
        write_record(output/'report.json',record)
    save()
    try:
        if platform.system()!='Darwin' or sys.version_info<(3,11):
            raise ValueError('The supported native boundary is macOS with Python 3.11+')
        inputs=output/'inputs';inputs.mkdir()
        (inputs/'source.md').write_bytes(source.encode('utf-8'))
        (inputs/'checks.json').write_text(json.dumps(checks))
        if failure_details:
            (inputs/'failure-details.json').write_text(json.dumps(failure_details,ensure_ascii=False))
        if promise_mapping is not None:
            (inputs/'promises.json').write_text(
                json.dumps(promise_mapping,ensure_ascii=False,sort_keys=True,separators=(',',':')),
                encoding='utf-8')
        record['selection']=capture_worktree(repo,inputs/'product')
        record.update(candidate_path=str(inputs/'product'),
                      candidate_commit=record['selection']['candidate_commit'],
                      candidate_tree=record['selection']['candidate_tree'])
        if promise_mapping is not None:
            promise_evidence.bind_candidate(promise_mapping,record['candidate_tree'])
        codex=host.find_codex(None)
        if not codex:raise ValueError('Supported Codex sandbox CLI unavailable')
        def remaining():
            budget=seconds-(time.monotonic()-started)
            if budget<=0:raise ValueError('Cumulative budget exhausted')
            return min(15,budget)
        version=host.run_command([codex,'--version'],output,remaining())
        record['version_receipt']=version
        if not host.succeeded(version) or version['stdout'].strip()!='codex-cli 0.162.1':
            raise ValueError('This boundary requires Codex CLI 0.162.1; no model authentication is used')
        target=next((path for path in (inputs/'product').rglob('*')
                     if path.is_file() and '.git' not in path.relative_to(inputs/'product').parts),None)
        if target is None:raise ValueError('A regular candidate file is required')
        boundary=output/'preflight';boundary.mkdir()
        record['boundary']=host.probe_boundary(codex,boundary,inputs,remaining(),target)
        if record['boundary']['assessment']['status']!='OBSERVED':
            raise ValueError('Native check boundary unavailable; no unprotected fallback')
        for name in ('canary.py','canary.json'):(inputs/name).unlink()
        record['snapshot']=host.snapshot(inputs)['sha256']
        record['status']='RUNNING CHECKS';save()
        execute_checks(record,inputs,output,codex,started,save)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        record['status']='EXECUTION UNAVAILABLE';record['error']=str(error) or type(error).__name__
    finally:
        save()
        # Keep host evidence outside the candidate and command-writable scratch.
        write_record(output/'evidence.json',record)
        record['evidence_sha256']=host.sha256((output/'evidence.json').read_bytes())
        write_record(output/'report.json',record)
    return record


def _stale(record):
    """A stale result cannot continue advertising old passing promise evidence."""
    record['status']='STALE CHECKS'
    if record.get('feedback_version')==1:
        record['feedback']=feedback.summarize(record)
    if record.get('promise_mapping') is not None:
        record['promise_evidence']=promise_evidence.summarize(record)
    return record


def inspect(path):
    record=json.loads(path.read_text())
    if record.get('kind') not in ('bounded_local_run','bounded_local_check') or record.get('schema_version')!=1:
        raise ValueError('Unsupported bounded run record')
    validate_checks(record['checks'])
    if record.get('feedback_version')==1:
        # A moved or rewritten native receipt is stale, even when the original
        # command reported failure or unavailability. Older reports are unchanged.
        if (not feedback.receipts_intact(record,path.parent) or
                record.get('feedback')!=feedback.summarize(record)):
            return _stale(record)
        if 'snapshot' in record:
            try:
                inputs=Path(record['candidate_path']).parent
                if (host.snapshot(inputs)['sha256']!=record['snapshot'] or
                        host.sha256((inputs/'source.md').read_bytes())!=record['source_sha256'] or
                        json.loads((inputs/'checks.json').read_text())!=record['checks']):
                    raise ValueError('Frozen evidence changed')
            except (OSError,ValueError,KeyError,TypeError):
                record['status']='STALE CHECKS'
                record['feedback']=feedback.summarize(record)
                return record
    if record['kind']=='bounded_local_check':
        try:
            evidence=(path.parent/'evidence.json').read_bytes()
            expected={key:value for key,value in record.items() if key!='evidence_sha256'}
            if (host.sha256(evidence)!=record['evidence_sha256'] or json.loads(evidence)!=expected):
                raise ValueError('Host evidence changed')
            if 'snapshot' in record and host.snapshot(Path(record['candidate_path']).parent)['sha256']!=record['snapshot']:
                raise ValueError('Frozen inputs changed')
        except (OSError,ValueError,KeyError,TypeError):
            record['status']='STALE CHECKS'
            record['feedback']=feedback.summarize(record)
            return record
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
    if record.get('promise_mapping') is not None:
        if record.get('kind')=='bounded_local_check' and 'snapshot' in record:
            # Do not follow a candidate path chosen by an untrusted report.
            fixed_inputs=path.parent/'inputs'
            if (fixed_inputs.is_symlink() or (fixed_inputs/'product').is_symlink() or
                    Path(record.get('candidate_path','')) != fixed_inputs/'product'):
                return _stale(record)
        if (record.get('promise_evidence') != promise_evidence.summarize(record) or
                ('snapshot' in record and not promise_evidence.readback_intact(
                    record,path.parent/'inputs'))):
            return _stale(record)
        record['promise_evidence']=promise_evidence.summarize(record)
    elif record.get('promise_evidence') is not None:
        return _stale(record)
    if record.get('feedback_version')==1:
        record['feedback']=feedback.summarize(record)
    return record
