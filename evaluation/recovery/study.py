"""Issue #34 adapter over existing native isolation and same-thread correction.

prepare/qualify are zero-model. execute requires authorization bound to FREEZE.
No production CLI, reviewer routing, or correction eligibility is changed.
"""
import argparse
import json
from pathlib import Path
import platform
import re
import sys
import time

from checks import candidate_snapshot as snapshots, codex_catalog, codex_live as live, host_probe as host, local_run
from checks.native_checks import oracle_runner, write_record
from evaluation.sol_luna import grader as binding, study as existing
from evaluation.sol_luna_host import accounting, study as previous_host
from evaluation.recovery import corpus, grader, probes, report

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STORE = ROOT / ".proofline/issue34-recovery-v1"
PYTHON = str(Path(sys.executable).resolve())
CODEX = existing.CODEX
ORDINARY_LAUNCH = "import json,os,sys; os.chdir(sys.argv[1]); a=json.loads(sys.argv[2]); os.execvpe(a[0],a,os.environ)"
runner = binding.bound_module(existing, HERE=HERE, STORE=STORE, corpus=corpus, grader=grader)
normalized = binding.bound_module(accounting, report=report)


def protocol():
    return json.loads((HERE / "protocol.json").read_text())


def checks(task):
    return [[PYTHON,"-B","-c",probes.script(task)],
            [PYTHON,"-B","-m","unittest","discover","-s","tests"]]


def ledger():
    spec=protocol()
    order=[(task,"A") for task in spec["baseline_order"]]
    order.extend((task,arm) for task,arms in zip(spec["tasks"],spec["remaining_order"]) for arm in arms)
    return [{"sequence":i+1,"task":task,"arm":arm,"status":"NOT_EXECUTED","stages":[],
             "checks":[],"correction":{"attempted":False},"total_seconds":None,
             "total_cost_usd":None} for i,(task,arm) in enumerate(order)]


def identities():
    frozen=json.loads((HERE/"FREEZE.json").read_text())
    for name,digest in frozen["sha256"].items():
        if host.sha256((ROOT/name).read_bytes())!=digest:
            raise ValueError("Frozen input drift: "+name)
    for name,path in (("codex",Path(CODEX)),("python",Path(PYTHON))):
        if host.sha256(path.read_bytes())!=frozen["runtime_sha256"][name]:
            raise ValueError("Frozen runtime drift: "+name)
    runner.validate_models(json.loads((HERE/"model-catalog.json").read_text()))
    return {"freeze_sha256":host.sha256((HERE/"FREEZE.json").read_bytes())}


runner.identities = identities


def prepare():
    identities()
    STORE.mkdir(mode=0o700,parents=True,exist_ok=False)
    began=time.monotonic()
    result={"study":protocol()["study_id"],"status":"PREPARING","declared_at":existing.now(),
            "assignments":ledger(),"model_dispatches":0}
    write_record(STORE/"results.json",result)
    try:
        manifest={"identities":identities(),"protocol":protocol(),"assignments":[]}
        frozen=json.loads((HERE/"FREEZE.json").read_text())
        for row in result["assignments"]:
            folder=STORE/"assignments"/f"{row['sequence']:02d}-{row['task']}-{row['arm']}"
            product=runner.initialize(row["task"],folder/"seed")
            row["seed"]=str(product)
            identity={"source_sha256":host.sha256((product.parent/"source.md").read_bytes()),
                      "seed_tree":host.git(product,"rev-parse","HEAD^{tree}")}
            if identity!=frozen["tasks"][row["task"]]: raise ValueError("Frozen seed drift")
            manifest["assignments"].append({**identity,"checks":checks(row["task"])})
        write_record(STORE/"manifest.json",manifest)
        controls=grader.controls(STORE/"offline-controls")
        if not controls["all_matched"]: raise ValueError("Offline oracle/probe controls do not match")
        result["status"]="PREPARED_NOT_QUALIFIED"
    except Exception as error:
        result.update(status="STOPPED",blocker=str(error)); raise
    finally:
        result["preparation_seconds"]=time.monotonic()-began
        result["metrics"]=report.summarize(result["assignments"])
        write_record(STORE/"results.json",result)


