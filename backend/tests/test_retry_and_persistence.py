import os
import sqlite3
import tempfile
import pytest
from backend.agent.graph import build_agent_graph
from langgraph.checkpoint.sqlite import SqliteSaver

def test_bounded_retry_routing_loop(monkeypatch):
    """Verify that transient failures route through handle_retry and recover within retry budget."""
    attempts = 0
    def mock_call_tool(tool_name, args):
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            return {"success": False, "error": "Temporary connection timeout: resource temporarily unavailable"}
        return {"success": True, "data": {"status": "ok", "passed": True}}

    from backend.agent import nodes
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

    # It must have called the tool 4 times (2 retries through handle_retry + 1 success + 1 verify_result)
    assert attempts == 4
    assert final_state.get("status") in ("completed", "verified")

def test_transient_failure_exceeding_max_retries_halts_safely(monkeypatch):
    """Verify that transient failures exceeding max_retries route to record_failure_and_recover."""
    def mock_call_tool(tool_name, args):
        return {"success": False, "error": "Persistent connection timeout: deadlock detected"}

    from backend.agent import nodes
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
        from langgraph.types import Command
        resumed_state = graph2.invoke(
            Command(resume={"decision": "approved", "feedback": "Patch authorized across restart"}),
            config=config
        )

        assert resumed_state["approval_status"] == "approved"
        assert resumed_state["status"] in ("verified", "completed", "patch_applied")
        conn2.close()
