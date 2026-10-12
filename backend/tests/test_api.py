import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.sandbox.setup_sandbox import setup_sandbox

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_list_tools():
    res = client.get("/api/tools")
    assert res.status_code == 200
    tools = res.json()
    tool_names = [t["name"] for t in tools]
    assert "search_repository" in tool_names
    assert "query_project_database" in tool_names
    assert "apply_approved_patch" in tool_names

def test_task_creation_and_approval_flow():
    setup_sandbox()
    # 1. Create task
    res = client.post("/api/tasks", json={
        "objective": "Investigate failing tests in my repository, identify root cause, propose fix, and wait for my approval"
    })
    assert res.status_code == 200
    data = res.json()
    task_id = data["task_id"]
    assert data["approval_required"] is True
    assert data["status"] == "waiting_approval"

    # 2. Get task details
    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    task_data = get_res.json()
    assert task_data["status"] == "waiting_approval"
    assert task_data["approval_payload"] is not None

    # 3. Submit approval
    appr_res = client.post(f"/api/tasks/{task_id}/approval", json={
        "decision": "approved",
        "feedback": "LGTM, apply the discount calculation fix."
    })
    assert appr_res.status_code == 200
    resumed_data = appr_res.json()
    assert resumed_data["approval_status"] == "approved"
    assert resumed_data["status"] in ("verified", "completed")

    # 4. Check trace
    trace_res = client.get(f"/api/tasks/{task_id}/trace")
    assert trace_res.status_code == 200
    trace = trace_res.json()
    assert "spans" in trace
    assert len(trace["spans"]) > 0
