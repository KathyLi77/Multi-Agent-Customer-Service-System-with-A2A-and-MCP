from typing import Any, Dict, List
from client.mcp_client import call_tool_sync


class CustomerDataAgent:
    name = "CustomerDataAgent"

    def log(self, state, sender, msg):
        state.setdefault("messages", []).append(
            {"from": sender, "to": self.name, "content": msg}
        )

    # ------------------------------------------------
    # GET CUSTOMER
    # ------------------------------------------------
    def get_customer_info(self, state, customer_id):
        self.log(state, "RouterAgent", f"Get customer {customer_id}")
        result = call_tool_sync("get_customer", {"customer_id": customer_id})
        state["customer"] = result
        return result

    # ------------------------------------------------
    # LIST ACTIVE CUSTOMERS
    # ------------------------------------------------
    def list_active_customers(self, state, limit=50):
        self.log(state, "RouterAgent", "List active customers")
        result = call_tool_sync("list_customers", {"status": "active", "limit": limit})
        state["active_customers"] = result
        return result

    # ------------------------------------------------
    # TICKET HISTORY
    # ------------------------------------------------
    def get_ticket_history(self, state, customer_id):
        self.log(state, "RouterAgent", f"Get ticket history for {customer_id}")
        result = call_tool_sync("get_customer_history", {"customer_id": customer_id})
        state.setdefault("tickets", {})[customer_id] = result
        return result

    # ------------------------------------------------
    # CREATE TICKET
    # ------------------------------------------------
    def create_ticket(self, state, customer_id, issue, priority="medium"):
        payload = {
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority
        }
        self.log(state, "RouterAgent", f"Create ticket: {issue} ({priority})")
        result = call_tool_sync("create_ticket", payload)
        return result

    # ------------------------------------------------
    # UPDATE CUSTOMER 
    # ------------------------------------------------
    def update_customer(self, state, customer_id, data: dict):
        self.log(state, "RouterAgent", f"Update customer {customer_id}: {data}")
        result = call_tool_sync("update_customer", {
            "customer_id": customer_id,
            "data": data
        })
        return result
