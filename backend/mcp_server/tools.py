import os
import difflib
import sqlite3
import subprocess
import sys
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.mcp_server.permissions import PermissionPolicy, SecurityError
from backend.agent.approval_manager import default_approval_manager

# In-memory store for pending proposed patches
_PENDING_PATCHES: Dict[str, Dict[str, Any]] = {}

class SearchRepositoryInput(BaseModel):
    query: str = Field(..., description="Text or symbol to search for in repo files")
    path_pattern: str = Field(default="*", description="Filename glob pattern to match (e.g., '*.py')")
    max_results: int = Field(default=20, description="Maximum number of matches to return")

class GetProjectStatusInput(BaseModel):
    include_tests: bool = Field(default=True, description="Whether to include test status")
    include_tasks: bool = Field(default=True, description="Whether to include pending task tickets")

class QueryProjectDatabaseInput(BaseModel):
    query: str = Field(..., description="Read-only SQL query (SELECT, PRAGMA, EXPLAIN)")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameterized arguments")
    limit: int = Field(default=50, description="Max rows to return")

class RunTestSuiteInput(BaseModel):
    test_target: str = Field(default="all", description="Target test module or 'all'")
    timeout_seconds: int = Field(default=30, description="Max execution timeout in seconds")

class ProposeFilePatchInput(BaseModel):
    file_path: str = Field(..., description="Path to file relative to repo root")
    search_block: str = Field(..., description="Exact original code block to be replaced")
    replace_block: str = Field(..., description="New replacement code block")
    explanation: str = Field(..., description="Rationale for the proposed change")

class ApplyApprovedPatchInput(BaseModel):
    patch_id: str = Field(..., description="ID of the previously proposed patch")
    approval_token: str = Field(..., description="Valid approval token issued upon human authorization")
    idempotency_key: str = Field(..., description="Unique client key ensuring idempotent patch application")

