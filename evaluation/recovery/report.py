"""All assigned slots, separate initial/final grades, and honest paired costs."""
from collections import Counter
import math

ARMS = ("A","B","C","D")
TOKENS = ("input_tokens","cached_input_tokens","output_tokens")


def total(values):
    return sum(values) if all(v is not None for v in values) else None


def baseline_gate(rows):
    baseline = [r for r in rows if r["arm"]=="A"]
    if len(baseline)!=6 or any(not r.get("initial_grade",{}).get("available") or
            type(r.get("initial_grade",{}).get("correct")) is not bool for r in baseline):
        raise ValueError("Six available independent baseline grades are required")
    defects = sum(r["initial_grade"]["correct"] is False for r in baseline)
    return {"defective":defects,"minimum_defects":2,"continue":defects>=2,
            "conditional_inference":"All B/C/D cells execute only if at least two A candidates are defective."}


def summarize(rows):
    from evaluation.recovery import corpus
    if len(rows)!=24 or {(r["task"],r["arm"]) for r in rows}!={(t,a) for t in corpus.REQUESTS for a in ARMS}:
        raise ValueError("All 24 unique assigned slots are required")
    metrics = {"assigned":24,"executed":sum(bool(r.get("stages")) for r in rows),"arms":{},
        "paired":{}, "billing_usd":None,"human_active_seconds":None,
        "authoring_tokens":None,"authoring_cost_usd":None,
        "uncertainty":"Six fixed synthetic repositories, one repetition, conditional on the baseline gate. Exact paired sign tests are descriptive; no population reliability or monetary savings claim.",
        "recommendations":{"Proofline":"INCONCLUSIVE","selective_Sol":"INCONCLUSIVE"}}
    for arm in ARMS:
        assigned=[r for r in rows if r["arm"]==arm]
        observed=[r for r in assigned if r["status"]!="NOT_EXECUTED"]
        successes=sum(r["status"]=="CORRECT_DELIVERY" for r in assigned)
        elapsed=total([r.get("total_seconds") for r in observed]) if observed else None
        stages=[s for r in observed for s in r.get("stages",[])]
        models={}
        for model in ("gpt-6-luna","gpt-6.1-sol"):
            used=[s for s in stages if s["model"]==model]
            tokens={key:total([(s.get("usage") or {}).get(key) for s in used]) for key in TOKENS}
            tokens["uncached_input_tokens"]=(tokens["input_tokens"]-tokens["cached_input_tokens"]
                if tokens["input_tokens"] is not None and tokens["cached_input_tokens"] is not None else None)
            models[model]={"native_turns":len(used),"tokens":tokens,
                "seconds":total([s.get("elapsed_seconds") for s in used]),
                "tool_executions":total([s.get("tool_executions") for s in used]),
                "unknown_usage_stages":sum(s.get("usage") is None for s in used)}
        metrics["arms"][arm]={"assigned":6,"outcomes":dict(Counter(r["status"] for r in assigned)),
            "correct_deliveries":successes,"rate_over_all_assigned":successes/6,
            "initial_correct":sum(r.get("initial_grade",{}).get("correct") is True for r in observed),
            "final_correct":sum(r.get("final_grade",{}).get("correct") is True for r in observed),
            "recovered":sum(r.get("initial_grade",{}).get("correct") is False and r.get("final_grade",{}).get("correct") is True for r in observed),
            "persistent_defects":sum(r.get("final_grade",{}).get("correct") is False for r in observed),
            "corrections":sum(r.get("correction",{}).get("attempted",False) for r in observed),
            "false_accept":sum(r["status"]=="FALSE_ACCEPTANCE" for r in observed),
            "false_block":sum(r["status"]=="CORRECT_BUT_BLOCKED" for r in observed),
            "green_probe_omissions":sum(r.get("initial_grade",{}).get("correct") is False and bool(r.get("checks",[])) and r["checks"][0]["status"]=="CHECKS PASSED" for r in observed),
            "green_repository_test_omissions":sum(r.get("initial_grade",{}).get("correct") is False and r.get("initial_grade",{}).get("repository_tests_passed") is True for r in observed),
            "unavailable_checks":sum(c["status"] not in ("CHECKS PASSED","CHECKS FAILED") for r in observed for c in r.get("checks",[])),
            "seconds":elapsed,"seconds_per_correct_delivery":elapsed/successes if elapsed is not None and successes else None,
            "probe_seconds":total([r.get("probe_seconds") for r in observed]) if observed else None,
            "grading_seconds":total([r.get("grading_seconds") for r in observed]) if observed else None,
            "cost_usd_per_correct_delivery":None,"models":models}
    complete=all(r["status"] not in ("NOT_EXECUTED","DISPATCHED","UNAVAILABLE") for r in rows)
    if complete:
        tasks={t:{r["arm"]:r for r in rows if r["task"]==t} for t in corpus.REQUESTS}
        for before,after in (("A","B"),("B","C"),("C","D")):
            changes=[int(v[after]["status"]=="CORRECT_DELIVERY")-int(v[before]["status"]=="CORRECT_DELIVERY") for v in tasks.values()]
            positive,negative=changes.count(1),changes.count(-1); n=positive+negative
            metrics["paired"][before+"_"+after]={"percentage_points":100*sum(changes)/6,
                "improved":positive,"worsened":negative,"tied":changes.count(0),
                "exact_two_sided_sign_p":min(1,2*sum(math.comb(n,k) for k in range(min(positive,negative)+1))/2**n) if n else 1,
                "mean_seconds_difference":sum(v[after]["total_seconds"]-v[before]["total_seconds"] for v in tasks.values())/6}
        for name,contrast in (("Proofline","B_C"),("selective_Sol","C_D")):
            metrics["recommendations"][name]=("KEEP optional: finite paired delivery gain, dollar value unknown"
                if metrics["paired"][contrast]["percentage_points"]>0 else
                "SIMPLIFY: no finite paired delivery gain; retain optional pending broader evidence")
    return metrics
