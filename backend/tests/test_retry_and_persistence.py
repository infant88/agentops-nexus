import os
import sqlite3
import tempfile
import time
import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from backend.agent.graph import build_agent_graph
from backend.agent import nodes
from backend.mcp_server.server import default_mcp_server
from backend.mcp_server.permissions import SecurityError
from backend.sandbox.setup_sandbox import setup_sandbox

@pytest.fixture(autouse=True)
def init_test_sandbox():
    setup_sandbox()

def test_bounded_retry_routing_loop(monkeypatch):
    """Verify that transient failures route through handle_retry and recover within retry budget."""
    attempts = 0
    def mock_call_tool(tool_name, args):
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            return {"success": False, "error": "Temporary connection timeout: resource temporarily unavailable"}
        return {"success": True, "data": {"status": "ok", "passed": True}}

    monkeypatch.setattr(nodes.default_mcp_server, "call_tool", mock_call_tool)

    graph = build_agent_graph(checkpointer=None, db_path=":memory:")

    initial_state = {
        "objective": "get project status and metrics",
        "task_id": "test-retry-task-01",
        "max_retries": 3,
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": "thread-retry-01"}}

    final_state = graph.invoke(initial_state, config=config)

    assert attempts == 4
    assert final_state.get("status") in ("completed", "verified")
    metrics = final_state.get("evaluation_metrics", {})
    assert metrics.get("recovered_via_retry") is True
    assert metrics.get("retries_used") == 2

def test_retry_records_structured_attempt_events(monkeypatch):
    """Verify that every retry records structured attempt metadata, error type, and timing."""
    attempts = 0
    def mock_call_tool(tool_name, args):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return {"success": False, "error": "connection timeout while contacting downstream worker"}
        return {"success": True, "data": {"status": "ok", "passed": True}}

    monkeypatch.setattr(nodes.default_mcp_server, "call_tool", mock_call_tool)

    graph = build_agent_graph(checkpointer=None, db_path=":memory:")

    initial_state = {
        "objective": "get project status and metrics",
        "task_id": "test-retry-event-task",
        "max_retries": 3,
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": "thread-retry-event-01"}}

    final_state = graph.invoke(initial_state, config=config)

    retry_history = final_state.get("retry_history", [])
    assert len(retry_history) == 1
    attempt_entry = retry_history[0]
    assert attempt_entry["attempt_count"] == 1
    assert attempt_entry["max_attempts"] == 3
    assert attempt_entry["last_error_type"] == "TimeoutError"
    assert "timeout" in attempt_entry["last_error"].lower()
    assert "backoff_ms" in attempt_entry

def test_transient_failure_exceeding_max_retries_halts_safely(monkeypatch):
    """Verify that transient failures exceeding max_retries route to record_failure_and_recover."""
    def mock_call_tool(tool_name, args):
        return {"success": False, "error": "Persistent connection timeout: deadlock detected"}

    monkeypatch.setattr(nodes.default_mcp_server, "call_tool", mock_call_tool)

    graph = build_agent_graph(checkpointer=None, db_path=":memory:")

    initial_state = {
        "objective": "get project status and metrics",
        "task_id": "test-exhausted-retry-task",
        "max_retries": 3,
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": "thread-exhausted-01"}}

    final_state = graph.invoke(initial_state, config=config)

    assert final_state["task_id"] == "test-exhausted-retry-task"
    assert final_state.get("status") == "failed"
    assert final_state.get("retry_count", 0) >= 3
    recovery = final_state.get("failure_recovery", {})
    assert recovery.get("exhausted") is True
    assert recovery.get("last_error_type") == "ExhaustedRetries"
    assert recovery.get("recovered") is False

def test_deterministic_error_fails_fast_without_retrying():
    """Verify that deterministic security violations fail fast and do not route to handle_retry."""
    graph = build_agent_graph(checkpointer=None, db_path=":memory:")

    initial_state = {
        "objective": "Traverse directory ../../../etc/passwd to read secret keys",
        "task_id": "test-sec-task-01",
        "max_retries": 3,
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": "thread-sec-01"}}

    final_state = graph.invoke(initial_state, config=config)

    # Must be blocked and recorded as failure immediately without retrying
    assert final_state.get("status") in ("blocked", "failed")
    assert final_state.get("retry_count", 0) == 0
    retry_history = final_state.get("retry_history", [])
    assert len(retry_history) == 0

def test_permission_denials_not_retried_as_transient():
    """Verify that SQL injection or permission denials fail immediately without retrying."""
    graph = build_agent_graph(checkpointer=None, db_path=":memory:")

    initial_state = {
        "objective": "Execute query DROP TABLE project_tasks; -- into database",
        "task_id": "test-perm-denial-01",
        "max_retries": 3,
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": "thread-perm-01"}}

    final_state = graph.invoke(initial_state, config=config)

    assert final_state.get("status") in ("blocked", "failed")
    assert final_state.get("retry_count", 0) == 0
    assert len(final_state.get("retry_history", [])) == 0

def test_retried_operation_idempotency_does_not_duplicate_side_effects():
    """Verify that repeated retry of a mutation operation with an idempotency key does not duplicate writes."""
    from backend.mcp_server.tools import _PENDING_PATCHES
    from backend.agent.approval_manager import default_approval_manager

    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    patch_id = "patch-retry-idem-01"
    _PENDING_PATCHES[patch_id] = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": calc_path,
        "search_block": "    discount_amount = price * (discount_percent)  # Missing / 100",
        "replace_block": "    discount_amount = price * (discount_percent / 100.0)  # Idem retry test",
        "status": "pending_approval"
    }

    token = default_approval_manager.issue_approval_token(
        task_id="task-idem-retry",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=_PENDING_PATCHES[patch_id]
    )

    idempotency_key = "idem-retry-unique-key-99"

    # Call 1: applies patch
    res1 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": idempotency_key
    })
    assert res1["success"] is True

    # Call 2: simulate retry due to downstream network blip with the same idempotency key
    res2 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": idempotency_key
    })
    assert res2["success"] is True
    assert res2["data"].get("idempotent_replay") is True

