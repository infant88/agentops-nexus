"""Official Model Context Protocol (MCP) Server for AgentOps Nexus.

Implements the standard MCP protocol transport (stdio and SSE)
allowing external MCP clients (Claude Desktop, Cursor, Zed, custom agents)
to discover and execute sandboxed repository and database tools.
"""

import sys
import json
import argparse
from typing import Any, Dict, Optional
from mcp.server.mcpserver import MCPServer
from backend.mcp_server.server import default_mcp_server

# Instantiate official MCP Server
mcp_protocol_server = MCPServer(
    name="agentops-nexus-tools",
    version="1.0.0",
    description="AgentOps Nexus Standardized MCP Tool Server"
)

# Register official MCP tools with docstrings and typed arguments

@mcp_protocol_server.tool()
def search_repository(query: str, path_pattern: str = "*", max_results: int = 20) -> str:
    """Search files and source code in the authorized sandbox repository.
    
    Args:
        query: Substring or regex pattern to match across files.
        path_pattern: Glob file filter pattern (e.g. '*.py').
        max_results: Maximum matching items to return (1-100).
    """
    res = default_mcp_server.call_tool("search_repository", {
        "query": query,
        "path_pattern": path_pattern,
        "max_results": max_results
    })
    return json.dumps(res, indent=2)

@mcp_protocol_server.tool()
def get_project_status(include_tests: bool = True, include_tasks: bool = True) -> str:
    """Retrieve current project metadata, open tickets, and recent test run status.
    
    Args:
        include_tests: Whether to attach recent test run statistics.
        include_tasks: Whether to attach open development task items.
    """
    res = default_mcp_server.call_tool("get_project_status", {
        "include_tests": include_tests,
        "include_tasks": include_tasks
    })
    return json.dumps(res, indent=2)

@mcp_protocol_server.tool()
def query_project_database(query: str, limit: int = 10) -> str:
    """Execute permitted read-only SQL queries against the sandbox project database.
    
    Args:
        query: Valid SELECT statement targeting permitted tables.
        limit: Maximum rows to return (bounded between 1 and 100).
    """
    res = default_mcp_server.call_tool("query_project_database", {
        "query": query,
        "limit": limit
    })
    return json.dumps(res, indent=2)

@mcp_protocol_server.tool()
def run_test_suite(test_target: str = "all", timeout_seconds: int = 30) -> str:
    """Execute allowlisted pytest suite in the isolated sandbox environment.
    
    Args:
        test_target: Target module or 'all' for full repository tests.
        timeout_seconds: Maximum execution time before termination.
    """
    res = default_mcp_server.call_tool("run_test_suite", {
        "test_target": test_target,
        "timeout_seconds": timeout_seconds
    })
    return json.dumps(res, indent=2)

@mcp_protocol_server.tool()
def propose_file_patch(file_path: str, search_block: str, replace_block: str, explanation: str) -> str:
    """Generate a validated unified diff patch without modifying files on disk.
    
    Args:
        file_path: Relative target file within the sandbox repository.
        search_block: Exact lines of source code to replace.
        replace_block: Proposed replacement lines.
        explanation: Clear technical description of why the change is required.
    """
    res = default_mcp_server.call_tool("propose_file_patch", {
        "file_path": file_path,
        "search_block": search_block,
        "replace_block": replace_block,
        "explanation": explanation
    })
    return json.dumps(res, indent=2)

@mcp_protocol_server.tool()
def apply_approved_patch(patch_id: str, approval_token: str, idempotency_key: str) -> str:
    """Apply a previously authorized patch to disk after human authorization validation.
    
    Args:
        patch_id: Unique identifier of the proposed patch.
        approval_token: Valid cryptographic human authorization token.
        idempotency_key: Client-generated deduplication token.
    """
    res = default_mcp_server.call_tool("apply_approved_patch", {
        "patch_id": patch_id,
        "approval_token": approval_token,
        "idempotency_key": idempotency_key
    })
    return json.dumps(res, indent=2)

def main():
    parser = argparse.ArgumentParser(description="AgentOps Nexus Official MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport protocol (stdio or sse)"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for SSE server")
    parser.add_argument("--port", type=int, default=8001, help="Port for SSE server")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp_protocol_server.run("stdio")
    elif args.transport == "sse":
        mcp_protocol_server.run("sse", host=args.host, port=args.port)

if __name__ == "__main__":
    main()
