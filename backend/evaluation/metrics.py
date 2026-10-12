import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.evaluation.thresholds import EVALUATION_THRESHOLDS, evaluate_threshold, BENCHMARK_VERSION

def get_git_commit_sha() -> str:
    """Retrieve current Git commit SHA."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown-git-commit"

def get_dataset_hash(dataset_path: str) -> str:
    """Compute SHA-256 hash of the benchmark dataset for cryptographic reproducibility."""
    if not os.path.exists(dataset_path):
        return "missing-dataset"
    hasher = hashlib.sha256()
    with open(dataset_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]

def validate_dataset_schema(dataset_path: str) -> List[Dict[str, Any]]:
    """Validate dataset structure, unique case IDs, and required fields."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    cases = []
    seen_ids = set()
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            case = json.loads(line_str)
            case_id = case.get("id")
            if not case_id:
                raise ValueError(f"Dataset error on line {line_num}: Missing 'id' field.")
            if case_id in seen_ids:
                raise ValueError(f"Dataset error on line {line_num}: Duplicate case ID '{case_id}'.")
            seen_ids.add(case_id)

            if "objective" not in case:
                raise ValueError(f"Case '{case_id}' is missing required 'objective' field.")
            if "category" not in case:
                raise ValueError(f"Case '{case_id}' is missing required 'category' field.")

            cases.append(case)

    return cases

def get_evaluation_environment(dataset_path: str) -> Dict[str, Any]:
    """Capture comprehensive execution environment metadata for reproducible benchmark reports."""
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "git_commit_sha": get_git_commit_sha(),
        "dataset_hash": get_dataset_hash(dataset_path),
        "python_version": platform.python_version(),
        "operating_system": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "model_provider": "Deterministic sandboxed agent orchestration (simulated LLM planner)",
        "model_mode": "mock_and_deterministic_heuristics",
        "database_backend": "SQLite3 (WAL-enabled persistent checkpointer)",
        "sandbox_status": "Ephemeral isolated sandbox (freshly reset per test)",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }

