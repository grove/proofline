"""All twenty slots, stage/model accounting and descriptive matched contrasts."""
from collections import Counter
from itertools import product

from evaluation.matched.report import outcome
from evaluation.sol_luna import corpus

ARMS = ("luna", "plan", "verify", "hybrid", "sol")
TOKENS = ("input_tokens", "cached_input_tokens", "output_tokens")
CONTRASTS = {
    "planning_without_verification": {"plan": 1, "luna": -1},
    "planning_with_verification": {"hybrid": 1, "verify": -1},
    "verification_without_planning": {"verify": 1, "luna": -1},
    "verification_with_planning": {"hybrid": 1, "plan": -1},
    "interaction": {"hybrid": 1, "verify": -1, "plan": -1, "luna": 1},
    "hybrid_vs_sol": {"hybrid": 1, "sol": -1},
    "luna_vs_sol": {"luna": 1, "sol": -1},
}


def total(values):
    return sum(values) if values and all(v is not None for v in values) else None


def summarize(rows):
    expected = {(t, a) for t in corpus.REQUESTS for a in ARMS}
    if len(rows) != 20 or {(r["task"], r["arm"]) for r in rows} != expected:
        raise ValueError("Report requires every unique predeclared task/arm slot")
    complete = all(r["status"] not in ("NOT_EXECUTED", "DISPATCHED", "UNAVAILABLE") for r in rows)
    result = {"assigned": 20, "executed": sum(bool(r.get("stages")) for r in rows),
              "empirical_acceptance": "OBSERVED_FINITE_STUDY" if complete else "INCOMPLETE",
              "arms": {}, "paired_effects": None, "paired_seconds": None,
              "provider_internal_model_calls": None, "human_active_seconds": None,
              "authoring_tokens": None, "authoring_dollars": None,
              "uncertainty": "Four fixed tasks, one repetition. Bootstrap intervals describe these tasks only; zero variation cannot rule out unseen-task effects.",
              "identification": "Verification is a package of Proofline checks, Sol review and eligible correction; their separate causal effects are not identified by these five arms."}
    for arm in ARMS:
        assigned = [r for r in rows if r["arm"] == arm]
        observed = [r for r in assigned if r["status"] != "NOT_EXECUTED"]
        stages = [s for r in observed for s in r.get("stages", [])]
        successes = sum(r["status"] == "CORRECT_DELIVERY" for r in assigned)
        seconds = total([r.get("total_seconds") for r in observed])
        dollars = total([r.get("total_cost_usd") for r in observed])
        models = {}
        for model in ("gpt-6-luna", "gpt-6.1-sol"):
            used = [s for s in stages if s["model"] == model]
            models[model] = {"native_dispatches": len(used),
                "tokens": {k: total([(s.get("usage") or {}).get(k) for s in used]) if used else 0 for k in TOKENS},
                "unknown_usage_stages": sum(s.get("usage") is None for s in used),
                "seconds": total([s.get("elapsed_seconds") for s in used]) if used else 0,
                "tool_executions": total([s.get("tool_executions") for s in used]) if used else 0,
                "cost_usd": total([s.get("cost_usd") for s in used]) if used else 0}
            models[model]["tokens_per_correct_delivery"] = {k: v / successes if v is not None and successes else None
                for k,v in models[model]["tokens"].items()}
        result["arms"][arm] = {
            "assigned": 4, "outcomes": dict(Counter(r["status"] for r in assigned)),
            "independently_correct_deliveries": successes,
            "delivery_rate_over_all_assigned": successes / 4 if observed else None,
            "initial_correct": sum(r.get("initial_grade", {}).get("correct") is True for r in observed),
            "corrections": sum(r.get("correction", {}).get("attempted", False) for r in observed),
            "correction_improvements": sum(r.get("initial_grade", {}).get("correct") is False and r.get("final_grade", {}).get("correct") is True for r in observed),
            "correction_regressions": sum(r.get("initial_grade", {}).get("correct") is True and r.get("final_grade", {}).get("correct") is False for r in observed),
            "total_seconds": seconds, "workflow_seconds": total([r.get("workflow_seconds") for r in observed]),
            "grading_seconds": total([r.get("grading_seconds") for r in observed]),
            "total_cost_usd": dollars, "unknown_cost_assignments": sum(r.get("total_cost_usd") is None for r in observed),
            "cost_per_correct_delivery": {"usd": dollars / successes if dollars is not None and successes else None,
                "seconds": seconds / successes if seconds is not None and successes else None},
            "models": models,
            "controller_processes": total([r.get("controller_processes") for r in observed]),
            "green_test_omissions": sum(r.get("initial_grade", {}).get("correct") is False and r.get("initial_grade", {}).get("repository_tests_passed") is True for r in observed),
            "unknown_checks": sum(c.get("status") not in ("CHECKS PASSED", "CHECKS FAILED") for r in observed for c in r.get("checks", [])),
            "advisory_failures": sum(r.get("plan_status") == "MISSING_OR_INVALID" or r.get("review_status") == "MISSING_OR_INVALID" for r in observed),
        }
    if complete:
        by_task = {t: {r["arm"]: r for r in rows if r["task"] == t} for t in corpus.REQUESTS}
        result["paired_effects"] = {}
        result["paired_seconds"] = {}
        for name, weights in CONTRASTS.items():
            effects = {}
            for phase in ("initial", "final_delivery"):
                values = [sum(w * (v[a].get("initial_grade", {}).get("correct") is True if phase == "initial" else v[a]["status"] == "CORRECT_DELIVERY") for a, w in weights.items()) for v in by_task.values()]
                samples = sorted(100 * sum(s) / 4 for s in product(values, repeat=4))
                effects[phase] = {"percentage_points": 100 * sum(values) / 4,
                    "task_bootstrap_95_percent_descriptive_interval": [samples[6], samples[249]]}
            result["paired_effects"][name] = effects
            values = [sum(w * v[a]["total_seconds"] for a,w in weights.items()) for v in by_task.values()]
            result["paired_seconds"][name] = sum(values) / 4
    ceiling = complete and all(r.get("initial_grade", {}).get("correct") is True for r in rows)
    result["ceiling_effect"] = ceiling
    result["cost_effectiveness"] = "INCONCLUSIVE" if not complete or any(a["total_cost_usd"] is None for a in result["arms"].values()) else "COMPARE_OBSERVED_COST_PER_CORRECT_DELIVERY"
    result["recommendations"] = {name: "INCONCLUSIVE" for name in ("Sol planning", "Sol verification", "Proofline checks", "bounded correction")}
    if ceiling:
        result["recommendations"] = {name: "SIMPLIFY: keep optional; no observed first-pass correctness gain" for name in result["recommendations"]}
    elif complete:
        for capability, contrast in (("Sol planning","planning_without_verification"), ("Sol verification","verification_without_planning")):
            gain = result["paired_effects"][contrast]["final_delivery"]["percentage_points"]
            result["recommendations"][capability] = ("KEEP optional: observed delivery gain; monetary value remains unknown" if gain>0 else
                "SIMPLIFY: no observed delivery gain; retain opt-in pending broader evidence")
    result["follow_up"] = ("Neither medium nor xhigh is justified by incomplete primary evidence. Each requires a separate frozen, authorized cohort." if not complete else
        "Consider medium only if high is reliable and total costs can be measured; consider xhigh only for observed high-effort defects or costly repairs. No follow-up is authorized here.")
    return result
