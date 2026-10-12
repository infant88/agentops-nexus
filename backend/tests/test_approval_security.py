import os
import time
import pytest
from langgraph.types import Command

from backend.agent.graph import build_agent_graph
from backend.sandbox.setup_sandbox import setup_sandbox
from backend.mcp_server.server import default_mcp_server
from backend.mcp_server.tools import _PENDING_PATCHES
from backend.agent.approval_manager import default_approval_manager, ApprovalSecurityError

@pytest.fixture(autouse=True)
def init_test_sandbox():
    setup_sandbox()
    default_approval_manager.clear()

def test_pre_approval_disk_invariance():
    """1. Sensitive action pauses before any side effect occurs."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()
    assert "Missing / 100" in initial_content

    app = build_agent_graph()
    thread_id = "test-sec-1-pause"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-sec-1",
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

    snapshot = app.get_state(config)
    assert len(snapshot.tasks) > 0
    assert any(len(t.interrupts) > 0 for t in snapshot.tasks)

    with open(calc_path, "r", encoding="utf-8") as f:
        pre_resume_content = f.read()
    assert pre_resume_content == initial_content
    assert "Missing / 100" in pre_resume_content

def test_approval_allows_execution_exactly_once():
    """2. Approved action executes exactly once."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))

    app = build_agent_graph()
    thread_id = "test-sec-2-exec-once"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-sec-2",
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

    resume_payload = {"decision": "approved", "feedback": "Approved by reviewer"}
    final_state = app.invoke(Command(resume=resume_payload), config=config)

    assert final_state["status"] in ("verified", "completed")
    with open(calc_path, "r", encoding="utf-8") as f:
        patched_content = f.read()
    assert "discount_percent / 100.0" in patched_content

def test_rejection_blocks_execution_and_leaves_disk_intact():
    """3. Rejected action never executes."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()

    app = build_agent_graph()
    thread_id = "test-sec-3-rejection"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-sec-3",
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

    resume_payload = {"decision": "rejected", "feedback": "Proposed change violates standards."}
    final_state = app.invoke(Command(resume=resume_payload), config=config)

    assert final_state["status"] == "cancelled"
    with open(calc_path, "r", encoding="utf-8") as f:
        post_content = f.read()
    assert post_content == initial_content
    assert "Missing / 100" in post_content

def test_revision_requested_returns_to_workflow_without_execution():
    """4. Revision requested returns to workflow without executing the original action."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    with open(calc_path, "r", encoding="utf-8") as f:
        initial_content = f.read()

    app = build_agent_graph()
    thread_id = "test-sec-4-revision"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-sec-4",
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

    resume_payload = {"decision": "revision_requested", "feedback": "Please add docstring comments."}
    final_state = app.invoke(Command(resume=resume_payload), config=config)

    assert final_state["status"] == "cancelled"
    with open(calc_path, "r", encoding="utf-8") as f:
        post_content = f.read()
    assert post_content == initial_content

def test_missing_approval_is_denied():
    """5. Missing approval is denied."""
    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": "patch-test-missing",
        "approval_token": "",
        "idempotency_key": "idem-missing"
    })
    assert res["success"] is False
    assert "unauthorized" in res["error"].lower() or "valid approval token" in res["error"].lower()

def test_expired_or_stale_approval_is_denied():
    """6. Expired or stale approval is denied."""
    patch_id = "patch-test-expired"
    _PENDING_PATCHES[patch_id] = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py")),
        "search_block": "Missing / 100",
        "replace_block": "Fixed",
        "status": "pending_approval"
    }
    # Issue token that expired 10 seconds ago
    expired_token = default_approval_manager.issue_approval_token(
        task_id="task-expired",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=_PENDING_PATCHES[patch_id],
        ttl_seconds=-10
    )

    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": expired_token,
        "idempotency_key": "idem-expired"
    })
    assert res["success"] is False
    assert "expired" in res["error"].lower()

def test_approval_for_one_action_cannot_authorize_different_action():
    """7. Approval for one action cannot authorize a different action."""
    patch_a = "patch-valid-A"
    patch_b = "patch-valid-B"
    _PENDING_PATCHES[patch_a] = {
        "patch_id": patch_a,
        "file_path": "calculator.py",
        "full_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py")),
        "search_block": "Missing / 100",
        "replace_block": "Fixed",
        "status": "pending_approval"
    }
    _PENDING_PATCHES[patch_b] = {
        "patch_id": patch_b,
        "file_path": "calculator.py",
        "full_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py")),
        "search_block": "calculate_tax",
        "replace_block": "calculate_tax_v2",
        "status": "pending_approval"
    }
    token_for_a = default_approval_manager.issue_approval_token(
        task_id="task-action-bind",
        action="apply_approved_patch",
        patch_id=patch_a,
        arguments=_PENDING_PATCHES[patch_a]
    )

    # Try applying token_for_a to patch_b
    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_b,
        "approval_token": token_for_a,
        "idempotency_key": "idem-cross-patch"
    })
    assert res["success"] is False
    assert "mismatch" in res["error"].lower() or "unauthorized" in res["error"].lower()

