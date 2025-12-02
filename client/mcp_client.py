# client/mcp_client.py
import asyncio
import json
import os
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent


async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    server = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:

            # Required handshake
            await session.initialize()

            # Call tool
            result: CallToolResult = await session.call_tool(tool_name, arguments)

            if not result.content:
                return None

            item = result.content[0]

            if isinstance(item, TextContent):
                try:
                    return json.loads(item.text)
                except json.JSONDecodeError:
                    return item.text

            return item


def call_tool_sync(tool_name: str, arguments: Dict[str, Any]) -> Any:
    return asyncio.run(call_mcp_tool(tool_name, arguments))
