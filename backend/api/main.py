import os
import sys
import uuid
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langgraph.types import Command

# Ensure backend root is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database.connection import init_db, get_db, SessionLocal
from backend.database.models import TaskRecord, AuditEvent, TraceSpan, EvaluationRun
from backend.agent.graph import build_agent_graph
from backend.mcp_server.server import default_mcp_server
from backend.observability.tracing import get_tracer
from backend.evaluation.runner import run_evaluation_suite
from backend.sandbox.setup_sandbox import setup_sandbox

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    setup_sandbox()
    yield

app = FastAPI(
    title="AgentOps Nexus API",
    description="Stateful LangGraph AI Agent Orchestration, MCP Tool Ecosystem, Human-in-the-Loop Approvals & Observability",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active execution threads store: task_id -> {"app": app, "config": config, "state": state}
_ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

class CreateTaskRequest(BaseModel):
    objective: str = Field(..., description="Task objective or goal for the agent")

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'approved', 'rejected', or 'revision_requested'")
    feedback: Optional[str] = Field(default="", description="Optional human reviewer instructions")

class ExecuteToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "service": "AgentOps Nexus",
        "version": "1.0.0",
        "mcp_tools_available": len(default_mcp_server.list_tools())
    }

# ----------------- Task Orchestration Endpoints -----------------

@app.post("/api/tasks")
def create_task(req: CreateTaskRequest):
    task_id = f"nexus-{uuid.uuid4().hex[:8]}"
    app_instance = build_agent_graph()
    config = {"configurable": {"thread_id": task_id}}

    initial_state = {
        "task_id": task_id,
        "objective": req.objective,
        "plan": [],
        "current_step_index": 0,
        "retry_count": 0,
        "max_retries": 3,
        "requires_approval": False,
        "approval_status": "none",
        "execution_history": [],
        "status": "pending"
    }

    # Record in DB
    db = SessionLocal()
    task_record = TaskRecord(
        id=task_id,
        objective=req.objective,
        status="planning",
        current_step=0,
        retry_count=0,
        requires_approval=False,
        approval_status="none"
    )
    db.add(task_record)
    db.commit()

    # Run LangGraph workflow up to completion or interrupt
    result = None
    interrupted = False
    interrupt_payload = None

    try:
        result = app_instance.invoke(initial_state, config=config)

        # Inspect if halted on human approval interrupt
        snapshot = app_instance.get_state(config)
        if snapshot.tasks:
            for t in snapshot.tasks:
                if t.interrupts:
                    interrupted = True
                    interrupt_payload = t.interrupts[0].value if hasattr(t.interrupts[0], "value") else str(t.interrupts[0])
                    break

        # Save session for approval resumption
        _ACTIVE_SESSIONS[task_id] = {
            "app": app_instance,
            "config": config,
            "state": result or snapshot.values
        }

        # Update database record
        status_val = "waiting_approval" if interrupted else result.get("status", "completed")
        task_record.status = status_val
        task_record.plan = result.get("plan", []) if result else snapshot.values.get("plan", [])
        task_record.requires_approval = interrupted or result.get("requires_approval", False)
        task_record.approval_status = "pending" if interrupted else result.get("approval_status", "none")
        task_record.approval_payload = interrupt_payload or (result.get("approval_payload") if result else None)
        task_record.current_step = result.get("current_step_index", 0) if result else snapshot.values.get("current_step_index", 0)
        task_record.result_summary = result.get("final_report", {}).get("root_cause") if result else None
        db.commit()

    except Exception as e:
        task_record.status = "failed"
        task_record.error_message = str(e)
        db.commit()
    finally:
        db.close()

    return {
        "task_id": task_id,
        "status": "waiting_approval" if interrupted else (result.get("status") if result else "failed"),
        "interrupted": interrupted,
        "approval_required": interrupted,
        "approval_payload": interrupt_payload or (result.get("approval_payload") if result else None),
        "plan": result.get("plan") if result else [],
        "execution_history": result.get("execution_history") if result else [],
        "final_report": result.get("final_report") if result else None
    }

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    db = SessionLocal()
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    db.close()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session = _ACTIVE_SESSIONS.get(task_id)
    snapshot_values = session["state"] if session else {}

    return {
        "id": task.id,
        "objective": task.objective,
        "status": task.status,
        "plan": task.plan or snapshot_values.get("plan", []),
        "current_step": task.current_step,
        "retry_count": task.retry_count,
        "requires_approval": task.requires_approval,
        "approval_status": task.approval_status,
        "approval_payload": task.approval_payload,
        "result_summary": task.result_summary,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "execution_history": snapshot_values.get("execution_history", []),
        "final_report": snapshot_values.get("final_report"),
        "verification_result": snapshot_values.get("verification_result")
    }

