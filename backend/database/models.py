import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from backend.database.connection import Base

class TaskRecord(Base):
    __tablename__ = "task_records"

    id = Column(String(64), primary_key=True, index=True)
    objective = Column(Text, nullable=False)
    status = Column(String(32), default="pending", index=True)  # pending, planning, running, waiting_approval, approved, rejected, completed, failed
    plan = Column(JSON, nullable=True)
    current_step = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(32), default="none")  # none, pending, approved, rejected, revision_requested
    approval_payload = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String(64), nullable=False)  # tool_call, validation, approval_request, approval_decision, retry, failure, verification
    tool_name = Column(String(64), nullable=True)
    parameters = Column(JSON, nullable=True)  # redacted secrets
    outcome = Column(String(32), nullable=False)  # success, error, blocked, pending
    metadata_json = Column(JSON, nullable=True)

class TraceSpan(Base):
    __tablename__ = "trace_spans"

    id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    parent_span_id = Column(String(64), nullable=True)
    node_name = Column(String(64), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration_ms = Column(Float, nullable=False)
    status = Column(String(32), default="success")  # success, error, paused
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(64), primary_key=True, index=True)
    run_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total_cases = Column(Integer, default=0)
    successful_cases = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    tool_accuracy = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    retry_recovery_rate = Column(Float, default=0.0)
    approval_compliance_rate = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    results_summary = Column(JSON, nullable=True)
