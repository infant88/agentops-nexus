import os
import re
from typing import Any, Dict, Tuple

FORBIDDEN_SQL_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|TRUNCATE|EXEC|VACUUM|GRANT|REVOKE)\b",
    r";\s*\S+",  # Disallow multiple chained queries
    r"--",        # Disallow SQL comment injection
]

ALLOWED_SQL_PREFIXES = ("SELECT", "PRAGMA TABLE_INFO", "PRAGMA INDEX_LIST", "EXPLAIN")

SECRET_REGEX = re.compile(
    r"(sk-[a-zA-Z0-9_\-]{16,}|bearer\s+[a-zA-Z0-9_\-\.]{16,}|ghp_[a-zA-Z0-9]{20,}|password\s*[:=]\s*\S+)",
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

    def validate_file_path(self, relative_or_abs_path: str) -> str:
        """Ensures file access stays strictly confined within repo_root."""
        if "\0" in relative_or_abs_path:
            raise SecurityError("Null byte injection detected in file path.")

        # If relative, anchor to repo_root
        if not os.path.isabs(relative_or_abs_path):
            target = os.path.join(self.repo_root, relative_or_abs_path)
        else:
            target = relative_or_abs_path

        resolved = os.path.realpath(target)

        # Path traversal jail check
        common = os.path.commonpath([resolved, self.repo_root])
        if common != self.repo_root:
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
