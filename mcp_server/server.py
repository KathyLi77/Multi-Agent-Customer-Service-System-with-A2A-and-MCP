# mcp_server/server.py
# Simple MCP server exposing DB operations as tools

from typing import Any, Dict, Optional
import json

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from mcp_server.db_access import (
    get_customer as db_get_customer,
    list_customers as db_list_customers,
    update_customer as db_update_customer,
    create_ticket as db_create_ticket,
    get_customer_history as db_get_customer_history,
)

# Create MCP server instance
mcp = FastMCP("support-mcp")


@mcp.tool()
async def get_customer(customer_id: int) -> TextContent:
    """Get customer details by ID."""
    data = db_get_customer(customer_id)
    return TextContent(type="text", text=json.dumps(data))


@mcp.tool()
async def list_customers(status: Optional[str] = None, limit: int = 10) -> TextContent:
    """List customers, optionally filtered by status."""
    data = db_list_customers(status, limit)
    return TextContent(type="text", text=json.dumps(data))


@mcp.tool()
async def update_customer(customer_id: int, data: Dict[str, Any]) -> TextContent:
    """Update fields on a customer record."""
    result = db_update_customer(customer_id, data)
    return TextContent(type="text", text=json.dumps(result))


@mcp.tool()
async def create_ticket(customer_id: int, issue: str, priority: str = "medium") -> TextContent:
    """Create a support ticket for a customer."""
    result = db_create_ticket(customer_id, issue, priority)
    return TextContent(type="text", text=json.dumps(result))


@mcp.tool()
async def get_customer_history(customer_id: int) -> TextContent:
    """Get all tickets associated with a customer."""
    data = db_get_customer_history(customer_id)
    return TextContent(type="text", text=json.dumps(data))


if __name__ == "__main__":
    # Use stdio transport so clients can talk to us via stdin/stdout
    mcp.run(transport="stdio")
