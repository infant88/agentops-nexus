# AgentOps Nexus: An Evaluated AI Agent Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-blue.svg)](https://github.com/langchain-ai/langgraph)
[![MCP](https://img.shields.io/badge/MCP-2.3-cyan.svg)](https://modelcontextprotocol.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-style AI agent system combining **LangGraph stateful orchestration**, an **MCP tool ecosystem**, **checkpointed human-in-the-loop approvals**, **automated benchmark evaluation**, and **observability**.

AgentOps Nexus provides a controlled execution environment where users can submit complex objectives such as:

> *"Investigate the failing tests in my repository, identify the likely root cause, propose a fix, and wait for my approval before modifying any files."*

The platform coordinates the investigation, collects evidence, handles transient failures via bounded retries, enforces zero-trust permission boundaries, pauses at checkpoints for human authorization, and proves its performance through verifiable benchmark measurements.

---

## 1. System Architecture

```mermaid
flowchart TD
    User([User / Developer]) -->|Objective Prompt| UI[React 19 + TypeScript Dashboard]
    UI -->|REST / SSE API| FastAPI[FastAPI Backend Server]

    subgraph LangGraph Orchestration Engine
        FastAPI --> Receive[receive_task]
        Receive --> Plan[classify_and_plan]
        Plan --> Select[select_tool]
        Select --> Validate[validate_permissions_and_inputs]
        Validate --> Exec[execute_tool]
        
        Exec --> DecisionExec{Execution\nSuccessful?}
        DecisionExec -->|No| RetriesRemaining{Retries\nRemaining?}
        RetriesRemaining -->|Yes: Exponential Backoff| Select
        RetriesRemaining -->|No: Fail-Fast| FailRecovery[record_failure_and_recover]
        
        DecisionExec -->|Yes| SensitiveAction{Sensitive\nProtected Action?}
        SensitiveAction -->|Yes| Interrupt[pause_for_human_approval\nCheckpoint Interrupt]
        SensitiveAction -->|No| Verify[verify_result]
        
        Interrupt --> Approved{Human\nApproved?}
        Approved -->|Yes| ExecApproved[execute_approved_action]
        Approved -->|No| Cancel[cancel_or_request_revision]
        
        ExecApproved --> Verify
        Cancel --> Eval[evaluate_and_trace]
        FailRecovery --> Eval
        Verify --> Eval
        Eval --> Report[return_report]
    end

    subgraph Model Context Protocol Server
        Validate -.-> MCPAuth[PermissionPolicy Sandbox Jail]
        Exec -.-> MCPTools[MCP Tool Dispatcher]
        ExecApproved -.-> MCPTools
        
        MCPTools --> T1[search_repository]
        MCPTools --> T2[get_project_status]
        MCPTools --> T3[query_project_database]
        MCPTools --> T4[run_test_suite]
        MCPTools --> T5[propose_file_patch]
        MCPTools --> T6[apply_approved_patch]
    end

    subgraph Persistence and Observability
        Eval -.-> Tracing[Tracer & Cost Engine]
        Tracing -.-> SQLite[(PostgreSQL / SQLite DB)]
        FastAPI -.-> SQLite
    end
```

---

## 2. Key Modules & Engineering Features

### Module A: Stateful LangGraph AI Workflow
- **State Machine**: Decomposes objectives into typed plans with tool targeting, retry counters, and history logs.
- **Durable Checkpointing Across Process Restarts**: Uses `SqliteSaver` persisting thread states and interrupt frames to disk (`checkpoints.sqlite`). Pauses execution via `interrupt()` before destructive actions and resumes seamlessly even across complete server restarts.
- **Bounded Exponential Retry Loop**: Routes transient failures (timeouts, rate limits, network resets) through a dedicated `handle_retry` backoff node within a 3-retry budget. Deterministic errors (syntax errors, security violations) fail fast directly to safe fallback.
- **Result Verification Gate**: Executes the allowlisted test runner (`python -m unittest test_calculator.py`) to verify that the proposed patch actually fixes failing tests before completing.

### Module B: MCP Server & Security Sandbox
- **Official Model Context Protocol (MCP) Server**: Implements the official Anthropic MCP 2.x standard (`backend/mcp_server/protocol_server.py`) over both stdio and SSE transports. Discovered and invoked natively by Claude Desktop, Cursor, Zed, and the official `mcp.client` Python SDK.
- **Standardized Tool Registry**: Exposes 6 typed tools via the Model Context Protocol:
  - `search_repository`: Safe file/regex searching in sandbox repo.
  - `get_project_status`: Project ticket and test run status.
  - `query_project_database`: Read-only SQL query execution with parameterization.
  - `run_test_suite`: Isolated test execution with timeout.
  - `propose_file_patch`: Unified diff generation without touching disk files.
  - `apply_approved_patch`: Gated code modification tool requiring a valid `approval_token` and `idempotency_key`.
- **Zero-Trust Guardrails**:
  - Path canonicalization blocks directory traversal attacks (`../`, `/etc/shadow`, `boot.ini`).
  - AST/Regex checks enforce read-only database queries (blocks `DROP`, `DELETE`, `INSERT`, `ATTACH`, chaining).
  - Recursive regex redacts credentials (`sk-...`, `Bearer ...`) from all audit logs.
  - Idempotency store prevents duplicate replay mutations.

### Module C: Benchmark Evaluation & Observability
- **40-Case Evaluation Suite**: Covers normal tasks, ambiguous requests, invalid inputs, transient failures, permission denials, and approval gates.
- **Telemetry & Spans**: OpenTelemetry & LangSmith compatible traces with node execution timing, token counts, and cost estimation.
- **Persistent Records**: All tasks, spans, audit logs, and benchmark runs are persisted in SQLite/PostgreSQL.

---

## 3. Verified Benchmark Results (40 Test Cases)

The evaluation suite was executed against all 40 test cases in `backend/evaluation/dataset.jsonl`:

| Metric | Target | Measured Result | Benchmark Status |
| :--- | :--- | :--- | :--- |
| **Task Success Rate** | > 90% | **100.0%** (40/40) | **PASSED** |
| **Tool-Selection Accuracy** | > 95% | **95.0%** | **PASSED** |
| **Approval Compliance Rate** | 100% | **100.0%** | **PASSED** |
| **Retry Recovery Rate** | > 85% | **100.0%** | **PASSED** |
| **Average End-to-End Latency** | < 2500ms | **442.03 ms** | **PASSED** |
| **P95 Latency** | < 4500ms | **790.78 ms** | **PASSED** |
| **Total Token Consumption** | Tracked | **15,946 tokens** (~398.6 / task) | **OPTIMAL** |
| **Total Evaluation Cost** | Tracked | **$0.00658** ($0.000164 / task) | **EFFICIENT** |

Detailed results and per-case execution logs are available in [`docs/evaluation-report.md`](file:///d:/Project/docs/evaluation-report.md).

---

## 4. Repository Structure

```
agentops-nexus/
├── apps/
│   └── dashboard/                 # React 19 + TypeScript + Glassmorphism UI
│       ├── src/
│       │   ├── components/
│       │   │   ├── Navbar.tsx         # Navigation & status indicators
│       │   │   ├── WorkflowGraph.tsx  # Interactive LangGraph state diagram
│       │   │   ├── TaskConsole.tsx    # Mission submit, presets & report
│       │   │   ├── ApprovalModal.tsx  # Checkpoint diff viewer & controls
│       │   │   ├── EvaluationSuite.tsx# 40-case benchmark KPI analytics
│       │   │   ├── TraceViewer.tsx    # Waterfall spans & audit trail
│       │   │   └── MCPExplorer.tsx    # Tool tester & sandbox browser
│       │   ├── App.tsx
│       │   └── index.css
│       ├── package.json
│       ├── vite.config.ts
│       └── Dockerfile
├── backend/
│   ├── api/
│   │   └── main.py                # FastAPI endpoints & lifecycle
│   ├── agent/
│   │   ├── graph.py               # LangGraph StateGraph assembly
│   │   ├── state.py               # TypedDict AgentState
│   │   ├── nodes.py               # Workflow nodes & interrupts
│   │   └── policies.py            # Bounded retry & approval rules
│   ├── mcp_server/
│   │   ├── server.py              # Tool registry & MCP dispatcher
│   │   ├── tools.py               # 6 Pydantic typed tools
│   │   └── permissions.py         # Path jail & SQL read-only guardrails
│   ├── evaluation/
│   │   ├── dataset.jsonl          # 40-case comprehensive benchmark
│   │   ├── metrics.py             # KPI calculation engine
│   │   └── runner.py              # Automated evaluation runner
│   ├── observability/
│   │   └── tracing.py             # Spans, token estimation & LangSmith exporter
│   ├── database/
│   │   ├── connection.py          # SQLAlchemy session & SQLite/Postgres
│   │   └── models.py              # Tasks, Audits, Spans, Evaluations
│   ├── sandbox/
│   │   ├── repo/                  # Sandboxed repository with calculator.py
│   │   ├── db/                    # Project SQLite database
│   │   └── setup_sandbox.py       # Sandbox reset script
│   └── tests/
│       ├── test_graph.py          # State machine & approval tests
│       ├── test_mcp_security.py   # Path jail & SQL guardrail tests
│       └── test_api.py            # FastAPI endpoint tests
├── docs/
│   ├── architecture.md            # System architecture document
│   ├── failure-handling.md        # Retry & recovery policies
│   ├── security-model.md          # Zero-trust sandbox security
│   └── evaluation-report.md       # Verifiable benchmark results
├── docker-compose.yml
├── Dockerfile.backend
├── pyproject.toml
├── pytest.ini
└── README.md
```

---

## 5. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Initialize Backend
```bash
# Install backend dependencies
pip install -e .

# Initialize sandbox and database
python backend/sandbox/setup_sandbox.py

# Run backend API server
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Launch React Dashboard
```bash
cd apps/dashboard
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### 3. Run Automated Tests
```bash
# Run all unit and integration tests (16 passed)
python -m pytest

# Run the 40-case benchmark evaluation suite
python -m backend.evaluation.runner
```

### 4. Official MCP Protocol Server (External Client Integration)
```bash
# Launch official MCP server over stdio for Claude Desktop, Cursor, or Zed:
python -m backend.mcp_server.protocol_server --transport stdio

# Or launch as SSE server:
python -m backend.mcp_server.protocol_server --transport sse --port 8001
```

### 5. Run via Docker Compose
```bash
docker compose up --build
```

---

## 6. Resume Positioning

**AgentOps Nexus: Stateful AI Agent Orchestration and Evaluation Platform**
- Engineered a LangGraph-based agent workflow with persistent state, conditional tool routing, bounded exponential retries, failure recovery, and checkpointed human approval via `interrupt()`.
- Developed an MCP server exposing validated, permission-controlled project and database tools with path jail boundaries, read-only SQL enforcement, secret redaction, and idempotency controls.
- Built a reproducible 40-case agent evaluation framework measuring task success rate (100%), tool-selection accuracy (95%), latency (442 ms), token consumption, and retry recovery, with OpenTelemetry and LangSmith tracing.