@app.post("/api/tasks/{task_id}/approval")
def submit_approval(task_id: str, req: ApprovalDecisionRequest):
    session = _ACTIVE_SESSIONS.get(task_id)
    if not session:
        # Restore execution thread from durable SQLite checkpointer
        app_instance = build_agent_graph()
        config = {"configurable": {"thread_id": task_id}}
        session = {
            "app": app_instance,
            "config": config,
            "state": {}
        }
        _ACTIVE_SESSIONS[task_id] = session

    app_instance = session["app"]
    config = session["config"]

    resume_payload = {
        "decision": req.decision,
        "feedback": req.feedback
    }

    try:
        # Resume graph execution from checkpoint!
        result = app_instance.invoke(Command(resume=resume_payload), config=config)
        session["state"] = result

        # Update DB record
        db = SessionLocal()
        task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if task:
            task.approval_status = req.decision
            task.status = result.get("status", "completed")
            task.result_summary = result.get("final_report", {}).get("root_cause")
            db.commit()
        db.close()

        return {
            "task_id": task_id,
            "status": result.get("status", "completed"),
            "approval_status": req.decision,
            "execution_history": result.get("execution_history", []),
            "verification_result": result.get("verification_result"),
            "final_report": result.get("final_report")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume execution: {str(e)}")

@app.get("/api/tasks")
def list_tasks():
    db = SessionLocal()
    tasks = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).limit(30).all()
    results = [
        {
            "id": t.id,
            "objective": t.objective,
            "status": t.status,
            "requires_approval": t.requires_approval,
            "approval_status": t.approval_status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]
    db.close()
    return results

# ----------------- Observability & Tracing Endpoints -----------------

@app.get("/api/tasks/{task_id}/trace")
def get_task_trace(task_id: str):
    tracer = get_tracer(task_id)
    trace = tracer.export_langsmith_trace()
    return trace

@app.get("/api/tasks/{task_id}/audit")
def get_task_audit(task_id: str):
    db = SessionLocal()
    events = db.query(AuditEvent).filter(AuditEvent.task_id == task_id).order_by(AuditEvent.timestamp.asc()).all()
    results = [
        {
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "event_type": e.event_type,
            "tool_name": e.tool_name,
            "parameters": e.parameters,
            "outcome": e.outcome,
            "metadata": e.metadata_json
        }
        for e in events
    ]
    db.close()
    return results

# ----------------- MCP Tools Endpoints -----------------

@app.get("/api/tools")
@app.get("/api/mcp/tools")
def list_mcp_tools():
    """Expose tools conforming to MCP JSON schema tool discovery."""
    return default_mcp_server.list_tools()

@app.post("/api/tools/execute")
@app.post("/api/mcp/call")
def execute_mcp_tool(req: ExecuteToolRequest):
    """Execute an MCP tool call with validation, secret redaction, and sandboxing."""
    return default_mcp_server.call_tool(req.tool_name, req.arguments)

# ----------------- Evaluation Benchmark Endpoints -----------------

@app.get("/api/evaluations")
def get_evaluations():
    db = SessionLocal()
    runs = db.query(EvaluationRun).order_by(EvaluationRun.run_timestamp.desc()).limit(10).all()
    results = [
        {
            "id": r.id,
            "timestamp": r.run_timestamp.isoformat() if r.run_timestamp else None,
            "total_cases": r.total_cases,
            "successful_cases": r.successful_cases,
            "success_rate": r.success_rate,
            "tool_accuracy": r.tool_accuracy,
            "avg_latency_ms": r.avg_latency_ms,
            "total_tokens": r.total_tokens,
            "retry_recovery_rate": r.retry_recovery_rate,
            "approval_compliance_rate": r.approval_compliance_rate,
            "total_cost_usd": r.total_cost_usd,
            "summary": r.results_summary
        }
        for r in runs
    ]
    db.close()
    return results

@app.post("/api/evaluations/run")
def trigger_evaluation():
    result = run_evaluation_suite()
    return result

# ----------------- Sandbox Repository Inspector -----------------

@app.get("/api/sandbox/files")
def get_sandbox_files():
    repo_root = default_mcp_server.policy.repo_root
    files_data = []

    for root, _, files in os.walk(repo_root):
        for f in files:
            if f.endswith(".py") or f.endswith(".md") or f.endswith(".txt"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, repo_root).replace("\\", "/")
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                files_data.append({
                    "path": rel_path,
                    "size": os.path.getsize(full_path),
                    "content": content
                })

    return {
        "repo_root": repo_root,
        "files": files_data
    }

@app.post("/api/sandbox/reset")
def reset_sandbox():
    setup_sandbox()
    return {"success": True, "message": "Sandbox repo and test database reset to initial state."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
