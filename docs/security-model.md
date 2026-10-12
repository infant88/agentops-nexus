# AgentOps Nexus — Security & Safeguard Model

MCP standardizes tool communication between LLMs and tools, but **MCP alone does not provide authorization, sandboxing, or safe execution**. AgentOps Nexus implements a zero-trust, server-enforced security architecture.

---

## 1. Threat Matrix & Mitigations

| Threat Vector | Attack Scenario | Defense Mechanism | Enforcement Point |
| :--- | :--- | :--- | :--- |
| **Path Traversal Escape** | Agent attempts reading `/etc/shadow` or writing to system dirs via `../../../` | Canonical path resolution (`os.path.realpath`) and `os.path.commonpath` verification | Server `PermissionPolicy` |
| **Destructive SQL Injection** | Prompt injection forces agent to run `DROP TABLE` or `DELETE FROM` | Strict whitelist of allowed query prefixes (`SELECT`, `PRAGMA table_info`, `EXPLAIN`) and forbidden mutation pattern matching | MCP Database Client |
| **Unreviewed File Mutation** | Agent modifies production source code autonomously | Mandatory LangGraph checkpoint `interrupt()`; requires high-entropy `approval_token` | Workflow Orchestrator & Server Tool Handler |
| **Replay Attacks** | Retried operations accidentally apply duplicate patches twice | UUID-based `idempotency_key` tracking | MCP Patch Engine |
| **Credential / Token Leakage** | API keys or authorization headers leak into logs or UI | Recursive regex secret redactor masking patterns (`sk-...`, `Bearer ...`) | Observability Tracer & Audit Logger |

---

## 2. Path Traversal Sandbox Prison

Paths are validated prior to opening file descriptors:

```python
def validate_file_path(self, relative_or_abs_path: str) -> str:
    if "\0" in relative_or_abs_path:
        raise SecurityError("Null byte injection detected in file path.")

    target = os.path.join(self.repo_root, relative_or_abs_path) if not os.path.isabs(relative_or_abs_path) else relative_or_abs_path
    resolved = os.path.realpath(target)

    if os.path.commonpath([resolved, self.repo_root]) != self.repo_root:
        raise SecurityError(f"Access denied: Path '{relative_or_abs_path}' escapes sandbox boundary.")

    return resolved
```

---

## 3. SQL Query Guardrails

The database tool enforces read-only access by default:
- **Disallowed Keywords**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `REPLACE`, `ATTACH`, `DETACH`, `TRUNCATE`, `EXEC`, `VACUUM`.
- **Query Chaining**: Multi-statement execution via semicolons (`;`) is blocked.
- **Limit Clamping**: If a query omits a `LIMIT` clause, the server clamps it to `LIMIT 100` to prevent memory denial-of-service.

---

## 4. Idempotency Controls

To ensure retried operations do not produce race conditions or duplicate file corruption, every mutating request requires a unique `idempotency_key`. The server records keys in memory; replay attempts return the cached outcome without reapplying changes.
