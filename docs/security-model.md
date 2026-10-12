# AgentOps Nexus: Security Architecture and Safeguard Model

MCP standardizes tool communication between LLMs and tools, but MCP alone does not provide authorization, sandboxing, or safe execution. AgentOps Nexus implements a multi-layer zero-trust security architecture.

---

## 1. System Trust Boundaries

The system architecture partitions operations into four distinct security trust boundaries:

```
[Untrusted Input / Client UI]
             |
             v (Boundary 1: Task Classification & Planning)
   [LangGraph Orchestrator]
             |
             v (Boundary 2: Human Approval Interrupt & Token Issuance)
   [Approval Security Manager]
             |
             v (Boundary 3: Protocol Transport & Input Validation)
      [MCP Server Runtime]
             |
             v (Boundary 4: Sandbox & Resource Isolation)
[Filesystem Sandbox & SQLite DB]
```

1. **Boundary 1 (Planner vs Tools)**: The agent planning prompt is never trusted to enforce security rules. Tool arguments are strictly re-validated at the tool boundary.
2. **Boundary 2 (Human Approval Gate)**: Sensitive write operations raise a LangGraph `interrupt()`, halting graph execution until a valid cryptographically signed authorization token is provided.
3. **Boundary 3 (MCP Protocol Boundary)**: Validates input schemas, enforces per-tool payload size limits, and sanitizes tool routing requests.
4. **Boundary 4 (Local Sandbox Prison)**: Confines file I/O to the authorized workspace root and restricts SQL database access to read-only queries.

---

## 2. Threat Matrix and Defense Enforcements

| Threat Vector | Attack Scenario | Defense Mechanism | Enforcement Point |
| :--- | :--- | :--- | :--- |
| **Path Traversal Escape** | Agent attempts reading `/etc/shadow`, `boot.ini`, or system directories via `../../` or `%2e%2e` | Canonical path resolution (`os.path.realpath`), URL decoding, and cross-drive `commonpath` verification | Server `PermissionPolicy.validate_file_path` |
| **Destructive SQL Injection** | Prompt injection commands `DROP TABLE`, `DELETE`, or stacked queries | Strict prefix validation (`SELECT`, `PRAGMA table_info`, `EXPLAIN`), comment stripping (`--`, `/* */`), and multi-statement blocking | Server `PermissionPolicy.validate_sql` |
| **Unreviewed File Mutation** | Agent modifies production source code autonomously | Mandatory LangGraph checkpoint `interrupt()`; requires HMAC-SHA256 `approval_token` bound to action arguments | `ApprovalManager` and tool boundary in `apply_approved_patch` |
| **Replay and Concurrency Attacks** | Retried operations or concurrent requests accidentally apply duplicate patches twice | High-entropy UUID `idempotency_key` tracking and single-use token consumption | MCP Patch Engine and `PermissionPolicy` |
| **Credential / Token Leakage** | API keys, passwords, or authorization headers leak into logs, exceptions, or tool outputs | Recursive secret redactor masking sensitive regex patterns (`sk-...`, `Bearer ...`, `AKIA...`, `password=...`) | Observability Tracer, Server `call_tool`, and Tool Handlers |
| **Oversized Payload DoS** | Massive SQL or search pattern floods server memory | Per-tool input size limits (e.g. 16KB for SQL, 64KB for patches) | Server `PermissionPolicy.validate_input_size` |

---

## 3. Cryptographic Human Approval Protocol

A workflow that merely pauses is not secure unless protected side effects are cryptographically gated. AgentOps Nexus enforces an HMAC-SHA256 authorization protocol:

1. **Token Generation**: When a sensitive action is proposed, an `ApprovalRecord` is generated with:
   - Unique `task_id` and action identifier (`apply_approved_patch`)
   - SHA-256 hash of core target arguments (`file_path`, `search_block`, `replace_block`)
   - Expiration timestamp (TTL: 15 minutes)
   - Cryptographic signature: `HMAC_SHA256(secret_key, task_id:action:arg_hash:expires_at)`
2. **Pre-Approval Invariance**: Sandbox repositories on disk are verified to be unmodified prior to receiving explicit human approval.
3. **Rejection Blocking**: If a reviewer rejects or requests revision, the graph terminates into a cancelled state and disk content remains strictly intact.
4. **Single-Use Consumption**: Once verified and applied, the token is marked as consumed, preventing replay attacks or token reuse across requests.
5. **Tamper Invalidation**: If tool arguments are altered between approval and execution, the recomputed argument hash mismatches the token signature and execution is immediately blocked.

---

## 4. Path Traversal and Filesystem Confinement

Paths are validated before opening any file descriptor:

```python
def validate_file_path(self, relative_or_abs_path: str) -> str:
    if not relative_or_abs_path:
        raise SecurityError("File path cannot be empty.")

    if "\0" in relative_or_abs_path:
        raise SecurityError("Null byte injection detected in file path.")

    decoded_path = urllib.parse.unquote(relative_or_abs_path)
    if "\0" in decoded_path:
        raise SecurityError("Null byte injection detected in decoded file path.")

    if not os.path.isabs(decoded_path):
        target = os.path.join(self.repo_root, decoded_path)
    else:
        target = decoded_path

    resolved = os.path.realpath(target)

    try:
        common = os.path.commonpath([resolved, self.repo_root])
        if common != self.repo_root:
            raise SecurityError(
                f"Access denied: Path '{relative_or_abs_path}' escapes sandbox boundary '{self.repo_root}'."
            )
    except ValueError:
        # Cross-drive attempts on Windows (e.g. C:\ vs D:\)
        raise SecurityError(
            f"Access denied: Path '{relative_or_abs_path}' escapes sandbox boundary '{self.repo_root}'."
        )

    return resolved
```

---

## 5. SQL Query Guardrails

The database tool enforces read-only access:
- **Allowed Query Prefixes**: Strictly `SELECT`, `PRAGMA table_info`, `PRAGMA index_list`, and `EXPLAIN`.
- **Blocked Mutation Statements**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `REPLACE`, `ATTACH`, `DETACH`, `TRUNCATE`, `EXEC`, `VACUUM`.
- **Comment Injection Filtering**: SQL line comments (`--`) and block comments (`/* ... */`) are rejected to prevent bypass of query structure parsers.
- **System Table Protection**: Queries targeting internal metadata tables (e.g. `sqlite_master`) are rejected.
- **Statement Stacking Prevention**: Chained semicolon statements (`;`) are strictly blocked.

---

## 6. Resilience, Retries, and Persistence Guarantees

- **Error Classification**: Errors are explicitly classified as transient (e.g., connection reset, network timeout, rate limits) or deterministic (e.g., security violation, path escaping, syntax error).
- **Bounded Retry Budget**: Transient errors retry up to 3 times with exponential backoff and jitter. Deterministic errors and security denials fail fast with zero retries.
- **Durable Checkpointing**: State is persisted using a WAL-enabled SQLite checkpointer. Process restarts preserve task status, retry history, pending approval state, and idempotency records.

---

## 7. Known Limitations and Threat Boundary Scope

1. **Local Single-Node Model**: The current architecture is designed for single-node development and evaluation. Distributed consensus for token revocation across multiple server workers requires a distributed KV store (e.g. Redis).
2. **Filesystem Symlinks**: The current sandbox uses Python canonicalization (`os.path.realpath`). In multi-user UNIX environments, symlink race conditions between check and open (TOCTOU) require OS-level mount namespaces or containerization.
3. **Simulated Model Planner**: In local benchmark runs, model decisions are simulated deterministically to guarantee test suite reproducibility without paid API keys.