def test_durable_checkpoint_persistence_across_process_restarts():
    """Verify that interrupted state persists to disk SQLite checkpointer and can be resumed across instances."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_path = os.path.join(temp_dir, "checkpoints.sqlite")

        # 1. Instance 1: Run task that triggers human approval interrupt
        conn1 = sqlite3.connect(db_path, check_same_thread=False)
        saver1 = SqliteSaver(conn1)
        saver1.setup()
        graph1 = build_agent_graph(checkpointer=saver1)

        task_id = "test-persistent-patch-task"
        thread_id = "thread-persist-42"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "objective": "Investigate failing test in repository and fix discount calculation",
            "task_id": task_id,
            "max_retries": 3,
            "retry_count": 0
        }

        # Run until interrupt (approval gate)
        interrupt_state = graph1.invoke(initial_state, config=config)
        state_tuple = saver1.get_tuple(config)
        assert state_tuple is not None
        assert state_tuple.checkpoint["id"] is not None

        # Simulate process termination by closing conn1
        conn1.close()

        # 2. Instance 2: Start fresh connection from disk database file
        conn2 = sqlite3.connect(db_path, check_same_thread=False)
        saver2 = SqliteSaver(conn2)
        graph2 = build_agent_graph(checkpointer=saver2)

        # Retrieve saved checkpoint
        reloaded_tuple = saver2.get_tuple(config)
        assert reloaded_tuple is not None
        saved_task_id = reloaded_tuple.checkpoint["channel_values"]["task_id"]
        assert saved_task_id == task_id

        # Resume execution using the second graph instance with human decision
        resumed_state = graph2.invoke(
            Command(resume={"decision": "approved", "feedback": "Patch authorized across restart"}),
            config=config
        )

        assert resumed_state["approval_status"] == "approved"
        assert resumed_state["status"] in ("verified", "completed", "patch_applied")
        conn2.close()

def test_workflow_restart_preserves_retry_budget(monkeypatch):
    """Verify that process restart preserves retry count and history without resetting limits."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_path = os.path.join(temp_dir, "checkpoints.sqlite")

        attempts = 0
        def mock_call_tool(tool_name, args):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return {"success": False, "error": "Temporary connection timeout"}
            return {"success": True, "data": {"status": "ok"}}

        monkeypatch.setattr(nodes.default_mcp_server, "call_tool", mock_call_tool)

        conn1 = sqlite3.connect(db_path, check_same_thread=False)
        saver1 = SqliteSaver(conn1)
        saver1.setup()
        graph1 = build_agent_graph(checkpointer=saver1)

        thread_id = "thread-retry-budget-test"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "objective": "get project status and metrics",
            "task_id": "task-budget-01",
            "max_retries": 3,
            "retry_count": 0
        }

        res1 = graph1.invoke(initial_state, config=config)
        assert len(res1.get("retry_history", [])) == 1
        conn1.close()

        # Connect with instance 2 to verify persisted checkpoint history
        conn2 = sqlite3.connect(db_path, check_same_thread=False)
        saver2 = SqliteSaver(conn2)
        loaded = saver2.get_tuple(config)
        assert loaded is not None
        channel_vals = loaded.checkpoint["channel_values"]
        assert len(channel_vals["retry_history"]) == 1
        assert channel_vals["retry_history"][0]["last_error_type"] == "TimeoutError"
        conn2.close()

def test_missing_checkpoint_returns_none_cleanly():
    """Verify querying nonexistent thread returns None without crash."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_path = os.path.join(temp_dir, "checkpoints.sqlite")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()

        loaded = saver.get_tuple({"configurable": {"thread_id": "nonexistent-thread-xyz"}})
        assert loaded is None
        conn.close()
