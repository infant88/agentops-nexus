# AgentOps Nexus: Evaluation Methodology and Benchmark Specification

This document details the evaluation framework, measurement formulas, dataset composition, and experimental methodology used to benchmark AgentOps Nexus across 40 standardized test cases.

---

## 1. Metrics Taxonomy and Formulas

To maintain engineering credibility, all metrics reported by the evaluation suite are partitioned into two categories:

### A. Empirical Measurements (Instrumented Directly)

1. **Task Success Rate (`task_success_rate`)**:
   - **Formula**: `(Successful Tasks / Total Eligible Tasks) * 100`
   - **Target**: `>= 90.0%`
   - **Definition**: For standard tasks, success requires verified resolution of the task objective. For permission-denial tasks, success requires clean policy blocking with zero unauthorized side effects. For rejection tasks, success requires workflow termination with zero file writes.

2. **Tool-Selection Accuracy (`tool_selection_accuracy`)**:
   - **Formula**: `(Correct Tool Decisions / Scored Tool Decisions) * 100`
   - **Target**: `>= 95.0%`
   - **Definition**: Measures whether the agent called the correct tool for the task. In cases where an action is unauthorized or rejected by a reviewer, halting without executing the tool is counted as a 100% correct decision. If a case produces no tool decisions, it is handled explicitly rather than assigned an optimistic default.

3. **Approval Compliance Rate (`approval_compliance_rate`)**:
   - **Formula**: `(Sensitive Actions Correctly Gated / All Sensitive-Action Tests) * 100`
   - **Target**: `== 100.0%` (Strict enforcement)
   - **Invariant Tested**:
     - **Pre-Approval Invariance**: Sandbox repository files are verified to be unmodified prior to human approval.
     - **Rejection Preservation**: When human reviewers decline, the operation is terminated and files remain strictly unmodified.
     - **Cryptographic Gate**: Actions execute only after receiving an authorized resumption command with a valid cryptographic token.

4. **Retry Recovery Rate (`retry_recovery_rate`)**:
   - **Formula**: `(Transient Cases Recovered via Retry / All Eligible Transient Cases) * 100`
   - **Target**: `>= 85.0%`
   - **Definition**: Verified using recorded attempt events in `retry_history`. The system tracks real retry transitions with exponential backoff and measures recovery to final success.

5. **End-to-End Latency and P95 (`latency.avg_ms`, `latency.p95_ms`)**:
   - **Targets**: `<= 2500.0 ms` average, `<= 4500.0 ms` P95
   - **Measurement**: Monotonic wall-clock durations captured via Python `time.perf_counter()`, capturing planning, tool invocation, and state checkpointing.

### B. Resource Consumption and Cost Disclosure

1. **Token Consumption (`tokens.total`, `tokens.avg_per_task`)**:
   - **Type**: Heuristic Estimate
   - **Method**: Character length approximation (`~4 characters per token`) over prompts, tool payloads, and workflow outputs.
   - **Honesty Disclosure**: These values represent offline heuristic estimates rather than live provider-metered billing counters.

2. **Evaluation Cost (`cost.total_usd`, `cost.avg_per_task_usd`)**:
   - **Type**: Heuristic Estimate
   - **Method**: Blended reference model pricing ($0.15 per 1M input tokens, $0.60 per 1M output tokens).

---

## 2. Test Dataset Composition

The benchmark dataset (`backend/evaluation/dataset.jsonl`) contains 40 structured test cases across 6 operational categories:

| Category | Count | Primary Objective | Success Criteria |
| :--- | :--- | :--- | :--- |
| `normal_task` | 13 | Code exploration, test execution, database queries, and multi-step investigation | Tasks complete, tests verify clean fix, metrics recorded |
| `ambiguous_request` | 5 | Underspecified user prompts ("fix everything", "check billing") | Agent executes safe read-only exploration without destructive actions |
| `invalid_input` | 5 | Empty SQL strings, non-existent files, missing diff blocks, expired patch IDs | Clean validation error raised without unhandled crashes |
| `transient_failure` | 5 | Injected connection timeouts, lock errors, and 503 service busy codes | Bounded retries engage with exponential backoff, recovering successfully |
| `permission_denial` | 8 | Path traversal (`../../`), destructive SQL (`DROP TABLE`), unauthenticated writes | Operation blocked at server boundary with zero disk or database side effects |
| `approval_required` | 4 | Human approval, reviewer rejection, revision request, and patch idempotency | Approval interrupt pause enforced, rejection leaves disk intact, replay blocked |

---

## 3. Transient Error Simulation

Transient failures are simulated via deterministic test flags in task state:
- When `simulate_transient_error` is present, downstream tools trigger simulated network timeouts on initial attempts.
- The workflow routes through `handle_retry`, calculates exponential backoff delay with jitter, appends an event to `retry_history`, and re-executes.
- Success on subsequent attempts is measured by comparing `retry_history` length with task outcome.

---

## 4. Reproducibility and Environment Metadata

Every benchmark run records:
- **Git Commit SHA**: Captures the exact code version evaluated.
- **Dataset Content Hash**: SHA-256 hash of `dataset.jsonl` verifying dataset immutability.
- **Python and OS Environment**: Complete platform and interpreter metadata.
- **Deterministic Evaluation**: Tests run locally against an isolated sandbox without external network dependencies, ensuring zero run-to-run flakiness.

---

## 5. Known Limitations and Potential Sources of Bias

1. **Deterministic Agent Simulation**: To provide deterministic, reproducible CI benchmarks without incurring API costs or rate limit failures, LLM responses are simulated through rule-based agent nodes.
2. **Offline Token Estimation**: Token counts are computed heuristically from character lengths rather than live BPE tokenizers.
3. **Single-Process Environment**: Benchmarks execute in a single Python process environment. Distributed latency and network partitions are outside the evaluation scope.
