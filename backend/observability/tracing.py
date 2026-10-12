import time
import uuid
from typing import Any, Dict, List, Optional
from backend.database.connection import SessionLocal
from backend.database.models import TraceSpan, AuditEvent

# Pricing per million tokens (standardized baseline for benchmarks)
COST_PER_MILLION_INPUT = 0.15
COST_PER_MILLION_OUTPUT = 0.60

def estimate_tokens(text: Any) -> int:
    """Rough heuristic estimate of tokens (1 token ~= 4 chars)."""
    if text is None:
        return 0
    str_val = str(text)
    return max(1, len(str_val) // 4)

class Tracer:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.spans: List[Dict[str, Any]] = []
        self._active_spans: Dict[str, Dict[str, Any]] = {}

    def start_span(self, node_name: str, inputs: Optional[Dict[str, Any]] = None, parent_span_id: Optional[str] = None) -> str:
        span_id = f"span-{uuid.uuid4().hex[:10]}"
        now = time.time()
        span_data = {
            "id": span_id,
            "task_id": self.task_id,
            "parent_span_id": parent_span_id,
            "node_name": node_name,
            "start_time": now,
            "inputs": inputs or {},
            "status": "running",
            "tokens_in": estimate_tokens(inputs)
        }
        self._active_spans[span_id] = span_data
        return span_id

    def end_span(self, span_id: str, outputs: Optional[Dict[str, Any]] = None, status: str = "success", error: Optional[str] = None) -> Dict[str, Any]:
        if span_id not in self._active_spans:
            return {}

        span_data = self._active_spans.pop(span_id)
        now = time.time()
        duration_ms = round((now - span_data["start_time"]) * 1000, 2)
        tokens_out = estimate_tokens(outputs)
        tokens_in = span_data.get("tokens_in", 0)

        cost = (tokens_in / 1_000_000 * COST_PER_MILLION_INPUT) + (tokens_out / 1_000_000 * COST_PER_MILLION_OUTPUT)

        span_data.update({
            "end_time": now,
            "duration_ms": duration_ms,
            "status": "error" if error else status,
            "outputs": outputs or {},
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
            "error": error
        })

        self.spans.append(span_data)

        # Persist to database
        self._persist_span(span_data)
        return span_data

    def _persist_span(self, span_dict: Dict[str, Any]):
        try:
            db = SessionLocal()
            span_record = TraceSpan(
                id=span_dict["id"],
                task_id=span_dict["task_id"],
                parent_span_id=span_dict.get("parent_span_id"),
                node_name=span_dict["node_name"],
                start_time=span_dict["start_time"],
                end_time=span_dict["end_time"],
                duration_ms=span_dict["duration_ms"],
                status=span_dict["status"],
                inputs=span_dict["inputs"],
                outputs=span_dict["outputs"],
                tokens_in=span_dict["tokens_in"],
                tokens_out=span_dict["tokens_out"],
                cost_usd=span_dict["cost_usd"]
            )
            db.add(span_record)
            db.commit()
            db.close()
        except Exception:
            pass

    def record_audit(self, event_type: str, tool_name: Optional[str], parameters: Any, outcome: str, metadata: Any = None):
        try:
            db = SessionLocal()
            audit_record = AuditEvent(
                task_id=self.task_id,
                event_type=event_type,
                tool_name=tool_name,
                parameters=parameters,
                outcome=outcome,
                metadata_json=metadata
            )
            db.add(audit_record)
            db.commit()
            db.close()
        except Exception:
            pass

    def export_langsmith_trace(self) -> Dict[str, Any]:
        """Export trace in LangSmith / OpenTelemetry compatible format."""
        total_tokens_in = sum(s["tokens_in"] for s in self.spans)
        total_tokens_out = sum(s["tokens_out"] for s in self.spans)
        total_cost = sum(s["cost_usd"] for s in self.spans)
        total_latency = sum(s["duration_ms"] for s in self.spans)

        return {
            "trace_id": self.task_id,
            "root_run_name": "agentops_nexus_workflow",
            "start_time": self.spans[0]["start_time"] if self.spans else time.time(),
            "end_time": self.spans[-1]["end_time"] if self.spans else time.time(),
            "total_latency_ms": round(total_latency, 2),
            "tokens": {
                "input": total_tokens_in,
                "output": total_tokens_out,
                "total": total_tokens_in + total_tokens_out
            },
            "estimated_cost_usd": round(total_cost, 6),
            "spans": self.spans
        }

# Global tracer registry by task_id
_TRACERS: Dict[str, Tracer] = {}

def get_tracer(task_id: str) -> Tracer:
    if task_id not in _TRACERS:
        _TRACERS[task_id] = Tracer(task_id)
    return _TRACERS[task_id]
