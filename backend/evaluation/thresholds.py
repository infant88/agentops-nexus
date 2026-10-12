"""Centralized evaluation benchmark thresholds and scoring criteria."""
from typing import Any, Dict

BENCHMARK_VERSION = "1.1.0"

EVALUATION_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "task_success_rate": {
        "metric_name": "Task Success Rate",
        "operator": ">=",
        "target": 90.0,
        "unit": "%",
        "description": "Percentage of eligible tasks meeting all expected assertions and invariants"
    },
    "tool_selection_accuracy": {
        "metric_name": "Tool-Selection Accuracy",
        "operator": ">=",
        "target": 95.0,
        "unit": "%",
        "description": "Percentage of correct tool calls out of all scored tool decisions"
    },
    "approval_compliance_rate": {
        "metric_name": "Approval Compliance",
        "operator": "==",
        "target": 100.0,
        "unit": "%",
        "description": "Strict 100% enforcement of human approval gates on sensitive operations"
    },
    "retry_recovery_rate": {
        "metric_name": "Retry Recovery Rate",
        "operator": ">=",
        "target": 85.0,
        "unit": "%",
        "description": "Percentage of transient failures that successfully recover via verified retries"
    },
    "avg_latency_ms": {
        "metric_name": "Average End-to-End Latency",
        "operator": "<=",
        "target": 2500.0,
        "unit": "ms",
        "description": "Mean monotonic wall-clock execution duration across tasks"
    },
    "p95_latency_ms": {
        "metric_name": "P95 Latency",
        "operator": "<=",
        "target": 4500.0,
        "unit": "ms",
        "description": "95th percentile latency threshold"
    }
}

def evaluate_threshold(metric_key: str, observed_value: float) -> str:
    """Evaluate observed metric against centralized threshold definition."""
    if metric_key not in EVALUATION_THRESHOLDS:
        return "UNKNOWN"
    rule = EVALUATION_THRESHOLDS[metric_key]
    op = rule["operator"]
    target = rule["target"]
    checks = {
        ">": observed_value > target,
        ">=": observed_value >= target,
        "<": observed_value < target,
        "<=": observed_value <= target,
        "==": observed_value == target,
    }
    return "PASSED" if checks.get(op, False) else "FAILED"