def verify():
    manifest=json.loads((STORE/"manifest.json").read_text())
    if manifest["identities"]!=identities() or manifest["protocol"]!=protocol():
        raise ValueError("Frozen declaration drift")
    return manifest


def qualify():
    verify()
    result=json.loads((STORE/"results.json").read_text())
    if result["status"]!="PREPARED_NOT_QUALIFIED": raise ValueError("No qualification retry/resume")
    began=time.monotonic()
    try:
        spec=protocol()
        if [platform.system(),platform.machine(),platform.mac_ver()[0],platform.python_version()]!=spec["host"]["versions"]:
            raise ValueError("Frozen host unavailable")
        version=host.run_command([CODEX,"--version"],STORE)
        if not host.succeeded(version) or version["stdout"].strip()!=spec["host"]["codex"]:
            raise ValueError("Frozen CLI unavailable")
        if host.auth_status(host.run_command([CODEX,"login","status"],STORE))!="authenticated":
            raise ValueError("Existing native authentication unavailable")
        codex_catalog.readback(CODEX,HERE/"model-catalog.json",spec["models"],STORE)
        probe=STORE/"qualification"; probe.mkdir()
        product=runner.initialize(spec["tasks"][0],probe/"seed")
        (product.parent/"accepted-input.md").write_text("Entire original request controls.\n")
        # Test denial of this fresh oracle/control source and all study results.
        fresh_boundary=binding.bound_module(existing.infrastructure,corpus=corpus,grader=grader,STORE=STORE)
        fresh_boundary.read_protocol=lambda: {"model":spec["models"]["luna"]}
        (probe/"sibling.txt").write_text("Unavailable sibling assignment\n")
        worker=fresh_boundary.boundary(product.parent,probe/"worker",worker=True)
        reader=fresh_boundary.boundary(product.parent,probe/"reader")
        native=grader.controls(probe/"controls",trusted=False)
        if not native["all_matched"]: raise ValueError("Native oracle/probe controls do not match")
        control=json.loads((ROOT/"evaluation/results/issue32-qualified-stopped/results.json").read_text())["handoff_qualification"]
        previous_host.validate_handoff(control)
        # This reuses machinery qualification only, never inherited efficacy.
        write_record(probe/"same-thread.json",{"scope":"Reused staged native #32 handoff, zero new inference",
            "control":control,"model_dispatches":0})
        # Both delivery mechanisms must pass the same probes and reject the same seed.
        comparisons=[]
        for task in spec["tasks"]:
            for variant in ("reference","defective"):
                folder=probe/"delivery"/task/variant
                candidate=runner.initialize(task,folder/"seed",variant)
                source=corpus.REQUESTS[task]
                plain=ordinary(candidate,source,checks(task),folder/"B",60)
                protected=runner.checked(candidate,source,checks(task),folder/"C",60)
                eligible_b=ordinary_allowed(plain,folder/"B",checks(task),candidate)
                eligible_c=runner.correction_allowed(protected,folder/"C",checks(task),candidate)
                if plain["status"]!=protected["status"] or eligible_b!=eligible_c or eligible_b!=(variant=="defective"):
                    raise ValueError("B/C probes or correction opportunities differ: "+task)
                comparisons.append({"task":task,"variant":variant,"B":plain["status"],
                                    "C":protected["status"],"B_eligible":eligible_b,"C_eligible":eligible_c})
        write_record(probe/"qualification.json",{"model_dispatches":0,"worker":worker,
            "reader":reader,"delivery":comparisons,"native_controls_matched":True})
        result["status"]="QUALIFIED_NOT_DISPATCHED"
    except Exception as error:
        result.update(status="STOPPED",blocker=str(error)); raise
    finally:
        result["qualification_seconds"]=time.monotonic()-began
        write_record(STORE/"results.json",result)


