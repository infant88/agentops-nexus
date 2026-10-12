import os
import re
from typing import Any, Dict, Tuple

import urllib.parse

TOOL_PERMISSION_MATRIX = {
    "search_repository": {
        "allowed_operations": ["read_files", "regex_search"],
        "permitted_scope": "repo_root",
        "required_permission": "read",
        "requires_approval": False,
        "max_input_size_bytes": 65536,
        "timeout_seconds": 30,
        "retry_safe": True,
        "audited_events": ["tool_invoked", "search_executed"]
    },
    "get_project_status": {
        "allowed_operations": ["read_status", "read_tickets", "read_test_runs"],
        "permitted_scope": "project_db",
        "required_permission": "read",
        "requires_approval": False,
        "max_input_size_bytes": 4096,
        "timeout_seconds": 15,
        "retry_safe": True,
        "audited_events": ["tool_invoked", "status_retrieved"]
    },
    "query_project_database": {
        "allowed_operations": ["read_only_select", "pragma_info"],
        "permitted_scope": "project_tasks, test_runs, system_config",
        "required_permission": "read",
        "requires_approval": False,
        "max_input_size_bytes": 16384,
        "timeout_seconds": 20,
        "retry_safe": True,
        "audited_events": ["query_validated", "query_executed", "security_violation"]
    },
    "run_test_suite": {
        "allowed_operations": ["execute_unit_tests"],
        "permitted_scope": "repo_root",
        "required_permission": "execute",
        "requires_approval": False,
        "max_input_size_bytes": 4096,
        "timeout_seconds": 60,
        "retry_safe": True,
        "audited_events": ["test_started", "test_completed"]
    },
    "propose_file_patch": {
        "allowed_operations": ["read_file", "generate_diff"],
        "permitted_scope": "repo_root",
        "required_permission": "read",
        "requires_approval": False,
        "max_input_size_bytes": 131072,
        "timeout_seconds": 30,
        "retry_safe": False,
        "audited_events": ["patch_proposed"]
    },
    "apply_approved_patch": {
        "allowed_operations": ["modify_file"],
        "permitted_scope": "repo_root",
        "required_permission": "write",
        "requires_approval": True,
        "max_input_size_bytes": 131072,
        "timeout_seconds": 30,
        "retry_safe": False,
        "audited_events": ["approval_verified", "patch_applied"]
    }
}

FORBIDDEN_SQL_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|TRUNCATE|EXEC|VACUUM|GRANT|REVOKE)\b",
    r";\s*\S+",  # Disallow multiple chained queries
    r"--",        # Disallow SQL line comment injection
    r"/\*|\*/",   # Disallow SQL block comment injection
    r"\b(sqlite_master|sqlite_temp_master|sqlite_schema)\b", # Disallow inspecting system metadata tables directly
]

ALLOWED_SQL_PREFIXES = ("SELECT", "PRAGMA TABLE_INFO", "PRAGMA INDEX_LIST", "EXPLAIN")

SECRET_REGEX = re.compile(
    r"(sk-[a-zA-Z0-9_\-]{16,}|bearer\s+[a-zA-Z0-9_\-\.]{16,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|password\s*[:=]\s*\S+)",
    re.IGNORECASE
)

class SecurityError(Exception):
    """Raised when a security boundary is violated."""
    pass

class PermissionPolicy:
    def __init__(self, repo_root: str, db_path: str):
        self.repo_root = os.path.realpath(repo_root)
        self.db_path = os.path.realpath(db_path)
        self._applied_idempotency_keys: Dict[str, Dict[str, Any]] = {}

    def validate_input_size(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Enforces maximum payload size limits per tool."""
        spec = TOOL_PERMISSION_MATRIX.get(tool_name)
        if spec:
            max_size = spec.get("max_input_size_bytes", 65536)
            serialized_size = len(str(arguments).encode("utf-8"))
            if serialized_size > max_size:
                raise SecurityError(
                    f"Oversized input payload for tool '{tool_name}': {serialized_size} bytes exceeds limit of {max_size} bytes."
                )

    def validate_file_path(self, relative_or_abs_path: str) -> str:
        """Ensures file access stays strictly confined within repo_root."""
        if not relative_or_abs_path:
            raise SecurityError("File path cannot be empty.")

        # Check for null bytes
        if "\0" in relative_or_abs_path:
            raise SecurityError("Null byte injection detected in file path.")

        # URL decode check (blocks encoded traversal such as %2e%2e)
        decoded_path = urllib.parse.unquote(relative_or_abs_path)
        if "\0" in decoded_path:
            raise SecurityError("Null byte injection detected in decoded file path.")

        # If relative, anchor to repo_root
        if not os.path.isabs(decoded_path):
            target = os.path.join(self.repo_root, decoded_path)
        else:
            target = decoded_path

        resolved = os.path.realpath(target)

        # Path traversal and symlink escape jail check
        try:
            common = os.path.commonpath([resolved, self.repo_root])
            if common != self.repo_root:
                raise SecurityError(
                    f"Access denied: Path '{relative_or_abs_path}' escapes sandbox boundary '{self.repo_root}'."
                )
        except ValueError:
            # Raised on Windows when paths are on different drives (e.g. C:\ vs D:\)
            raise SecurityError(
                f"Access denied: Path '{relative_or_abs_path}' escapes sandbox boundary '{self.repo_root}'."
            )

        return resolved

    def validate_sql(self, query: str) -> None:
        """Validates that SQL is strictly read-only and non-destructive."""
        cleaned = query.strip()
        if not cleaned:
            raise SecurityError("SQL query cannot be empty.")

        upper = cleaned.upper()
        if not any(upper.startswith(prefix) for prefix in ALLOWED_SQL_PREFIXES):
            raise SecurityError(
                f"Disallowed query type. Only read-only queries ({', '.join(ALLOWED_SQL_PREFIXES)}) are permitted."
            )

        for pattern in FORBIDDEN_SQL_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                raise SecurityError(
                    f"Forbidden SQL keyword or pattern detected in query: '{pattern}'."
                )

    def is_sensitive_operation(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Classifies if a tool call requires Human-in-the-Loop approval gate."""
        spec = TOOL_PERMISSION_MATRIX.get(tool_name)
        if spec and spec.get("requires_approval"):
            return True, f"Tool '{tool_name}' requires human authorization according to permission matrix."
        if tool_name == "apply_approved_patch":
            return True, "Modifying repository source code requires human authorization."
        if tool_name == "propose_file_patch" and arguments.get("auto_apply", False):
            return True, "Direct modification of repository files requires explicit human sign-off."
        if tool_name == "run_test_suite" and arguments.get("destructive", False):
            return True, "Running potentially destructive tests requires approval."
        return False, ""


    def check_and_record_idempotency(self, idempotency_key: str, action_summary: str) -> bool:
        """Returns True if already processed (preventing duplicate execution)."""
        if not idempotency_key:
            return False
        if idempotency_key in self._applied_idempotency_keys:
            return True
        self._applied_idempotency_keys[idempotency_key] = {
            "summary": action_summary,
            "timestamp": os.times()[4]
        }
        return False

def redact_secrets(data: Any) -> Any:
    """Recursively redacts API keys, credentials, and tokens from dicts, lists, strings."""
    if isinstance(data, str):
        redacted = SECRET_REGEX.sub("[REDACTED_SECRET]", data)
        # Redact known password patterns
        return redacted
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if any(term in k.lower() for term in ("secret", "token", "password", "key", "auth")):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = redact_secrets(v)
        return new_dict
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data
