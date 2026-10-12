import os
import pytest
from backend.mcp_server.permissions import PermissionPolicy, SecurityError, redact_secrets
from backend.mcp_server.server import default_mcp_server

def test_path_traversal_blocked():
    policy = default_mcp_server.policy
    with pytest.raises(SecurityError) as exc_info:
        policy.validate_file_path("../../../etc/shadow")
    assert "escapes sandbox boundary" in str(exc_info.value)

def test_null_byte_blocked():
    policy = default_mcp_server.policy
    with pytest.raises(SecurityError):
        policy.validate_file_path("calculator.py\0.txt")

def test_sql_read_only_enforcement():
    policy = default_mcp_server.policy

    # Disallow DROP
    with pytest.raises(SecurityError):
        policy.validate_sql("DROP TABLE project_tasks;")

    # Disallow DELETE
    with pytest.raises(SecurityError):
        policy.validate_sql("DELETE FROM project_tasks WHERE id = 1;")

    # Disallow INSERT
    with pytest.raises(SecurityError):
        policy.validate_sql("INSERT INTO project_tasks (ticket_id) VALUES ('HACK');")

    # Allow valid SELECT
    policy.validate_sql("SELECT * FROM project_tasks LIMIT 10;")
    policy.validate_sql("PRAGMA table_info(project_tasks);")

def test_secret_redaction():
    raw_data = {
        "api_key": "sk-1234567890abcdef1234567890",
        "auth_header": "Bearer secret_jwt_token_payload_here",
        "normal_text": "Normal operation sk-1234567890abcdef1234567890 here"
    }
    cleaned = redact_secrets(raw_data)
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["auth_header"] == "[REDACTED]"
    assert "[REDACTED_SECRET]" in cleaned["normal_text"]

def test_idempotency_control():
    policy = default_mcp_server.policy
    key = "idem-test-key-1"
    first = policy.check_and_record_idempotency(key, "apply patch test")
    assert first is False  # Not seen before

    second = policy.check_and_record_idempotency(key, "apply patch test")
    assert second is True  # Replay detected