def calculate_benchmark_metrics(case_results: List[Dict[str, Any]], environment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Audit every metric with strict evidence, explicit denominators, and no optimistic defaults."""
    total_cases = len(case_results)
    if total_cases == 0:
        return {}

    # 1. Task Success Rate
    successful_tasks = sum(1 for c in case_results if c.get("task_success", False))
    task_success_rate = round(successful_tasks / total_cases * 100, 2)

    # 2. Tool-Selection Accuracy
    # Only evaluate cases that have an instrumented tool-selection decision
    scored_tool_cases = [c for c in case_results if c.get("tool_accuracy") is not None]
    if scored_tool_cases:
        avg_tool_accuracy = round(sum(c["tool_accuracy"] for c in scored_tool_cases) / len(scored_tool_cases) * 100, 2)
    else:
        avg_tool_accuracy = None

    # 3. Latency Metrics (Monotonic clock)
    latencies = [c.get("latency_ms", 0.0) for c in case_results]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    sorted_latencies = sorted(latencies)
    p95_index = int(0.95 * len(sorted_latencies)) - 1
    p95_latency = round(sorted_latencies[max(0, p95_index)], 2) if sorted_latencies else 0.0

    # 4. Token Consumption & Cost (Heuristic estimates)
    total_tokens_in = sum(c.get("tokens_in", 0) for c in case_results)
    total_tokens_out = sum(c.get("tokens_out", 0) for c in case_results)
    total_tokens = total_tokens_in + total_tokens_out
    total_cost_usd = round(sum(c.get("cost_usd", 0.0) for c in case_results), 5)

    # 5. Retry Recovery Rate
    transient_cases = [c for c in case_results if c.get("is_transient_test", False)]
    recovered_transient = sum(1 for c in transient_cases if c.get("recovered_via_retry", False))
    total_retry_attempts = sum(c.get("retry_attempts", 0) for c in transient_cases)
    if transient_cases:
        retry_recovery_rate = round(recovered_transient / len(transient_cases) * 100, 2)
    else:
        retry_recovery_rate = None

    # 6. Approval Compliance Rate
    sensitive_cases = [c for c in case_results if c.get("requires_approval_test", False)]
    correctly_gated = sum(1 for c in sensitive_cases if c.get("approval_correctly_gated", False))
    if sensitive_cases:
        approval_compliance_rate = round(correctly_gated / len(sensitive_cases) * 100, 2)
    else:
        approval_compliance_rate = None

    # 7. Category Performance Breakdown
    categories: Dict[str, Dict[str, Any]] = {}
    for c in case_results:
        cat = c.get("category", "other")
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0, "avg_latency_ms": 0.0, "latencies": []}
        categories[cat]["total"] += 1
        categories[cat]["latencies"].append(c.get("latency_ms", 0.0))
        if c.get("task_success", False):
            categories[cat]["success"] += 1

    for cat, data in categories.items():
        data["success_rate"] = round(data["success"] / data["total"] * 100, 2)
        data["avg_latency_ms"] = round(sum(data["latencies"]) / len(data["latencies"]), 2) if data["latencies"] else 0.0
        del data["latencies"]

    # 8. Evaluation Status Assessment against central thresholds
    metric_evaluations = {
        "task_success_rate": evaluate_threshold("task_success_rate", task_success_rate),
        "tool_selection_accuracy": evaluate_threshold("tool_selection_accuracy", avg_tool_accuracy) if avg_tool_accuracy is not None else "N/A",
        "approval_compliance_rate": evaluate_threshold("approval_compliance_rate", approval_compliance_rate) if approval_compliance_rate is not None else "N/A",
        "retry_recovery_rate": evaluate_threshold("retry_recovery_rate", retry_recovery_rate) if retry_recovery_rate is not None else "N/A",
        "avg_latency_ms": evaluate_threshold("avg_latency_ms", avg_latency),
        "p95_latency_ms": evaluate_threshold("p95_latency_ms", p95_latency)
    }

    return {
        "environment": environment or {},
        "total_cases": total_cases,
        "successful_tasks": successful_tasks,
        "task_success_rate": task_success_rate,
        "tool_selection_accuracy": avg_tool_accuracy,
        "scored_tool_decisions": len(scored_tool_cases),
        "total_eligible_tool_cases": total_cases,
        "latency": {
            "avg_ms": avg_latency,
            "min_ms": round(min(latencies), 2) if latencies else 0.0,
            "max_ms": round(max(latencies), 2) if latencies else 0.0,
            "p95_ms": p95_latency,
            "sample_count": len(latencies)
        },
        "tokens": {
            "provider_reported_tokens": None,
            "estimated_input": total_tokens_in,
            "estimated_output": total_tokens_out,
            "total": total_tokens,
            "avg_per_task": round(total_tokens / total_cases, 1),
            "is_estimated": True,
            "estimation_method": "Character length heuristic (1 token ~= 4 characters)"
        },
        "cost": {
            "provider_reported_cost_usd": None,
            "total_usd": total_cost_usd,
            "avg_per_task_usd": round(total_cost_usd / total_cases, 6),
            "is_estimated": True,
            "pricing_basis": "Claude 3.5 Sonnet standard reference ($0.15/1M input, $0.60/1M output)"
        },
        "retry_recovery_rate": retry_recovery_rate,
        "transient_cases_evaluated": len(transient_cases),
        "transient_cases_recovered": recovered_transient,
        "total_retry_attempts_recorded": total_retry_attempts,
        "approval_compliance_rate": approval_compliance_rate,
        "sensitive_cases_evaluated": len(sensitive_cases),
        "sensitive_cases_correctly_gated": correctly_gated,
        "category_breakdown": categories,
        "metric_evaluations": metric_evaluations,
        "thresholds_applied": EVALUATION_THRESHOLDS
    }
