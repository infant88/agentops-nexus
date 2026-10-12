import pytest
from langgraph.types import Command
from backend.agent.graph import build_agent_graph
from backend.sandbox.setup_sandbox import setup_sandbox

def test_full_agent_workflow_with_human_approval():
    setup_sandbox()
    app = build_agent_graph()
    thread_id = "test-thread-full-001"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-1",
        "objective": "Investigate the failing tests in my repository, identify the likely root cause, propose a fix, and wait for my approval before modifying any files.",
        "plan": [],
        "current_step_index": 0,
        "retry_count": 0,
        "max_retries": 3,
        "requires_approval": False,
        "approval_status": "none",
        "execution_history": [],
        "status": "pending"
    }

    # First invoke should pause at pause_for_human_approval interrupt
    result = app.invoke(initial_state, config=config)

    snapshot = app.get_state(config)
    assert len(snapshot.tasks) > 0
    assert snapshot.tasks[0].interrupts is not None

    interrupt_data = snapshot.tasks[0].interrupts[0].value
    assert interrupt_data["type"] == "human_approval_required"
    assert interrupt_data["payload"]["file_path"] == "calculator.py"
    assert "diff" in interrupt_data["payload"]

    # Now resume with approval
    resumed = app.invoke(Command(resume={"decision": "approved", "feedback": "Approved fix"}), config=config)

    assert resumed["approval_status"] == "approved"
    assert resumed["status"] in ("verified", "completed")
    assert resumed["verification_result"]["verified"] is True
    assert resumed["final_report"] is not None

def test_agent_workflow_human_rejection():
    setup_sandbox()
    app = build_agent_graph()
    thread_id = "test-thread-reject-002"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task_id": "test-task-2",
        "objective": "Investigate the failing tests in my repository, identify the likely root cause, propose a fix, and wait for my approval before modifying any files.",
        "plan": [],
        "current_step_index": 0,
        "retry_count": 0,
        "max_retries": 3,
        "requires_approval": False,
        "approval_status": "none",
        "execution_history": [],
        "status": "pending"
    }

    result = app.invoke(initial_state, config=config)

    # Resume with rejection
    resumed = app.invoke(Command(resume={"decision": "rejected", "feedback": "Patch declined by user"}), config=config)

    assert resumed["approval_status"] == "rejected"
    assert resumed["status"] in ("cancelled", "rejected")
