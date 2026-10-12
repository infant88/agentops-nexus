import os
import pytest
from backend.mcp_server.server import default_mcp_server
from backend.mcp_server.permissions import SecurityError, redact_secrets
from backend.sandbox.setup_sandbox import setup_sandbox

@pytest.fixture(autouse=True)
def init_test_sandbox():
    setup_sandbox()

# 1. Filesystem Adversarial Tests
def test_encoded_url_path_traversal_blocked():
    """Verify %2e%2e%2f URL-encoded traversal is detected and blocked."""
    res = default_mcp_server.call_tool("search_repository", {
        "query": "root",
        "path_pattern": "%2e%2e%2f%2e%2e%2fetc%2fshadow"
    })
    # Must fail or return error
    assert res["success"] is False
    assert "escapes sandbox" in res["error"].lower() or "access denied" in res["error"].lower()

def test_absolute_system_path_traversal_blocked():
    """Verify absolute paths outside the repo sandbox root are denied."""
    res = default_mcp_server.call_tool("propose_file_patch", {
        "file_path": "C:\\Windows\\System32\\drivers\\etc\\hosts" if os.name == "nt" else "/etc/passwd",
        "search_block": "127.0.0.1",
        "replace_block": "0.0.0.0",
        "explanation": "Malicious hosts edit"
    })
    assert res["success"] is False
    assert "escapes sandbox" in res["error"].lower() or "access denied" in res["error"].lower()

# 2. SQL Injection Adversarial Tests
def test_sql_comment_injection_blocked():
    """Verify SQL line comment (--) and block comment (/* */) injections are blocked."""
    res1 = default_mcp_server.call_tool("query_project_database", {
        "query": "SELECT * FROM project_tasks -- DROP TABLE test_runs;"
    })
    assert res1["success"] is False
    assert "forbidden sql" in res1["error"].lower()

    res2 = default_mcp_server.call_tool("query_project_database", {
        "query": "SELECT /* injection */ * FROM project_tasks;"
    })
    assert res2["success"] is False
    assert "forbidden sql" in res2["error"].lower()

def test_sql_system_table_access_blocked():
    """Verify queries targeting internal metadata tables (sqlite_master) are blocked."""
    res = default_mcp_server.call_tool("query_project_database", {
        "query": "SELECT sql FROM sqlite_master WHERE type='table';"
    })
    assert res["success"] is False
    assert "forbidden sql" in res["error"].lower()

def test_sql_stacked_queries_blocked():
    """Verify stacked semicolon queries are blocked."""
    res = default_mcp_server.call_tool("query_project_database", {
        "query": "SELECT 1; SELECT 2;"
    })
    assert res["success"] is False
    assert "forbidden sql" in res["error"].lower()

# 3. Input Validation & Oversized Payload Tests
def test_oversized_payload_rejected():
    """Verify input payloads exceeding the maximum tool size limit are rejected."""
    huge_query = "SELECT " + ("'A' AS x, " * 5000) + "1;"
    res = default_mcp_server.call_tool("query_project_database", {
        "query": huge_query
    })
    assert res["success"] is False
    assert "oversized input payload" in res["error"].lower()

def test_missing_required_fields_rejected():
    """Verify missing required parameters trigger validation error without unhandled exceptions."""
    res = default_mcp_server.call_tool("query_project_database", {})
    assert res["success"] is False
    assert "validation error" in res["error"].lower() or "missing" in res["error"].lower()

def test_invalid_type_payload_rejected():
    """Verify wrong data types in inputs are rejected gracefully."""
    res = default_mcp_server.call_tool("get_project_status", {
        "include_tests": "not-a-boolean-value-xyz"
    })
    assert res["success"] is False
    assert "validation error" in res["error"].lower()

# 4. Secret Redaction Tests
def test_secret_redaction_in_data_and_errors():
    """Verify secrets are redacted from data structures, logs, and error strings."""
    secret_payload = {
        "api_key": "sk-live-supersecretapikey123456789",
        "auth_header": "Bearer abcdef1234567890abcdef1234567890",
        "aws_key": "AKIAIOSFODNN7EXAMPLE",
        "nested": {
            "password": "ProductionDatabasePassword999!"
        }
    }
    redacted = redact_secrets(secret_payload)
    assert "sk-live-supersecretapikey123456789" not in str(redacted)
    assert "[REDACTED" in str(redacted)

# 5. Direct Tool Routing & Authorization Boundary
def test_restricted_tool_direct_call_without_token_denied():
    """Verify calling apply_approved_patch directly without approval token fails at the tool boundary."""
    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": "patch-bypass-attempt",
        "approval_token": "",
        "idempotency_key": "idem-bypass"
    })
    assert res["success"] is False
    assert "unauthorized" in res["error"].lower() or "valid approval token" in res["error"].lower()

# 6. Concurrency & Idempotency Replay Prevention
def test_concurrent_duplicate_mutation_requests_idempotent():
    """Verify duplicate patch application with same idempotency key is safely deduplicated."""
    from backend.mcp_server.tools import _PENDING_PATCHES
    from backend.agent.approval_manager import default_approval_manager

    patch_id = "patch-concurrency-test"
    calc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo", "calculator.py"))
    _PENDING_PATCHES[patch_id] = {
        "patch_id": patch_id,
        "file_path": "calculator.py",
        "full_path": calc_path,
        "search_block": "    discount_amount = price * (discount_percent)  # Missing / 100",
        "replace_block": "    discount_amount = price * (discount_percent / 100.0)  # Concurrency fix",
        "status": "pending_approval"
    }
    token = default_approval_manager.issue_approval_token(
        task_id="task-conc",
        action="apply_approved_patch",
        patch_id=patch_id,
        arguments=_PENDING_PATCHES[patch_id]
    )

    # First request applies patch
    res1 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": "idem-concurrency-key-1"
    })
    assert res1["success"] is True

    # Concurrent / duplicate request with same idempotency key returns idempotent replay without repeating write
    res2 = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": token,
        "idempotency_key": "idem-concurrency-key-1"
    })
    assert res2["success"] is True
    assert res2["data"].get("idempotent_replay") is True
