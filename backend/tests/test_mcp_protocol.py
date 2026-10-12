import sys
import json
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

@pytest.mark.asyncio
async def test_mcp_client_discover_and_call_tools_over_stdio():
    """Verify that an actual MCP client discovers and calls tools over official MCP stdio transport."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.mcp_server.protocol_server", "--transport", "stdio"]
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. Initialize MCP protocol session
            init_res = await session.initialize()
            assert init_res.server_info.name == "agentops-nexus-tools"
            assert init_res.server_info.version == "1.0.0"

            # 2. Discover available tools via official protocol tools/list
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            assert "search_repository" in tool_names
            assert "get_project_status" in tool_names
            assert "query_project_database" in tool_names
            assert "run_test_suite" in tool_names
            assert "propose_file_patch" in tool_names
            assert "apply_approved_patch" in tool_names
            assert len(tool_names) == 6

            # 3. Call tool: get_project_status
            status_res = await session.call_tool(
                "get_project_status",
                arguments={"include_tests": True, "include_tasks": True}
            )
            assert len(status_res.content) > 0
            payload = json.loads(status_res.content[0].text)
            assert payload["success"] is True
            assert payload["tool"] == "get_project_status"
            assert "project_name" in payload["data"]

            # 4. Call tool: query_project_database with read-only query
            db_res = await session.call_tool(
                "query_project_database",
                arguments={"query": "SELECT * FROM project_tasks LIMIT 3;", "limit": 3}
            )
            assert len(db_res.content) > 0
            db_payload = json.loads(db_res.content[0].text)
            assert db_payload["success"] is True
            assert db_payload["tool"] == "query_project_database"
            assert "rows" in db_payload["data"]

            # 5. Call tool: search_repository
            search_res = await session.call_tool(
                "search_repository",
                arguments={"query": "calculate_discount", "path_pattern": "*.py", "max_results": 5}
            )
            search_payload = json.loads(search_res.content[0].text)
            assert search_payload["success"] is True
            assert len(search_payload["data"]["matches"]) > 0

@pytest.mark.asyncio
async def test_mcp_client_security_enforcement_over_protocol():
    """Verify that permission violations are safely blocked through the MCP protocol."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.mcp_server.protocol_server", "--transport", "stdio"]
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Attempt forbidden DROP TABLE statement
            sql_res = await session.call_tool(
                "query_project_database",
                arguments={"query": "DROP TABLE project_tasks;", "limit": 10}
            )
            payload = json.loads(sql_res.content[0].text)
            assert payload["success"] is False
            assert "Only read-only queries" in payload["error"]

            # Attempt forbidden path traversal on propose_file_patch
            traversal_res = await session.call_tool(
                "propose_file_patch",
                arguments={
                    "file_path": "../../../etc/shadow",
                    "search_block": "root:x:",
                    "replace_block": "root:hacked:",
                    "explanation": "Attempt traversal escape"
                }
            )
            traversal_payload = json.loads(traversal_res.content[0].text)
            assert traversal_payload["success"] is False
            assert "escapes sandbox boundary" in traversal_payload["error"]