def ordinary(product,source,selected,directory,seconds):
    """Same argv/native protection as C; no Proofline check, feedback or policy."""
    began=time.monotonic()
    directory.mkdir(parents=True,exist_ok=False)
    inputs=directory/"inputs"; inputs.mkdir()
    selection=snapshots.capture_worktree(product,inputs/"product")
    (inputs/"source.md").write_text(source)
    (inputs/"checks.json").write_text(json.dumps(selected))
    snapshot=host.snapshot(inputs)
    private=directory/"private"; private.mkdir()
    record={"status":"CHECKS UNAVAILABLE","checks":selected,"observations":[],
        "candidate_tree":selection["candidate_tree"],"source_sha256":host.sha256(source.encode()),
        "snapshot":snapshot["sha256"],"model_dispatches":0,"delivery":"ordinary protected commands"}
    for index,argv in enumerate(selected):
        scratch=directory/f"check-{index}"; scratch.mkdir(); receipts=[]
        entry={"argv":argv,"status":"UNAVAILABLE","receipts":receipts}
        try:
            remaining=seconds-(time.monotonic()-began)
            if remaining<=0: raise OSError("Check budget exhausted")
            completed=oracle_runner(CODEX,inputs,private,receipts)(
                [PYTHON,"-I","-B","-c",ORDINARY_LAUNCH,str(inputs/"product"),json.dumps(argv)],
                cwd=scratch,timeout=min(protocol()["limits"]["check_seconds"],remaining))
            if "sandbox-exec: sandbox_apply:" in completed.stderr: raise OSError("Native sandbox unavailable")
            entry.update(returncode=completed.returncode,status="PASSED" if completed.returncode==0 else "FAILED")
        except OSError as error:
            entry["error"]=str(error)
        record["observations"].append(entry)
        write_record(directory/f"receipt-{index}.json",receipts)
        entry["receipt_sha256"]=host.sha256((directory/f"receipt-{index}.json").read_bytes())
    if host.snapshot(inputs)!=snapshot: raise ValueError("Ordinary frozen inputs changed")
    statuses=[o["status"] for o in record["observations"]]
    record["status"]="CHECKS UNAVAILABLE" if "UNAVAILABLE" in statuses else "CHECKS FAILED" if "FAILED" in statuses else "CHECKS PASSED"
    record["elapsed_seconds"]=time.monotonic()-began
    write_record(directory/"report.json",record)
    return record


def ordinary_allowed(record,directory,selected,candidate):
    if (record["status"]!="CHECKS FAILED" or record["checks"]!=selected or
            record["candidate_tree"]!=host.git(candidate,"rev-parse","HEAD^{tree}") or
            json.loads((directory/"report.json").read_text())!=record or
            record["source_sha256"]!=host.sha256((directory/"inputs/source.md").read_bytes()) or
            host.snapshot(directory/"inputs")["sha256"]!=record["snapshot"] or
            len(record["observations"])!=len(selected) or record["observations"][0]["status"]!="FAILED"):
        return False
    for index,entry in enumerate(record["observations"]):
        path=directory/f"receipt-{index}.json"
        if path.is_symlink() or host.sha256(path.read_bytes())!=entry["receipt_sha256"]:
            return False
        receipts=json.loads(path.read_text())
        if receipts!=entry["receipts"] or len(receipts)!=1 or entry["status"] not in ("PASSED","FAILED") or entry["argv"]!=selected[index]:
            return False
        native=receipts[0]
        expected=[PYTHON,"-I","-B","-c",ORDINARY_LAUNCH,str(directory/"inputs/product"),json.dumps(selected[index])]
        try:
            if json.loads(native["argv"][-1])!=expected: return False
        except (KeyError,TypeError,ValueError):
            return False
        if any(native.get(k) for k in ("error","timed_out","stdout_truncated","stderr_truncated")) or native["exit_code"]!=entry.get("returncode"):
            return False
        if entry["status"]=="FAILED":
            text=native["stdout"]+"\n"+native["stderr"]
            if entry["returncode"]<=0 or not re.search(r"(?m)^(?:E\s+)?AssertionError(?::|$)",text) or re.search(r"(?:ImportError|ModuleNotFoundError|FileNotFoundError|PermissionError|OSError|MemoryError|TimeoutError|SyntaxError|ConnectionError|ConnectionRefusedError|sandbox-exec):",text):
                return False
    return True


