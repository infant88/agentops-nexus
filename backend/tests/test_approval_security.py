import os
import pytest
from langgraph.types import Command
from backend.agent.graph import build_agent_graph
from backend.sandbox.setup_sandbox import setup_sandbox
from backend.mcp_server.server import default_mcp_server

@pytest.fixture(autouse=True)
def init_test_sandbox():
    setup_sandbox()

def test_pre_approval_disk_invariance():
    """Assert that sandbox files remain unaltered and mutation tools do not execute prior to reviewer resumption."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()
    assert "Missing / 100" in initial_content

    app = build_agent_graph()
    thread_id = "test-approval-pre-invariance"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-pre-approval",
        "objective": "Investigate failing tests in repository, identify root cause, propose fix, and request approval",
        "messages": [],
        "plan": [],
        "current_step_index": 0,
        "context_data": {},
        "patch_id": None,
        "proposed_patch": None,
        "approval_status": "pending",
        "reviewer_feedback": None,
        "retry_count": 0,
        "status": "pending"
    }

    # Execute graph until interrupt
    app.invoke(initial_state, config=config)

    # Verify graph is paused at interrupt
    snapshot = app.get_state(config)
    assert len(snapshot.tasks) > 0
    assert any(len(t.interrupts) > 0 for t in snapshot.tasks)

    # Invariant: file on disk is strictly unmodified prior to human approval
    with open(calc_path, "r", encoding="utf-8") as f:
        pre_resume_content = f.read()
    assert pre_resume_content == initial_content
    assert "Missing / 100" in pre_resume_content

def test_rejection_blocks_execution_and_leaves_disk_intact():
    """Assert that when reviewer rejects, the task aborts and disk remains unchanged."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()

    app = build_agent_graph()
    thread_id = "test-approval-rejection"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-rejection",
        "objective": "Investigate failing tests in repository, identify root cause, propose fix, and request approval",
        "messages": [],
        "plan": [],
        "current_step_index": 0,
        "context_data": {},
        "patch_id": None,
        "proposed_patch": None,
        "approval_status": "pending",
        "reviewer_feedback": None,
        "retry_count": 0,
        "status": "pending"
    }

    app.invoke(initial_state, config=config)

    # Submit rejection command
    resume_payload = {
        "decision": "rejected",
        "feedback": "Reviewer rejected patch: proposed fix violates code standards."
    }
    final_state = app.invoke(Command(resume=resume_payload), config=config)

    assert final_state["status"] == "cancelled"
    assert final_state.get("approval_status") == "rejected" or final_state.get("final_report", {}).get("approval_status") == "rejected"

    # Invariant: file on disk must still remain completely unmodified
    with open(calc_path, "r", encoding="utf-8") as f:
        post_rejection_content = f.read()
    assert post_rejection_content == initial_content
    assert "Missing / 100" in post_rejection_content

def test_unauthorized_patch_application_blocked():
    """Assert that calling apply_approved_patch without a valid token is blocked at the policy boundary."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()

    result = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": "patch-non-existent-999",
        "approval_token": "invalid-token-abc",
        "idempotency_key": "idem-bad-token"
    })

    assert result["success"] is False
    err = result["error"].lower()
    assert "unknown or expired" in err or "invalid" in err or "unauthorized" in err

    # Disk remains unaltered
    with open(calc_path, "r", encoding="utf-8") as f:
        current_content = f.read()
    assert current_content == initial_content

def test_approval_allows_execution_and_verifies_change():
    """Assert that when reviewer approves, the patch is applied and verified."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))

    app = build_agent_graph()
    thread_id = "test-approval-approved"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-approved",
        "objective": "Investigate failing tests in repository, identify root cause, propose fix, and request approval",
        "messages": [],
        "plan": [],
        "current_step_index": 0,
        "context_data": {},
        "patch_id": None,
        "proposed_patch": None,
        "approval_status": "pending",
        "reviewer_feedback": None,
        "retry_count": 0,
        "status": "pending"
    }

    app.invoke(initial_state, config=config)

    # Submit approval command
    resume_payload = {
        "decision": "approved",
        "feedback": "Looks good, patch approved for application."
    }
    final_state = app.invoke(Command(resume=resume_payload), config=config)

    assert final_state["status"] in ("verified", "completed")

    # Invariant: file on disk now has the fix applied
    with open(calc_path, "r", encoding="utf-8") as f:
        patched_content = f.read()
    assert "Missing / 100" not in patched_content
    assert "discount_percent / 100.0" in patched_content
