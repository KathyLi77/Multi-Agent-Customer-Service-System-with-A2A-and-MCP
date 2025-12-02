import re
from typing import Any, Dict, List
from agents.data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent


class RouterAgent:
    name = "RouterAgent"

    def __init__(self):
        self.data = CustomerDataAgent()
        self.support = SupportAgent()

    # Logging helper
    def log(self, state: Dict[str, Any], receiver: str, content: str):
        state.setdefault("messages", []).append(
            {"from": self.name, "to": receiver, "content": content}
        )

    # Extract customer ID
    def extract_id(self, text: str):
        m = re.search(r"\b(\d{1,6})\b", text)
        return int(m.group(1)) if m else None

    # Extract email
    def extract_email(self, text: str):
        m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return m.group(0) if m else None

    # ----------------------------
    # Scenario 1 – Task Allocation
    # ----------------------------
    def scenario_task_allocation(self, query: str, state: Dict[str, Any]):
        cid = self.extract_id(query)
        if not cid:
            return "Please provide a valid customer ID."

        self.log(state, "CustomerDataAgent", "Requesting customer info")
        self.data.get_customer_info(state, cid)

        self.log(state, "SupportAgent", "Forwarding upgrade task")
        return self.support.handle_account_upgrade(state)

    # ----------------------------
    # Scenario 2 – Negotiation
    # ----------------------------
    def scenario_negotiation(self, query: str, state: Dict[str, Any]):
        cid = self.extract_id(query)
        if not cid:
            return "Please include your customer ID for billing issues."

        self.data.get_customer_info(state, cid)
        self.data.get_ticket_history(state, cid)

        self.log(state, "CustomerDataAgent", "Creating escalation ticket")
        self.data.create_ticket(
            state, cid,
            issue="Billing problem during cancellation",
            priority="high"
        )

        return self.support.handle_billing_escalation(state)

    # ----------------------------
    # Scenario 3 – Multi-Step
    # ----------------------------
    def scenario_multistep(self, query: str, state: Dict[str, Any]):
        self.data.list_active_customers(state, limit=200)

        high_tickets = []
        for c in state["active_customers"]:
            tks = self.data.get_ticket_history(state, c["id"])
            for t in tks:
                if t["priority"] == "high":
                    high_tickets.append(t)

        state["high_priority_tickets"] = high_tickets
        return self.support.summarize_high_priority_tickets(state)

    # ----------------------------
    # Scenario 4 – Multi-Intent
    # update email + show history
    # ----------------------------
    def scenario_multi_intent(self, query: str, state: Dict[str, Any]):
        cid = self.extract_id(query)
        if not cid:
            return "Please provide your customer ID for updates."

        email = self.extract_email(query)
        if not email:
            return "Please specify the new email address you want to update."

        # 1. Fetch customer info
        self.log(state, "CustomerDataAgent", f"Fetching customer info for {cid}")
        cust = self.data.get_customer_info(state, cid)

        # 2. Update email
        self.log(state, "CustomerDataAgent", f"Updating email to {email}")
        self.data.update_customer(state, cid, {"email": email})

        # 3. Ticket history
        self.log(state, "CustomerDataAgent", "Fetching ticket history")
        tickets = self.data.get_ticket_history(state, cid)

        # 4. Support agent formats final answer
        self.log(state, "SupportAgent", "Summarizing multi-intent response")
        return self.support.summarize_multi_intent(state, cust, email, tickets)

    # ----------------------------
    # Simple fallback
    # ----------------------------
    def simple_lookup(self, query: str, state: Dict[str, Any]):
        cid = self.extract_id(query)
        if not cid:
            return "Not sure how to help with that request."

        self.data.get_customer_info(state, cid)
        return state.get("customer")

    # ----------------------------
    # ROUTER
    # ----------------------------
    def route(self, query: str):
        state = {"messages": []}
        q = query.lower()

        if "status of all high-priority" in q:
            answer = self.scenario_multistep(query, state)

        elif "cancel" in q or "billing" in q:
            answer = self.scenario_negotiation(query, state)

        elif "update" in q and "email" in q:
            answer = self.scenario_multi_intent(query, state)

        elif "upgrade" in q or "account" in q:
            answer = self.scenario_task_allocation(query, state)

        else:
            answer = self.simple_lookup(query, state)

        return {"answer": answer, "state": state}