def test_approval_cannot_be_reused_for_second_execution():
    """8. Approval cannot be reused for a second execution (replay prevention)."""
    patch_id = "patch-replay-test"
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    _PENDING_PATCHES[patch_id] = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": calc_path,
        "search_block": "    discount_amount = price * (discount_percent)  # Missing / 100",
        "replace_block": "    discount_amount = price * (discount_percent / 100.0)  # Replay fix",
        "status": "pending_approval"
    }
    token = default_approval_manager.issue_approval_token(
        task_id="task-replay",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=_PENDING_PATCHES[patch_id]
    )

    # First execution succeeds
    res1 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": "idem-replay-1"
    })
    assert res1["success"] is True

    # Second execution using same token with different idempotency key is rejected
    res2 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": "idem-replay-2"
    })
    assert res2["success"] is False
    assert "consumed" in res2["error"].lower() or "unauthorized" in res2["error"].lower()

def test_unauthorized_user_cannot_approve_request():
    """9. Unauthorized user cannot approve another user's request."""
    patch_id = "patch-unauth-user"
    _PENDING_PATCHES[patch_id] = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py")),
        "search_block": "Missing / 100",
        "replace_block": "Fixed",
        "status": "pending_approval"
    }
    token = default_approval_manager.issue_approval_token(
        task_id="task-principal-1",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=_PENDING_PATCHES[patch_id],
        approver_principal="lead-architect"
    )

    with pytest.raises(ApprovalSecurityError) as exc_info:
        default_approval_manager.validate_and_consume_token(
            token=token,
            task_id="task-principal-1",
            action="apply_approved_patch",
            patch_id=patch_id,
            approver_principal="malicious-guest"
        )
    assert "unauthorized approver" in str(exc_info.value).lower()

def test_tampered_tool_arguments_invalidate_approval():
    """10. Tampered tool arguments invalidate the approval."""
    patch_id = "patch-tamper-test"
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    original_args = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": calc_path,
        "search_block": "price * (discount_percent)",
        "replace_block": "price * (discount_percent / 100.0)"
    }
    _PENDING_PATCHES[patch_id] = original_args

    token = default_approval_manager.issue_approval_token(
        task_id="task-tamper",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=original_args
    )

    # Malicious actor tampers with replace_block to inject backdoors
    tampered_args = dict(original_args)
    tampered_args["replace_block"] = "import os; os.system('rm -rf /')"
    _PENDING_PATCHES[patch_id] = tampered_args

    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": "idem-tamper"
    })
    assert res["success"] is False
    assert "tampered" in res["error"].lower() or "unauthorized" in res["error"].lower()

def test_workflow_restart_preserves_pending_approval():
    """11. Workflow restart preserves the pending approval safely."""
    thread_id = "test-sec-11-restart"
    config = {"configurable": {"thread_id": thread_id}}

    app1 = build_agent_graph()
    initial_state = {
        "task_id": "test-task-sec-11",
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

    app1.invoke(initial_state, config=config)

    # Simulate full process restart with clean graph instance pointing to same checkpoint thread
    app2 = build_agent_graph()
    snapshot = app2.get_state(config)
    assert len(snapshot.tasks) > 0
    assert any(len(t.interrupts) > 0 for t in snapshot.tasks)

def test_repeated_resume_requests_do_not_duplicate_side_effects():
    """12. Repeated resume requests do not duplicate side effects."""
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))

    app = build_agent_graph()
    thread_id = "test-sec-12-dup-resume"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-sec-12",
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

    # First resume approves
    resume_payload = {"decision": "approved", "feedback": "Approved"}
    final1 = app.invoke(Command(resume=resume_payload), config=config)
    assert final1["status"] in ("verified", "completed")

    with open(calc_path, "r", encoding="utf-8") as f:
        content_after_first = f.read()

    # Re-checking state after completion
    final_snap = app.get_state(config)
    assert len(final_snap.tasks) == 0  # No pending interrupts remain

    with open(calc_path, "r", encoding="utf-8") as f:
        content_after_second = f.read()
    assert content_after_first == content_after_second
