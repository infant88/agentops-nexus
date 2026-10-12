import os
import sqlite3
from typing import Any, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from backend.agent.state import AgentState
from backend.agent.policies import can_retry
from backend.agent.nodes import (
    receive_task,
    classify_and_plan,
    select_tool,
    validate_permissions_and_inputs,
    execute_tool,
    pause_for_human_approval,
    execute_approved_action,
    cancel_or_request_revision,
    verify_result,
    handle_retry,
    record_failure_and_recover,
    evaluate_and_trace,
    return_report
)

DEFAULT_CHECKPOINT_DB = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "sandbox", "checkpoints.sqlite")
)

def route_after_select_tool(state: AgentState) -> Literal["validate_permissions_and_inputs", "verify_result"]:
    if state.get("current_tool_call"):
        return "validate_permissions_and_inputs"
    return "verify_result"

def route_after_validate(state: AgentState) -> Literal["pause_for_human_approval", "execute_tool", "handle_retry", "record_failure_and_recover"]:
    last_err = state.get("last_error")
    if last_err:
        retries = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        if can_retry(last_err, retries, max_retries):
            return "handle_retry"
        return "record_failure_and_recover"
    if state.get("requires_approval"):
        return "pause_for_human_approval"
    return "execute_tool"

def route_after_execute(state: AgentState) -> Literal["handle_retry", "record_failure_and_recover", "select_tool", "verify_result"]:
    last_err = state.get("last_error")
    if last_err:
        retries = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        if can_retry(last_err, retries, max_retries):
            return "handle_retry"
        return "record_failure_and_recover"
    # Check if more steps remain in plan
    plan = state.get("plan", [])
    current_idx = state.get("current_step_index", 0)
    if current_idx < len(plan):
        return "select_tool"
    return "verify_result"

def route_after_approval(state: AgentState) -> Literal["execute_approved_action", "cancel_or_request_revision"]:
    if state.get("approval_status") == "approved":
        return "execute_approved_action"
    return "cancel_or_request_revision"

def build_agent_graph(checkpointer: Optional[Any] = None, db_path: Optional[str] = None):
    builder = StateGraph(AgentState)

    # 1. Register all nodes
    builder.add_node("receive_task", receive_task)
    builder.add_node("classify_and_plan", classify_and_plan)
    builder.add_node("select_tool", select_tool)
    builder.add_node("validate_permissions_and_inputs", validate_permissions_and_inputs)
    builder.add_node("execute_tool", execute_tool)
    builder.add_node("pause_for_human_approval", pause_for_human_approval)
    builder.add_node("execute_approved_action", execute_approved_action)
    builder.add_node("cancel_or_request_revision", cancel_or_request_revision)
    builder.add_node("verify_result", verify_result)
    builder.add_node("handle_retry", handle_retry)
    builder.add_node("record_failure_and_recover", record_failure_and_recover)
    builder.add_node("evaluate_and_trace", evaluate_and_trace)
    builder.add_node("return_report", return_report)

    # 2. Add edges
    builder.add_edge(START, "receive_task")
    builder.add_edge("receive_task", "classify_and_plan")
    builder.add_edge("classify_and_plan", "select_tool")

    builder.add_conditional_edges(
        "select_tool",
        route_after_select_tool,
        {
            "validate_permissions_and_inputs": "validate_permissions_and_inputs",
            "verify_result": "verify_result"
        }
    )

    builder.add_conditional_edges(
        "validate_permissions_and_inputs",
        route_after_validate,
        {
            "pause_for_human_approval": "pause_for_human_approval",
            "execute_tool": "execute_tool",
            "handle_retry": "handle_retry",
            "record_failure_and_recover": "record_failure_and_recover"
        }
    )

    builder.add_conditional_edges(
        "execute_tool",
        route_after_execute,
        {
            "handle_retry": "handle_retry",
            "record_failure_and_recover": "record_failure_and_recover",
            "select_tool": "select_tool",
            "verify_result": "verify_result"
        }
    )

    builder.add_edge("handle_retry", "select_tool")

    builder.add_conditional_edges(
        "pause_for_human_approval",
        route_after_approval,
        {
            "execute_approved_action": "execute_approved_action",
            "cancel_or_request_revision": "cancel_or_request_revision"
        }
    )

    builder.add_edge("execute_approved_action", "verify_result")
    builder.add_edge("cancel_or_request_revision", "evaluate_and_trace")
    builder.add_edge("record_failure_and_recover", "evaluate_and_trace")
    builder.add_edge("verify_result", "evaluate_and_trace")
    builder.add_edge("evaluate_and_trace", "return_report")
    builder.add_edge("return_report", END)

    # Durable SQLite Checkpointer
    if checkpointer is None:
        target_db = db_path or DEFAULT_CHECKPOINT_DB
        dir_name = os.path.dirname(target_db)
        if target_db != ":memory:" and dir_name:
            os.makedirs(dir_name, exist_ok=True)
        conn = sqlite3.connect(target_db, check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()
        checkpointer = saver

    app = builder.compile(checkpointer=checkpointer)
    return app

# Default compiled graph with durable SQLite persistence
agent_graph = build_agent_graph()
