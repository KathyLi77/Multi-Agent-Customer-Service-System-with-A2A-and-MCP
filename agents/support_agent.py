# agents/support_agent.py

from typing import Any, Dict, List


class SupportAgent:
    """
    Support Agent:
    - Turns raw DB info into helpful customer-support answers.
    - Handles upgrade, cancellations, refunds, friendly summaries.
    """

    def summarize_customer(self, customer: Dict[str, Any]) -> str:
        """
        Summarize a single customer record.

        Expected input shape from CustomerDataAgent:
        - {"customer": <dict>} when found
        - {"customer": None} or {} or None when not found
        - We also guard against wrong types (e.g., a plain string) to avoid crashes.
        """
        if (
            not customer
            or "customer" not in customer
            or customer["customer"] is None
            or not isinstance(customer["customer"], dict)
        ):
            return "Customer not found."

        c = customer["customer"]

        name = c.get("name", "Unknown")
        cid = c.get("id", "Unknown")
        email = c.get("email", "N/A")
        phone = c.get("phone", "N/A")
        status = c.get("status", "N/A")

        return (
            f"Customer {name} (ID {cid})\n"
            f"- Email: {email}\n"
            f"- Phone: {phone}\n"
            f"- Status: {status}\n"
        )

    def summarize_customers(
        self,
        customers: Dict[str, Any],
        status: Any = None,
    ) -> str:
        """
        Summarize a list of customers returned by DataAgent.list_customers().

        Expected input:
        - {"customers": [customer_dict, ...]} or directly a list [{...}, ...]
        """
        # Support both {"customers": [...]} and plain list [...]
        if isinstance(customers, dict) and "customers" in customers:
            customer_list = customers["customers"]
        else:
            customer_list = customers

        if not customer_list:
            return "No customers found."

        header_status = f" (status={status})" if status else ""
        lines: List[str] = [f"Customer List{header_status}:"]

        for c in customer_list:
            # Defensive access
            cid = c.get("id", "Unknown")
            name = c.get("name", "Unknown")
            email = c.get("email", "N/A")
            st = c.get("status", "N/A")
            lines.append(f"- ID {cid}: {name} | {email} | {st}")

        return "\n".join(lines)

    def summarize_tickets(self, history: Dict[str, Any]) -> str:
        """
        Summarize ticket history for a customer.

        Expected input shape from CustomerDataAgent.get_history:
        - {"tickets": [ticket_dict, ...]}
        - or {"tickets": []} if none
        """
        if not history or "tickets" not in history:
            return "No ticket history found."

        tickets: List[Dict[str, Any]] = history["tickets"]
        if not tickets:
            return "No ticket history found."

        lines = ["Ticket History:"]
        for t in tickets:
            tid = t.get("id", "Unknown")
            issue = t.get("issue", "N/A")
            status = t.get("status", "N/A")
            priority = t.get("priority", "N/A")
            created_at = t.get("created_at", "N/A")

            lines.append(
                f"- #{tid} | {issue} | {status} | {priority} | {created_at}"
            )
        return "\n".join(lines)

    def build_final_answer(self, parts: List[str]) -> str:
        """
        Combine multiple reasoning results into a final coherent answer.

        `parts` is a list of strings generated during routing:
        - customer summaries
        - ticket summaries
        - small text notes like "Updated: {...}" or "Created ticket: ..."
        """
        cleaned = [p for p in parts if p]
        if not cleaned:
            return "I could not find any relevant information for your request."
        return "\n".join(cleaned)

    def upgrade_account(self, customer: Dict[str, Any]) -> str:
        """
        Optional helper for explicit upgrade-related flows.
        Currently not wired directly by the Router, but can be used in
        extended routing logic for upgrade scenarios.
        """
        if (
            not customer
            or "customer" not in customer
            or customer["customer"] is None
            or not isinstance(customer["customer"], dict)
        ):
            return "Upgrade failed — customer not found."

        name = customer["customer"].get("name", "the customer")
        return f"Account upgrade for {name} has been processed successfully!"
