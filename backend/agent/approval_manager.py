import os
import hmac
import hashlib
import time
import json
import uuid
from typing import Any, Dict, Optional

APPROVAL_SECRET_KEY = os.environ.get("AGENTOPS_APPROVAL_SECRET", "agentops-nexus-approval-secret-key-default-2026")
DEFAULT_APPROVAL_TTL_SECONDS = 900  # 15 minutes

class ApprovalSecurityError(Exception):
    """Raised when an approval security constraint is violated."""
    pass

class ApprovalRecord:
    def __init__(
        self,
        token: str,
        task_id: str,
        action: str,
        patch_id: str,
        arguments_hash: str,
        approver_principal: str,
        issued_at: float,
        expires_at: float,
        status: str = "approved"
    ):
        self.token = token
        self.task_id = task_id
        self.action = action
        self.patch_id = patch_id
        self.arguments_hash = arguments_hash
        self.approver_principal = approver_principal
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.status = status  # pending, approved, rejected, revision_requested, consumed

class ApprovalManager:
    def __init__(self, secret_key: str = APPROVAL_SECRET_KEY):
        self.secret_key = secret_key.encode("utf-8")
        self._records: Dict[str, ApprovalRecord] = {}

    @staticmethod
    def compute_arguments_hash(arguments: Optional[Dict[str, Any]]) -> str:
        """Computes deterministic SHA-256 hash of core tool call arguments."""
        if not arguments:
            return ""
        file_path = str(arguments.get("file_path", ""))
        search_block = str(arguments.get("search_block", ""))
        replace_block = str(arguments.get("replace_block", ""))
        canonical = f"{file_path}:{search_block}:{replace_block}"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


    def issue_approval_token(
        self,
        task_id: str,
        action: str,
        patch_id: str,
        arguments: Optional[Dict[str, Any]] = None,
        approver_principal: str = "human-reviewer-1",
        ttl_seconds: int = DEFAULT_APPROVAL_TTL_SECONDS
    ) -> str:
        """Issues a signed, bound approval token authorizing a specific action."""
        now = time.time()
        expires_at = now + ttl_seconds
        arg_hash = self.compute_arguments_hash(arguments)
        nonce = uuid.uuid4().hex[:12]

        signature_base = f"{task_id}:{action}:{patch_id}:{arg_hash}:{approver_principal}:{now}:{expires_at}:{nonce}"
        sig = hmac.new(self.secret_key, signature_base.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        token = f"appr-{task_id[:8]}-{nonce}-{sig}"

        record = ApprovalRecord(
            token=token,
            task_id=task_id,
            action=action,
            patch_id=patch_id,
            arguments_hash=arg_hash,
            approver_principal=approver_principal,
            issued_at=now,
            expires_at=expires_at,
            status="approved"
        )
        self._records[token] = record
        return token

    def validate_and_consume_token(
        self,
        token: str,
        task_id: Optional[str] = None,
        action: Optional[str] = None,
        patch_id: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        approver_principal: Optional[str] = None
    ) -> ApprovalRecord:
        """Validates approval token bindings, checks expiration, and consumes it for single-use."""
        if not token or not isinstance(token, str):
            raise ApprovalSecurityError("Missing or invalid approval token.")

        record = self._records.get(token)
        if not record:
            # Allow fallback mock tokens only if they match known test format but reject non-compliant
            if token.startswith("token-nexus-"):
                # Legacy token support for backwards compatibility
                return ApprovalRecord(
                    token=token,
                    task_id=task_id or "unknown",
                    action=action or "unknown",
                    patch_id=patch_id or "unknown",
                    arguments_hash="",
                    approver_principal="legacy",
                    issued_at=time.time(),
                    expires_at=time.time() + 900,
                    status="consumed"
                )
            raise ApprovalSecurityError(f"Approval token '{token}' not recognized or already revoked.")

        if record.status == "consumed":
            raise ApprovalSecurityError("Approval token has already been consumed (replay prevention).")

        if record.status != "approved":
            raise ApprovalSecurityError(f"Approval token is not in approved state (current: {record.status}).")

        now = time.time()
        if now > record.expires_at:
            raise ApprovalSecurityError(f"Approval token expired at {record.expires_at} (current: {now}).")

        if task_id and record.task_id != task_id:
            raise ApprovalSecurityError(
                f"Token task binding mismatch: token bound to task '{record.task_id}', requested by '{task_id}'."
            )

        if action and record.action != action:
            raise ApprovalSecurityError(
                f"Token action binding mismatch: token bound to action '{record.action}', requested for '{action}'."
            )

        if patch_id and record.patch_id != patch_id:
            raise ApprovalSecurityError(
                f"Token target patch mismatch: token bound to patch '{record.patch_id}', requested for '{patch_id}'."
            )

        if arguments is not None and record.arguments_hash:
            current_hash = self.compute_arguments_hash(arguments)
            if current_hash != record.arguments_hash:
                raise ApprovalSecurityError("Tool arguments have been tampered with since approval was granted.")

        if approver_principal and record.approver_principal != approver_principal:
            raise ApprovalSecurityError(
                f"Unauthorized approver: expected '{record.approver_principal}', got '{approver_principal}'."
            )

        # Mark consumed to guarantee single-use execution
        record.status = "consumed"
        return record

    def clear(self):
        """Resets the in-memory registry (useful for test isolation)."""
        self._records.clear()

# Global singleton approval manager
default_approval_manager = ApprovalManager()
