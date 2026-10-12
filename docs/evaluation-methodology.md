# AgentOps Nexus: Evaluation Methodology & Benchmark Specification

This document details the evaluation framework, measurement definitions, and experimental methodology used to benchmark AgentOps Nexus across 40 standardized test cases.

---

## 1. Metrics Taxonomy

To maintain engineering credibility, all metrics reported by the evaluation suite are partitioned into two strict categories:

### A. Empirical Measurements (Instrumented Directly)
These values are measured at runtime from real execution traces, filesystem state checks, and process telemetry:

1. **Task Success Rate (`task_success_rate`)**:
   - Target: `> 90%`
   - Calculation: Percentage of tasks meeting their objective criteria. For normal tasks, this requires successful completion and verification; for permission-denial tasks, this requires clean policy blocking without executing unauthorized side effects.
2. **Tool-Selection Accuracy (`tool_selection_accuracy`)**:
   - Target: `> 95%`
   - Calculation: Precision and recall of planned tool sequences against ground-truth expected tools in the dataset.
3. **Approval Compliance Rate (`approval_compliance_rate`)**:
   - Target: `100%`
   - Invariant: Evaluates three distinct security conditions:
     - **Pre-Approval Invariance**: Sandbox files on disk are verified to be unmodified prior to human approval.
     - **Rejection Preservation**: When human reviewers decline, the operation is terminated and files remain strictly unmodified.
     - **Gated Execution**: Write mutations are only applied after receiving an authorized resumption command with a valid cryptographic token.
4. **Retry Recovery Rate (`retry_recovery_rate`)**:
   - Target: `> 85%`
   - Measurement: Verified using an explicit `retry_history` state array. The system tracks real retry transitions with exponential backoff and measures recovery to successful completion.
5. **End-to-End Latency & P95 (`latency.avg_ms`, `latency.p95_ms`)**:
   - Targets: `< 2500ms` average, `< 4500ms` P95.
   - Measurement: High-resolution monotonic timers wrapping graph initialization, execution, and state checkpointing.

### B. Heuristic Estimates (Model Approximations)
1. **Token Consumption (`tokens.total`, `tokens.avg_per_task`)**:
   - Labeled: `ESTIMATED`
   - Basis: Offline heuristic calculation derived from benchmark prompt length, message history, and tool payload tokens.
2. **Evaluation Cost (`cost.total_usd`, `cost.avg_per_task_usd`)**:
   - Labeled: `ESTIMATED`
   - Basis: Standard blended pricing heuristics ($0.15/1M input tokens, $0.60/1M output tokens).

---

## 2. Test Dataset Composition

The benchmark suite consists of 40 test cases across 6 operational categories:

| Category | Count | Focus |
| :--- | :--- | :--- |
| `normal_task` | 13 | Code exploration, test execution, database queries, and multi-step investigation. |
| `ambiguous_request` | 5 | Ambiguous user requests requiring status queries and safe exploration. |
| `invalid_input` | 5 | Malformed inputs, missing files, non-existent search blocks, and expired patch tokens. |
| `transient_failure` | 5 | Injected network timeouts and connection resets testing bounded retries with backoff. |
| `permission_denial` | 8 | Path traversal attacks, SQL injection attempts, and unauthorized mutation calls. |
| `approval_required` | 4 | Human-in-the-loop review, reviewer rejection, reviewer revision, and patch replay prevention. |

---

## 3. Security Threat Model & Invariants

AgentOps Nexus implements a zero-trust model between LLM agents and system tools:

1. **Path Traversal Boundary**: All file operations validate canonical real paths against the sandbox root. Null bytes, relative escape sequences (`../`), and absolute host system paths are rejected before filesystem access.
2. **SQL Injection Jail**: Database queries are parsed and checked against a strict read-only grammar. Multiple semicolons, `DROP`, `DELETE`, `INSERT`, `UPDATE`, and `ATTACH` commands are denied at the MCP layer.
3. **Idempotency & Replay Prevention**: Every state mutation requires an idempotency key. Duplicate requests within the cache window return cached outcomes without re-executing writes.
4. **Human Review Gate**: Destructive operations raise an interrupt checkpoint in LangGraph. State is preserved in durable SQLite storage, allowing safe resumption or cancellation.
