import math
import random
import uuid
from typing import Any, Dict

NON_TRANSIENT_ERRORS = [
    "securityerror",
    "access denied",
    "escapes sandbox boundary",
    "forbidden sql",
    "validationerror",
    "syntax error",
    "missing argument",
    "unknown or expired patch id",
    "file does not exist",
    "unauthorized"
]

TRANSIENT_ERRORS = [
    "timeout",
    "connection reset",
    "temporary failure",
    "rate limit",
    "transient_simulated_error",
    "server busy",
    "503",
    "lock"
]

def is_transient_failure(error_msg: str) -> bool:
    """Classify if an error is transient (safe to retry) or deterministic (fail-fast)."""
    if not error_msg:
        return False
    lower_msg = error_msg.lower()

    # If matches explicit non-transient rule, never retry
    for non_trans in NON_TRANSIENT_ERRORS:
        if non_trans in lower_msg:
            return False

    # Check for transient patterns
    for trans in TRANSIENT_ERRORS:
        if trans in lower_msg:
            return True

    return False

def calculate_backoff_delay(retry_count: int, base_delay: float = 0.2, factor: float = 1.5, max_delay: float = 3.0) -> float:
    """Calculates exponential backoff delay with jitter."""
    calculated = base_delay * (factor ** retry_count)
    jitter = random.uniform(0.05, 0.15)
    return min(max_delay, calculated + jitter)

def can_retry(error_msg: str, current_retries: int, max_retries: int = 3) -> bool:
    """Bounded retry decision."""
    if current_retries >= max_retries:
        return False
    return is_transient_failure(error_msg)

def is_sensitive_step(step: Dict[str, Any]) -> bool:
    """Check if tool call needs human approval."""
    if not step:
        return False
    tool = step.get("tool", "")
    if tool in ("apply_approved_patch", "execute_approved_action"):
        return True
    if step.get("is_sensitive", False):
        return True
    args = step.get("arguments", {})
    if args.get("is_sensitive", False) or args.get("auto_apply", False):
        return True
    return False

def generate_approval_token(task_id: str) -> str:
    """Generate high-entropy token validating human sign-off."""
    return f"token-nexus-{task_id[:8]}-{uuid.uuid4().hex[:12]}"
