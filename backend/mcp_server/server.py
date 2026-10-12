import os
import json
from typing import Any, Dict, List
from backend.mcp_server.permissions import PermissionPolicy, redact_secrets, SecurityError
from backend.mcp_server.tools import (
    MCPTools,
    SearchRepositoryInput,
    GetProjectStatusInput,
    QueryProjectDatabaseInput,
    RunTestSuiteInput,
    ProposeFilePatchInput,
    ApplyApprovedPatchInput,
    get_pending_patch
)

DEFAULT_REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "repo"))
DEFAULT_DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sandbox", "db", "project_db.sqlite"))

class MCPServer:
    def __init__(self, repo_dir: str = DEFAULT_REPO_DIR, db_path: str = DEFAULT_DB_FILE):
        self.policy = PermissionPolicy(repo_root=repo_dir, db_path=db_path)
        self.tools = MCPTools(policy=self.policy)
        self.tool_registry = {
            "search_repository": {
                "description": "Search files and source code in an authorized repository",
                "schema": SearchRepositoryInput.model_json_schema(),
                "handler": lambda args: self.tools.search_repository(SearchRepositoryInput(**args)),
                "is_sensitive": False
            },
            "get_project_status": {
                "description": "Retrieve project, task, and test status from repository database",
                "schema": GetProjectStatusInput.model_json_schema(),
                "handler": lambda args: self.tools.get_project_status(GetProjectStatusInput(**args)),
                "is_sensitive": False
            },
            "query_project_database": {
                "description": "Retrieve permitted project records using read-only SQL queries",
                "schema": QueryProjectDatabaseInput.model_json_schema(),
                "handler": lambda args: self.tools.query_project_database(QueryProjectDatabaseInput(**args)),
                "is_sensitive": False
            },
            "run_test_suite": {
                "description": "Run an allowlisted test command in the isolated sandbox environment",
                "schema": RunTestSuiteInput.model_json_schema(),
                "handler": lambda args: self.tools.run_test_suite(RunTestSuiteInput(**args)),
                "is_sensitive": False
            },
            "propose_file_patch": {
                "description": "Generate a proposed code change without applying it to disk",
                "schema": ProposeFilePatchInput.model_json_schema(),
                "handler": lambda args: self.tools.propose_file_patch(ProposeFilePatchInput(**args)),
                "is_sensitive": False
            },
            "apply_approved_patch": {
                "description": "Apply a previously approved patch only after authorization token validation",
                "schema": ApplyApprovedPatchInput.model_json_schema(),
                "handler": lambda args: self.tools.apply_approved_patch(ApplyApprovedPatchInput(**args)),
                "is_sensitive": True
            }
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Expose list of available tools with schemas and metadata."""
        return [
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["schema"],
                "isSensitive": meta["is_sensitive"]
            }
            for name, meta in self.tool_registry.items()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate permissions and inputs, execute tool, redact secrets, return structured result."""
        if name not in self.tool_registry:
            raise ValueError(f"Tool '{name}' not found in MCP server registry.")

        tool_meta = self.tool_registry[name]
        is_sensitive = False

        try:
            # 1. Enforce permission checks and sensitive classification
            is_sensitive, reason = self.policy.is_sensitive_operation(name, arguments)

            # 2. Validate input payload size limits
            self.policy.validate_input_size(name, arguments)

            # 3. Redacted arguments for logging
            safe_args = redact_secrets(arguments)

            handler = tool_meta["handler"]
            output = handler(arguments)
            safe_output = redact_secrets(output)
            return {
                "success": True,
                "tool": name,
                "is_sensitive": is_sensitive,
                "data": safe_output
            }
        except Exception as e:
            return {
                "success": False,
                "tool": name,
                "is_sensitive": is_sensitive,
                "error": str(e)
            }

# Global singleton server instance
default_mcp_server = MCPServer()
