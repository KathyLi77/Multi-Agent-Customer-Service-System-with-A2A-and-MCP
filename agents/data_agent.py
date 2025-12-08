# agents/data_agent.py

from client.mcp_client import call_tool_sync


class CustomerDataAgent:
    """
    MCP-backed Data Agent.
    Contains dedicated methods + a dynamic fallback.
    """

    # ---------------------------
    # Get customer
    # ---------------------------
    def get_customer(self, customer_id: int):
        resp = call_tool_sync("get_customer", {"customer_id": customer_id})
        return {"customer": resp}

    # ---------------------------
    # Update customer
    # ---------------------------
    def update_customer(self, customer_id: int, updates: dict):
        resp = call_tool_sync("update_customer", {
            "customer_id": customer_id,
            "data": updates
        })
        return {"updated": resp}

    # ---------------------------
    # List customers
    # ---------------------------
    def list_customers(self, status="active", limit=20):
        resp = call_tool_sync("list_customers", {
            "status": status,
            "limit": limit
        })
        return {"customers": resp}

    # ---------------------------
    # Ticket history
    # ---------------------------
    def get_history(self, customer_id: int):
        resp = call_tool_sync("get_customer_history", {
            "customer_id": customer_id
        })
        return {"tickets": resp or []}

    # ---------------------------
    # Create ticket
    # ---------------------------
    def create_ticket(self, customer_id: int, issue: str, priority="medium"):
        resp = call_tool_sync("create_ticket", {
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority
        })
        return {"created": resp}

    # ---------------------------
    # Dynamic fallback
    # ---------------------------
    def call_dynamic(self, action: str, args: dict):
        resp = call_tool_sync(action, args)
        return {"result": resp}
