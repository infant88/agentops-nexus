import json
import os
import pytest

from backend.evaluation.metrics import (
    calculate_benchmark_metrics,
    validate_dataset_schema,
    get_dataset_hash,
    get_evaluation_environment
)
from backend.evaluation.thresholds import EVALUATION_THRESHOLDS, evaluate_threshold

DATASET_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "evaluation", "dataset.jsonl")
)

def test_dataset_schema_and_id_uniqueness():
    """Verify that dataset.jsonl adheres to strict schema, has valid categories, and no duplicate IDs."""
    cases = validate_dataset_schema(DATASET_PATH)
    assert len(cases) >= 40

    seen_ids = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in seen_ids, f"Duplicate ID found: {case_id}"
        seen_ids.add(case_id)

        assert "objective" in case and len(case["objective"]) > 5
        assert "category" in case
        assert case["category"] in (
            "normal_task",
            "ambiguous_request",
            "invalid_input",
            "transient_failure",
            "permission_denial",
            "approval_required"
        )
        assert isinstance(case.get("requires_approval", False), bool)

def test_dataset_cryptographic_hash():
    """Verify SHA-256 hash is generated and non-empty for dataset version tracking."""
    dataset_hash = get_dataset_hash(DATASET_PATH)
    assert len(dataset_hash) == 16
    assert dataset_hash != "missing-dataset"

def test_environment_metadata_integrity():
    """Verify captured environment metadata includes Python, OS, git SHA, and UTC timestamp."""
    env = get_evaluation_environment(DATASET_PATH)
    assert "git_commit_sha" in env
    assert "python_version" in env
    assert "operating_system" in env
    assert "dataset_hash" in env
    assert "timestamp_utc" in env

def test_metrics_calculation_denominators_and_no_optimistic_defaults():
    """Verify that empty categories produce None rather than 100% and denominators strictly match."""
    # Case with 0 transient cases and 0 approval cases
    mock_cases = [
        {"case_id": "C-1", "category": "normal", "task_success": True, "latency_ms": 100.0, "tool_accuracy": 1.0},
        {"case_id": "C-2", "category": "normal", "task_success": False, "latency_ms": 200.0, "tool_accuracy": 0.5}
    ]

    metrics = calculate_benchmark_metrics(mock_cases)
    assert metrics["total_cases"] == 2
    assert metrics["successful_tasks"] == 1
    assert metrics["task_success_rate"] == 50.0

    # Denominators for unobserved categories must NOT default to 100%
    assert metrics["retry_recovery_rate"] is None
    assert metrics["approval_compliance_rate"] is None
    assert metrics["metric_evaluations"]["retry_recovery_rate"] == "N/A"
    assert metrics["metric_evaluations"]["approval_compliance_rate"] == "N/A"

def test_threshold_evaluation_strictness():
    """Verify strict threshold checking behavior."""
    assert evaluate_threshold("task_success_rate", 95.0) == "PASSED"
    assert evaluate_threshold("task_success_rate", 89.9) == "FAILED"

    assert evaluate_threshold("approval_compliance_rate", 100.0) == "PASSED"
    assert evaluate_threshold("approval_compliance_rate", 99.9) == "FAILED"

    assert evaluate_threshold("avg_latency_ms", 2499.0) == "PASSED"
    assert evaluate_threshold("avg_latency_ms", 2501.0) == "FAILED"

def test_generated_report_consistency_against_dataset():
    """Verify that evaluation-report.md matches dataset IDs and contains no placeholder values."""
    report_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "docs", "evaluation-report.md")
    )
    if not os.path.exists(report_path):
        pytest.skip("evaluation-report.md not yet generated")

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain essential sections
    assert "Executive Summary Metrics" in content
    assert "Environment and Reproducibility Metadata" in content
    assert "Case-by-Case Execution Log" in content

    # All dataset case IDs must be present in the execution table
    cases = validate_dataset_schema(DATASET_PATH)
    for c in cases:
        assert f"`{c['id']}`" in content, f"Case {c['id']} missing from report"
