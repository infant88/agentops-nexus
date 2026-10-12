from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

class PlanStep(TypedDict):
    step_id: int
    description: str
    tool: str
    arguments: Dict[str, Any]
    is_sensitive: bool
    status: str  # pending, running, completed, failed, skipped

class AgentState(TypedDict):
    task_id: str
    objective: str
    plan: List[Dict[str, Any]]
    current_step_index: int
    current_tool_call: Optional[Dict[str, Any]]
    last_tool_output: Optional[Dict[str, Any]]
    last_error: Optional[str]
    is_transient_error: bool
    retry_count: int
    max_retries: int
    requires_approval: bool
    approval_status: str  # none, pending, approved, rejected, revision_requested
    approval_payload: Optional[Dict[str, Any]]
    human_feedback: Optional[str]
    approval_token: Optional[str]
    idempotency_key: Optional[str]
    execution_history: List[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    failure_recovery: Optional[Dict[str, Any]]
    evaluation_metrics: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    status: str  # pending, planning, executing, waiting_approval, approved, rejected, verified, completed, failed