def approved():
    path=STORE/"approval.json"
    approval=json.loads(path.read_text()) if path.exists() else {}
    limits=protocol()["limits"]
    if (approval.get("freeze_sha256")!=identities()["freeze_sha256"] or
        approval.get("study_id")!=protocol()["study_id"] or
        approval.get("max_native_dispatches")!=limits["max_native_dispatches"] or
        approval.get("max_seconds")!=limits["max_campaign_seconds"] or
        not isinstance(approval.get("user_authorization"),str) or not approval["user_authorization"].strip()):
        raise ValueError("Fresh declaration-bound explicit live spending authorization required")
    return approval


def episode(row,frozen,folder,save):
    began=time.monotonic(); spec=protocol(); deadline=began+spec["limits"]["episode_seconds"]
    source=corpus.REQUESTS[row["task"]]; selected=frozen["checks"]
    def allowance(cap):
        remaining=min(cap,deadline-time.monotonic())
        if remaining<=0: raise ValueError("Total assignment budget exhausted")
        return remaining
    def dispatch():
        slots=row.get("reserved_native_dispatches",0)
        if slots>={"A":1,"B":2,"C":2,"D":3}[row["arm"]]:
            raise ValueError("Predeclared native dispatch slots exhausted")
        row["reserved_native_dispatches"]=slots+1
        row["status"]="DISPATCHED"; save()
    def append(result):
        row["stages"].extend(result["stages"]); save()
        if not result["stages"] or any(s["status"]!="OBSERVED" for s in result["stages"]):
            raise ValueError("Native implementer unavailable")
    def check(candidate,directory):
        function=ordinary if row["arm"]=="B" else runner.checked
        value=function(candidate,source,selected,directory,allowance(90))
        row["checks"].append({"path":str(directory/"report.json"),"status":value["status"],"elapsed_seconds":value["elapsed_seconds"]})
        if value["status"] not in ("CHECKS PASSED","CHECKS FAILED"): raise ValueError("Public checks unavailable")
        row["repository_tests_passed"]=value["observations"][1]["status"]=="PASSED"
        save(); return value
    try:
        verify()
        seed=Path(row["seed"])
        if host.git(seed,"status","--porcelain") or host.git(seed,"rev-parse","HEAD^{tree}")!=frozen["seed_tree"] or host.sha256((seed.parent/"source.md").read_bytes())!=frozen["source_sha256"]:
            raise ValueError("Frozen initial repository/request changed")
        # Public probes are absent from every initial worker's readable inputs.
        result=runner.implement(source,seed,folder/"coding","luna",
            allowance(spec["limits"]["ordinary_initial_seconds"] if row["arm"]=="A" else spec["limits"]["initial_seconds"]),[],
            persist=row["arm"]!="A",on_dispatch=dispatch,deadline=deadline-90)
        append(result)
        candidate=Path(result["candidate"]); handoff=result["accepted"]
        row["initial_candidate"]={"path":str(candidate),"tree":host.git(candidate,"rev-parse","HEAD^{tree}")}
        check_record=None; eligible=False
        if row["arm"]!="A":
            check_directory=folder/"initial-check"
            check_record=check(candidate,check_directory)
            gate=ordinary_allowed if row["arm"]=="B" else runner.correction_allowed
            eligible=gate(check_record,check_directory,selected,candidate)
            handoff=handoff and check_record["status"]=="CHECKS PASSED"
        row["initial_grade"]=grader.grade(candidate,row["task"],folder/"initial-grade",seconds=allowance(60))
        if not row["initial_grade"]["available"]: raise ValueError("Initial independent oracle unavailable")
        if eligible:
            original=result["stages"][0]; live.reconcile_worker(folder/"coding/implementation/private")
            if live.read_events(original["receipt"])["thread_id"]!=original["thread_id"]: raise ValueError("Original implementer thread drift")
            advice=[]
            if row["arm"]=="D":
                dispatch()
                diagnosis=runner.advisory("verification",source,candidate,folder/"verification",allowance(120),selected,check_record)
                row["stages"].append(diagnosis); save()
                if diagnosis["status"]!="OBSERVED": raise ValueError("Selective Sol unavailable")
                if runner.review_valid(diagnosis,source,len(selected)):
                    advice=diagnosis["report"]["findings"]
            def correction_dispatch():
                if not gate(check_record,check_directory,selected,candidate): raise ValueError("Public assertion evidence drift")
                if row["correction"]["attempted"]: raise ValueError("Only one correction allowed")
                row["correction"]={"attempted":True,"thread_id":original["thread_id"],
                    "trigger":"Prevalidated public assertion on exact frozen candidate"}
                dispatch()
            guidance={"observations":check_record["observations"],"Sol_advice_not_proof":advice}
            if row["arm"]!="B": guidance["feedback"]=check_record["feedback"]
            corrected=runner.implement(source,candidate,folder/"correction","luna",allowance(180),selected,
                session_id=original["thread_id"],on_dispatch=correction_dispatch,deadline=deadline-150,guidance=guidance)
            append(corrected); candidate=Path(corrected["candidate"])
            final_check=check(candidate,folder/"final-check")
            handoff=corrected["accepted"] and final_check["status"]=="CHECKS PASSED"
            row["final_grade"]=grader.grade(candidate,row["task"],folder/"final-grade",seconds=allowance(60))
        else:
            row["final_grade"]=row["initial_grade"]
        if not row["final_grade"]["available"]: raise ValueError("Final independent oracle unavailable")
        row["final_candidate"]={"path":str(candidate),"tree":host.git(candidate,"rev-parse","HEAD^{tree}")}
        row["status"]=existing.report.outcome(handoff,row["final_grade"]["correct"],True)
        verify()
        if time.monotonic()>deadline: raise ValueError("Total assignment budget exhausted")
    except BaseException as error:
        row.update(status="UNAVAILABLE",unavailable_reason=str(error) or type(error).__name__); raise
    finally:
        runner.recover_stages(folder,row)
        row["total_seconds"]=time.monotonic()-began
        row["grading_seconds"]=sum(row.get(key,{}).get("elapsed_seconds",0) for key in
            (("initial_grade","final_grade") if row["correction"]["attempted"] else ("initial_grade",)))
        row["probe_seconds"]=sum(c["elapsed_seconds"] for c in row["checks"])
        row["operator_candidate_edits"]=0; row["extra_worker_messages"]=0
        write_record(folder/"result.json",row); save()


