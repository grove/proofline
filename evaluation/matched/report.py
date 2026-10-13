"""All-assigned accounting and descriptive paired uncertainty, without AI judging."""
from collections import Counter
from itertools import product

ARMS = ("ordinary", "proofline", "intentline", "combined")


def outcome(handoff, correct, available=True):
    if not available or correct is None:
        return "UNAVAILABLE"
    if correct:
        return "CORRECT_DELIVERY" if handoff else "CORRECT_BUT_BLOCKED"
    return "FALSE_ACCEPTANCE" if handoff else "INCORRECT_NO_HANDOFF"


def summarize(rows):
    result = {"assigned": len(rows), "executed": sum(r["status"] != "NOT_EXECUTED" for r in rows), "arms": {}}
    for arm in ARMS:
        assigned = [r for r in rows if r["arm"] == arm]
        observed = [r for r in assigned if r["status"] != "NOT_EXECUTED"]
        count = Counter(r["status"] for r in assigned)
        usage = [r.get("usage") for r in observed]
        successes = count["CORRECT_DELIVERY"]
        measured = [r.get("workflow_seconds") for r in observed]
        seconds = sum(measured) if measured and all(v is not None for v in measured) else None
        known_tokens = {k: sum((u or {}).get(k, 0) for u in usage) for k in ("input_tokens", "cached_input_tokens", "output_tokens")} if observed else None
        result["arms"][arm] = {
            "assigned": len(assigned), "executed": len(observed), "outcomes": dict(count),
            "independently_correct_deliveries": successes if observed else None,
            "observed_delivery_rate": successes / len(assigned) if observed else None,
            "workflow_seconds": seconds, "seconds_per_correct_delivery": seconds / successes if seconds is not None and successes else None,
            "known_tokens": known_tokens,
            "tokens_per_correct_delivery": (known_tokens["input_tokens"] + known_tokens["output_tokens"]) / successes if successes and all(u is not None for u in usage) else None,
            "unknown_usage_attempts": sum(u is None for u in usage),
            "native_model_dispatches": sum(r.get("model_dispatches", 0) for r in assigned),
            "observed_agent_tool_executions": sum(r.get("tool_executions", 0) for r in observed),
            "tool_count_unknown_attempts": sum(r.get("tool_executions") is None for r in observed),
            "material_green_test_omissions": sum(bool(r.get("grade", {}).get("failures")) and r.get("grade", {}).get("repository_tests_passed") is True for r in observed) if any(r.get("grade", {}).get("available") for r in observed) else None,
            "retained_stale_test_expectations": sum(r.get("grade", {}).get("stale_test_expectation_retained", False) for r in observed) if any(r.get("grade", {}).get("available") for r in observed) else None,
            "independent_grading_seconds": sum(r.get("grade", {}).get("elapsed_seconds", 0) for r in observed) if any("grade" in r for r in observed) else None,
            "selected_check_processes": sum(len(r.get("feedback", {}).get("checks", [])) for r in observed),
            "operator_candidate_edits": sum(r.get("operator_candidate_edits", 0) for r in observed) if observed else None,
            "extra_worker_messages": sum(r.get("extra_worker_messages", 0) for r in observed) if observed else None,
        }
    complete = len(rows) == 16 and all(r["status"] not in ("NOT_EXECUTED", "UNAVAILABLE") for r in rows)
    result.update(empirical_acceptance="OBSERVED_FINITE_STUDY" if complete else "INCOMPLETE",
                  paired_effects=None, mandatory_actions_decision="INCONCLUSIVE" if not complete else "NO_NEW_MANDATORY_ACTION",
                  human_active_seconds=None, initiating_agent_tokens=None, dollars=None, provider_internal_calls=None,
                  other_host_tool_executions=None)
    if complete:
        by_task = {}
        for row in rows:
            by_task.setdefault(row["task"], {})[row["arm"]] = int(row["status"] == "CORRECT_DELIVERY")
        contrasts = {"proofline_minus_ordinary": {"proofline": 1, "ordinary": -1},
                     "intentline_minus_ordinary": {"intentline": 1, "ordinary": -1},
                     "combined_minus_ordinary": {"combined": 1, "ordinary": -1},
                     "combined_minus_intentline": {"combined": 1, "intentline": -1},
                     "combined_minus_proofline": {"combined": 1, "proofline": -1},
                     "interaction": {"combined": 1, "intentline": -1, "proofline": -1, "ordinary": 1}}
        effects = {}
        for label, weights in contrasts.items():
            differences = [sum(v[a] * w for a, w in weights.items()) for v in by_task.values()]
            bootstrap = sorted(100 * sum(sample) / 4 for sample in product(differences, repeat=4))
            effects[label] = {"percentage_points": 100 * sum(differences) / 4,
                              "task_bootstrap_95_percent_descriptive_interval": [bootstrap[6], bootstrap[249]]}
        result["paired_effects"] = effects
    return result
