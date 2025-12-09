# agents/support_agent.py
'''
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
'''

# agents/support_agent.py

from typing import Any, Dict, List
import json

from llm_utils import ask_llm


SUPPORT_SYSTEM_PROMPT = """
You are the SupportAgent in a multi-agent customer service system.

You receive:
- the original user query,
- the full conversation log between agents (e.g., User, RouterAgent, CustomerDataAgent),
- raw MCP tool results produced by the CustomerDataAgent.

Your job:
- Explain to the user what you did on their behalf
  (e.g., fetched their profile, updated their email, showed their ticket history).
- Present important results clearly and concisely.
- Be polite, professional, and warm.
- Avoid leaking internal tool names or overly technical details.
- At the end, include a short "A2A LOG" that summarizes how the agents coordinated.

FORMAT:
- First, a friendly answer addressed directly to the user.
- Then a blank line.
- Then a section starting with: "A2A LOG"
  followed by a brief bullet-style or line-by-line description of the key agent interactions.

Do NOT invent data that is not implied by the tool results or messages.
"""


class SupportAgent:
    """
    SupportAgent:
    - Uses an LLM to translate internal agent/tool activity into
      a user-facing answer + a brief A2A-style log.
    """

    def build_final_answer(
        self,
        user_query: str,
        messages: List[Dict[str, str]],
        data_output: Dict[str, Any],
    ) -> str:
        """
        Create the final user-facing answer using the LLM.

        Parameters
        ----------
        user_query:
            Original user query string.
        messages:
            Conversation log (User, RouterAgent, CustomerDataAgent, SupportAgent).
        data_output:
            Dictionary from CustomerDataAgent.handle(), expected keys:
              - "note": short summary string
              - "results": list of tool call outputs
        """
        # Build a simple text log for the LLM to inspect
        log_lines: List[str] = []
        for m in messages:
            sender = m.get("from", "?")
            receiver = m.get("to", "?")
            content = m.get("content", "")
            log_lines.append(f"{sender} → {receiver}: {content}")

        messages_log = "\n".join(log_lines)

        payload = {
            "user_query": user_query,
            "conversation_log": messages_log,
            "data_results": data_output.get("results", []),
            "data_note": data_output.get("note", ""),
        }

        # Let the LLM decide how to best respond to the user
        return ask_llm(
            SUPPORT_SYSTEM_PROMPT,
            json.dumps(payload),
        )
