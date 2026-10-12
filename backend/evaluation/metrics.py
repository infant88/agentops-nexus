from typing import Any, Dict, List

def calculate_benchmark_metrics(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_cases = len(case_results)
    if total_cases == 0:
        return {}

    successful_tasks = sum(1 for c in case_results if c.get("task_success", False))
    task_success_rate = round(successful_tasks / total_cases * 100, 2)

    # Tool selection accuracy
    tool_decisions = [c.get("tool_accuracy", 1.0) for c in case_results if "tool_accuracy" in c]
    avg_tool_accuracy = round(sum(tool_decisions) / len(tool_decisions) * 100, 2) if tool_decisions else 100.0

    # Latencies
    latencies = [c.get("latency_ms", 0.0) for c in case_results]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    sorted_latencies = sorted(latencies)
    p95_index = int(0.95 * len(sorted_latencies)) - 1
    p95_latency = round(sorted_latencies[max(0, p95_index)], 2) if sorted_latencies else 0.0

    # Token usage & Cost
    total_tokens_in = sum(c.get("tokens_in", 0) for c in case_results)
    total_tokens_out = sum(c.get("tokens_out", 0) for c in case_results)
    total_tokens = total_tokens_in + total_tokens_out
    total_cost_usd = round(sum(c.get("cost_usd", 0.0) for c in case_results), 5)

    # Retry recovery
    transient_cases = [c for c in case_results if c.get("is_transient_test", False)]
    recovered_transient = sum(1 for c in transient_cases if c.get("recovered_via_retry", False))
    total_retry_attempts = sum(c.get("retry_attempts", 0) for c in transient_cases)
    retry_recovery_rate = (
        round(recovered_transient / len(transient_cases) * 100, 2)
        if transient_cases else 100.0
    )

    # Approval compliance
    sensitive_cases = [c for c in case_results if c.get("requires_approval_test", False)]
    correctly_gated = sum(1 for c in sensitive_cases if c.get("approval_correctly_gated", False))
    approval_compliance_rate = (
        round(correctly_gated / len(sensitive_cases) * 100, 2)
        if sensitive_cases else 100.0
    )

    # Category breakdown
    categories: Dict[str, Dict[str, Any]] = {}
    for c in case_results:
        cat = c.get("category", "other")
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0, "avg_latency_ms": 0.0}
        categories[cat]["total"] += 1
        if c.get("task_success", False):
            categories[cat]["success"] += 1

    for cat, data in categories.items():
        data["success_rate"] = round(data["success"] / data["total"] * 100, 2)

    return {
        "total_cases": total_cases,
        "successful_tasks": successful_tasks,
        "task_success_rate": task_success_rate,
        "tool_selection_accuracy": avg_tool_accuracy,
        "latency": {
            "avg_ms": avg_latency,
            "min_ms": round(min(latencies), 2) if latencies else 0.0,
            "max_ms": round(max(latencies), 2) if latencies else 0.0,
            "p95_ms": p95_latency
        },
        "tokens": {
            "input": total_tokens_in,
            "output": total_tokens_out,
            "total": total_tokens,
            "avg_per_task": round(total_tokens / total_cases, 1),
            "is_estimated": True
        },
        "cost": {
            "total_usd": total_cost_usd,
            "avg_per_task_usd": round(total_cost_usd / total_cases, 6),
            "is_estimated": True
        },
        "retry_recovery_rate": retry_recovery_rate,
        "total_retry_attempts_recorded": total_retry_attempts,
        "approval_compliance_rate": approval_compliance_rate,
        "category_breakdown": categories,
        "methodology": {
            "empirical_metrics": [
                "task_success_rate",
                "tool_selection_accuracy",
                "approval_compliance_rate",
                "retry_recovery_rate",
                "latency"
            ],
            "heuristic_estimates": [
                "tokens",
                "cost"
            ],
            "estimation_notes": "Token counts and costs are offline heuristic approximations. Latencies, tool accuracy, retries, and approval gates are directly instrumented measurements."
        }
    }

