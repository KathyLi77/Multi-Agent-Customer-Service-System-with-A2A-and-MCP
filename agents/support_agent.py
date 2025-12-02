class SupportAgent:
    name = "SupportAgent"

    def log(self, state, sender, msg):
        state.setdefault("messages", []).append(
            {"from": sender, "to": self.name, "content": msg}
        )

    # ------------------------------------------------
    # Scenario 1: Upgrade account
    # ------------------------------------------------
    def handle_account_upgrade(self, state):
        cust = state.get("customer")
        if not cust:
            return "Customer information not found."

        name = cust.get("name", "Customer")
        return f"Hello {name}! Your account is active. I can help upgrade your plan immediately."

    # ------------------------------------------------
    # Scenario 2: Billing escalation
    # ------------------------------------------------
    def handle_billing_escalation(self, state):
        cust = state.get("customer")
        cid = cust.get("id")

        tickets = state.get("tickets", {}).get(cid, [])
        active_issues = len([t for t in tickets if t["status"] != "resolved"])

        return (
            f"Billing team already has {active_issues} active issues for you. "
            f"I have escalated to high priority."
        )

    # ------------------------------------------------
    # Scenario 3: High-priority ticket summary
    # ------------------------------------------------
    def summarize_high_priority_tickets(self, state):
        tickets = state.get("high_priority_tickets", [])
        if not tickets:
            return "There are no high-priority tickets for premium customers."

        lines = []
        for t in tickets:
            cid = t["customer_id"]
            # Find the matching customer
            cust_list = state.get("active_customers", [])
            cust = next((c for c in cust_list if c["id"] == cid), None)

            cname = cust["name"] if cust else f"Customer {cid}"
            lines.append(
                f"{cname}: Ticket {t['id']} — {t['issue']} [{t['status']}]"
            )

        return "\n".join(lines)

    # ------------------------------------------------
    # NEW: Scenario 4 – Multi-intent update + history
    # ------------------------------------------------
    def summarize_multi_intent(self, state, customer, updated_email, tickets):
        name = customer.get("name", "Customer")
        cid = customer.get("id", "?")

        ticket_lines = "\n".join(
            [f" - Ticket {t['id']}: {t['issue']} [{t['status']}]" for t in tickets]
        ) or "No ticket history found."

        return (
            f"Success! I've updated the email for customer {cid} ({name}) to {updated_email}.\n\n"
            f"Here is your ticket history:\n{ticket_lines}"
        )
