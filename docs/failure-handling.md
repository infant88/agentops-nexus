# AgentOps Nexus — Failure Handling & Recovery Policy

A resilient AI agent system must distinguish between **transient network glitches** (which should be retried with exponential backoff) and **deterministic errors** (such as syntax errors, validation failures, or security breaches, which must fail fast to prevent resource exhaustion and infinite loops).

---

## 1. Error Classification Engine

| Failure Category | Examples | Policy Action | Retry Budget |
| :--- | :--- | :--- | :--- |
| **Transient Glitches** | Network timeouts, rate limit spikes (HTTP 429), lock contention, temporary server unresponsiveness (HTTP 503) | **Bounded Exponential Backoff with Jitter** | Up to 3 attempts |
| **Security Violations** | Path traversal (`../`), null byte injections, forbidden SQL keywords (`DROP`, `DELETE`, `INSERT`) | **Immediate Halt / Fail-Fast** | 0 (No retries) |
| **Schema & Input Errors** | Missing required parameters, malformed JSON, invalid data types | **Fail-Fast** | 0 (No retries) |
| **Human Rejection** | Reviewer declines proposed patch or requests architectural revision | **Graceful Abort / Postmortem Logging** | 0 |

---

## 2. Bounded Exponential Backoff Algorithm

When a transient error is caught, the backoff delay is calculated with bounded exponential growth and random jitter:

$$\text{Delay} = \min\left(\text{max\_delay},\, \text{base\_delay} \times \text{factor}^{\text{retry\_count}} + \text{jitter}\right)$$

Where:
- $\text{base\_delay} = 0.2\text{s}$
- $\text{factor} = 1.5$
- $\text{jitter} \in [0.05, 0.15]\text{s}$
- $\text{max\_delay} = 3.0\text{s}$

This prevents thundering-herd problems and guarantees that the system will never loop indefinitely.

---

## 3. Human-in-the-Loop Checkpoint Interrupts

For protected actions (such as applying unified diff code patches or altering persistent configuration):
1. The orchestrator calls LangGraph's `interrupt()` function.
2. The current execution frame and all state variables are snapshotted to the persistent checkpointer.
3. The API signals `status = "waiting_approval"` and returns an interactive diff preview to the frontend dashboard.
4. When a reviewer responds (`approved`, `rejected`, or `revision_requested`), the state is rehydrated via `Command(resume=...)` without re-running previous steps or losing historical evidence.

---

## 4. Verification Gates & Result Integrity

After an approved patch is applied:
- The agent does not blindly report success.
- It enters the `verify_result` node, executing the allowlisted test runner (`python -m unittest test_calculator.py`).
- Only if the test suite returns exit code `0` and passes all assertions does the system mark the mission as `VERIFIED`.
- If tests fail, diagnostic logs are captured and presented in the executive summary.