class MCPTools:
    def __init__(self, policy: PermissionPolicy):
        self.policy = policy

    def search_repository(self, input_data: SearchRepositoryInput) -> Dict[str, Any]:
        """Search files and source code in the authorized repository."""
        results = []
        repo_root = self.policy.repo_root

        for root, dirs, files in os.walk(repo_root):
            # Exclude hidden or pycache directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), repo_root)
                # Simple glob check
                if input_data.path_pattern != "*" and not rel_path.endswith(input_data.path_pattern.replace("*", "")):
                    continue

                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                        lines = file_obj.readlines()
                        for line_idx, line in enumerate(lines, start=1):
                            if input_data.query.lower() in line.lower():
                                results.append({
                                    "file": rel_path.replace("\\", "/"),
                                    "line": line_idx,
                                    "content": line.strip()
                                })
                                if len(results) >= input_data.max_results:
                                    break
                except Exception:
                    continue
            if len(results) >= input_data.max_results:
                break

        return {
            "query": input_data.query,
            "total_matches": len(results),
            "matches": results
        }

    def get_project_status(self, input_data: GetProjectStatusInput) -> Dict[str, Any]:
        """Retrieve project status, tickets, and test run summaries."""
        status_data: Dict[str, Any] = {
            "project_name": "agentops-nexus-billing",
            "repo_root": self.policy.repo_root,
            "environment": "sandboxed-evaluation"
        }

        if not os.path.exists(self.policy.db_path):
            return {"error": "Project database not found", "status": status_data}

        conn = sqlite3.connect(self.policy.db_path)
        cur = conn.cursor()

        if input_data.include_tasks:
            cur.execute("SELECT ticket_id, title, status, priority FROM project_tasks")
            tasks = [{"ticket_id": r[0], "title": r[1], "status": r[2], "priority": r[3]} for r in cur.fetchall()]
            status_data["tasks"] = tasks

        if input_data.include_tests:
            cur.execute("SELECT suite_name, status, failed_count, passed_count, last_error FROM test_runs")
            test_runs = [{
                "suite_name": r[0],
                "status": r[1],
                "failed_count": r[2],
                "passed_count": r[3],
                "last_error": r[4]
            } for r in cur.fetchall()]
            status_data["test_runs"] = test_runs

        conn.close()
        return status_data

    def query_project_database(self, input_data: QueryProjectDatabaseInput) -> Dict[str, Any]:
        """Run safe, read-only parameterized SQL query."""
        self.policy.validate_sql(input_data.query)

        conn = sqlite3.connect(self.policy.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            params = input_data.params or {}
            # Enforce max limit
            effective_query = input_data.query
            if "limit" not in effective_query.lower():
                effective_query = f"{effective_query} LIMIT {min(input_data.limit, 100)}"

            if isinstance(params, dict) and params:
                cur.execute(effective_query, params)
            elif isinstance(params, (list, tuple)) and params:
                cur.execute(effective_query, params)
            else:
                cur.execute(effective_query)

            rows = cur.fetchall()
            col_names = [col[0] for col in cur.description] if cur.description else []
            data = [dict(zip(col_names, row)) for row in rows]
            return {
                "columns": col_names,
                "row_count": len(data),
                "rows": data
            }
        finally:
            conn.close()

    def run_test_suite(self, input_data: RunTestSuiteInput) -> Dict[str, Any]:
        """Run allowlisted test suite in the sandbox."""
        repo_root = self.policy.repo_root
        test_file = "test_calculator.py"

        if input_data.test_target != "all":
            # Sanitize target
            safe_target = os.path.basename(input_data.test_target)
            if safe_target.endswith(".py"):
                test_file = safe_target

        full_test_path = self.policy.validate_file_path(test_file)

        cmd = [sys.executable, "-m", "unittest", test_file]
        try:
            proc = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=input_data.timeout_seconds
            )
            passed = (proc.returncode == 0)
            return {
                "command": f"python -m unittest {test_file}",
                "exit_code": proc.returncode,
                "passed": passed,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "summary": "All tests passed" if passed else "Tests failed with errors"
            }
        except subprocess.TimeoutExpired:
            return {
                "command": f"python -m unittest {test_file}",
                "exit_code": -1,
                "passed": False,
                "error": f"Test run timed out after {input_data.timeout_seconds} seconds"
            }

    def propose_file_patch(self, input_data: ProposeFilePatchInput) -> Dict[str, Any]:
        """Generates a proposed patch without applying it; stores it for review."""
        full_path = self.policy.validate_file_path(input_data.file_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Target file '{input_data.file_path}' does not exist.")

        with open(full_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        if input_data.search_block not in original_content:
            raise ValueError(
                f"Search block not found in '{input_data.file_path}'. "
                f"Verify lines before proposing patch."
            )

        new_content = original_content.replace(input_data.search_block, input_data.replace_block, 1)

        # Generate standard unified diff
        diff_lines = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{input_data.file_path}",
            tofile=f"b/{input_data.file_path}",
        ))
        diff_text = "".join(diff_lines)

        patch_id = f"patch-{uuid.uuid4().hex[:12]}"
        _PENDING_PATCHES[patch_id] = {
            "patch_id": patch_id,
            "file_path": input_data.file_path,
            "full_path": full_path,
            "search_block": input_data.search_block,
            "replace_block": input_data.replace_block,
            "explanation": input_data.explanation,
            "diff": diff_text,
            "status": "pending_approval"
        }

        return {
            "patch_id": patch_id,
            "file_path": input_data.file_path,
            "explanation": input_data.explanation,
            "diff": diff_text,
            "status": "pending_approval",
            "message": "Patch generated and pending human approval before modification."
        }

    def apply_approved_patch(self, input_data: ApplyApprovedPatchInput) -> Dict[str, Any]:
        """Applies a patch only after verifying human authorization and idempotency."""
        # 1. Require approval token first
        if not input_data.approval_token or len(input_data.approval_token.strip()) < 8:
            raise SecurityError("Unauthorized: Valid approval token is required to apply patch.")

        # 2. Check idempotency
        already_applied = self.policy.check_and_record_idempotency(
            input_data.idempotency_key,
            f"Apply patch {input_data.patch_id}"
        )
        if already_applied:
            return {
                "success": True,
                "patch_id": input_data.patch_id,
                "message": "Idempotent operation: patch already applied previously.",
                "idempotent_replay": True
            }

        # 3. Validate patch ID
        patch = _PENDING_PATCHES.get(input_data.patch_id)
        if not patch:
            raise ValueError(f"Unknown or expired patch ID: {input_data.patch_id}")

        # 4. Cryptographic and binding validation via ApprovalManager
        try:
            default_approval_manager.validate_and_consume_token(
                token=input_data.approval_token,
                action="apply_approved_patch",
                patch_id=input_data.patch_id,
                arguments=patch
            )
        except Exception as e:
            raise SecurityError(f"Unauthorized: Approval boundary check failed: {e}")

        full_path = patch["full_path"]
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        if patch["search_block"] not in current_content:
            # Maybe already modified
            if patch["replace_block"] in current_content:
                patch["status"] = "applied"
                return {
                    "success": True,
                    "patch_id": input_data.patch_id,
                    "file_path": patch["file_path"],
                    "message": "File already contains proposed changes."
                }
            raise ValueError(
                f"Cannot apply patch: search block no longer matches current file content in '{patch['file_path']}'."
            )

        updated_content = current_content.replace(patch["search_block"], patch["replace_block"], 1)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        patch["status"] = "applied"
        return {
            "success": True,
            "patch_id": input_data.patch_id,
            "file_path": patch["file_path"],
            "message": f"Patch successfully applied to '{patch['file_path']}'.",
            "diff_applied": patch.get("diff", "")
        }


def get_pending_patch(patch_id: str) -> Optional[Dict[str, Any]]:
    return _PENDING_PATCHES.get(patch_id)