def execute():
    approved(); manifest=verify()
    result=json.loads((STORE/"results.json").read_text())
    if result["status"]!="QUALIFIED_NOT_DISPATCHED": raise ValueError("No replay/resume of live study")
    began=time.monotonic(); result["status"]="EXECUTING"
    def save():
        result["model_dispatches"]=sum(len(r["stages"]) for r in result["assignments"])
        result["reserved_native_dispatches"]=sum(r.get("reserved_native_dispatches",0) for r in result["assignments"])
        write_record(STORE/"results.json",result)
    save()
    try:
        for index,(row,frozen) in enumerate(zip(result["assignments"],manifest["assignments"])):
            if index==6:
                result["spending_gate"]=report.baseline_gate(result["assignments"]); save()
                if not result["spending_gate"]["continue"]:
                    result["status"]="EARLY_STOP_CORRECTNESS_CEILING"; break
            if time.monotonic()-began>=protocol()["limits"]["max_campaign_seconds"]:
                raise ValueError("Campaign budget exhausted")
            episode(row,frozen,Path(row["seed"]).parent.parent,save)
        else: result["status"]="COMPLETED"
    except BaseException as error:
        result.update(status="STOPPED_INCOMPLETE",blocker=str(error) or type(error).__name__); raise
    finally:
        result["campaign_seconds"]=time.monotonic()-began
        result["metrics"]=normalized.normalize(result)["metrics"]
        save()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","qualify","execute","report"))
    args=parser.parse_args(argv)
    if args.action=="report":
        result=json.loads((STORE/"results.json").read_text())
        print(json.dumps(normalized.normalize(result),indent=2)); return
    {"prepare":prepare,"qualify":qualify,"execute":execute}[args.action]()


if __name__=="__main__":
    main()
