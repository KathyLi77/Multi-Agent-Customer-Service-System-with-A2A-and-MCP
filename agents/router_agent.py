# agents/router_agent.py

from typing import Any, Dict, List, Optional

from llm_utils import ask_llm_json
from agents.data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent


LLM_ROUTER_PROMPT = """
You are the Router Agent.

You MUST output ONLY valid JSON.
You MUST NOT output explanations.
You MUST NOT output markdown.
You MUST NOT output text outside of JSON.

===============================
AVAILABLE AGENTS AND ACTIONS
===============================
You orchestrate two agents:

1. CustomerDataAgent (use agent = "data"):
   - get_customer(id)             -> args: {"id": <int>}
   - update_customer(id, fields)  -> args: {"id": <int>, "fields": {...}}
   - get_history(id)              -> args: {"id": <int>}
   - create_ticket(id, issue, priority)
       -> args: {"id": <int>, "issue": <str>, "priority": "low"|"medium"|"high"}
   - list_customers(status, limit)
       -> args: {"status": <str>, "limit": <int>}

2. SupportAgent (use agent = "support"):
   - final_answer()               -> args: {}

===============================
ARGUMENT RULES
===============================
- For get_customer, update_customer, get_history, and create_ticket:
  • "id" MUST be an integer customer ID.
  • NEVER omit the "id" argument.
- For list_customers:
  • "status" is usually "active" or "disabled".
  • "limit" is a small integer (e.g., 10, 20).

===============================
PLANNING GUIDELINES
===============================
General:
- Always produce a minimal but sufficient sequence of steps.
- ALWAYS end with a SupportAgent step:
    {"agent": "support", "action": "final_answer", "args": {}}
- Use only the allowed actions and fields.

Single-customer queries:
- If the user provides a numeric customer ID in any way (for example: "ID 7", "customer 12", "I am customer 5"):
  • The FIRST step MUST be:
      {"agent": "data", "action": "get_customer", "args": {"id": <that id>}}
  • After that, you may add other data steps (update_customer, get_history, create_ticket)
    as needed before final_answer.

Account help / upgrade / subscription changes:
- When the user says they need help with their account, plan, upgrade, or subscription
  and they provide an ID:
  • FIRST: get_customer(id).
  • Optionally: create_ticket(id, issue, priority="medium") to record the request.
  • Then: final_answer that explains what was done and confirms help.

Billing / overcharge / urgent issues (for example, being charged twice, refund, urgent cancellation):
- When the user reports a billing problem and also wants cancellation or refund,
  and they provide an ID:
  • FIRST: get_customer(id).
  • THEN: create_ticket(
            id=<same id>,
            issue=<short description of the billing and cancellation problem>,
            priority="high"
          ).
  • THEN: final_answer that acknowledges urgency and confirms that a high-priority
    ticket has been created.

Queries involving multiple customers or tickets:
- If the question clearly refers to groups, aggregates, or "all" customers/tickets
  (for example: "all active customers with open tickets", "status of all high-priority tickets"):
  • Use list_customers(status, limit) to get a relevant set of customers.
    - Usually status="active" and limit is a small integer.
  • Optionally, for some or all of those customers, call get_history(id=...) to fetch tickets.
  • Then call final_answer, summarizing what you found across the group.

===============================
STRICT OUTPUT FORMAT
===============================
Output ONLY this JSON object:

{
  "steps": [
    {"agent": "data", "action": "...", "args": {...}},
    {"agent": "support", "action": "final_answer", "args": {}}
  ]
}

Rules:
• ALWAYS include "steps"
• ALWAYS end with support.final_answer
• NEVER output text outside JSON
• NEVER include comments
• Use only the allowed actions and fields
"""


class RouterAgent:
    """
    Router Agent:
    - Uses an LLM to decide which sub-agent to call in which order.
    - CustomerDataAgent talks to the MCP server (DB).
    - SupportAgent turns raw results into friendly answers.
    - This class also records an explicit "A2A-style" log that shows how
      the Router coordinates between agents.

    The test harness (tests/main.py) expects the state to look like:
        state = {
            "messages": [
                {"from": "...", "to": "...", "content": "..."},
                ...
            ]
        }
    """

    def __init__(self):
        self.data = CustomerDataAgent()
        self.support = SupportAgent()

    # ------------------------------------------------------
    # Public entry point used by tests.main.run()
    # ------------------------------------------------------
    def route(self, query: str) -> Dict[str, Any]:
        """Simple wrapper so tests.main.py can call `router.route(query)`."""
        return self.run(query)

    # ------------------------------------------------------
    # Helper: safely parse a customer ID from LLM args
    # ------------------------------------------------------
    @staticmethod
    def _parse_customer_id(raw_id: Any) -> Optional[int]:
        """
        Convert the raw LLM-provided ID to an integer if possible.

        Returns:
            int if raw_id is a valid integer value
            None otherwise
        """
        if isinstance(raw_id, int):
            return raw_id
        if isinstance(raw_id, str) and raw_id.isdigit():
            return int(raw_id)
        return None

    # ------------------------------------------------------
    # LLM-driven multi-step orchestration
    # ------------------------------------------------------
    def run(self, query: str) -> Dict[str, Any]:
        """
        Main orchestration method:
        1. Ask the LLM for a JSON "plan" of steps.
        2. Execute each step in order.
        3. Build an explicit A2A log in the format expected by tests/main.py.
        """
        # STEP 1 — get routing plan as JSON (robust JSON extraction)
        plan = ask_llm_json(LLM_ROUTER_PROMPT, f"User query: {query}")

        # Basic safety checks on the plan structure
        if not plan or "steps" not in plan or not isinstance(plan["steps"], list):
            msg = f"Router did not produce a valid plan: {plan}"
            return {
                "answer": msg,
                "log": [],
                "state": {"messages": []},
            }

        # A2A-style log for the notebook / test harness
        messages: List[Dict[str, str]] = []

        # Partial answers / summaries from each step
        answer_chunks: List[str] = []

        # STEP 2 — Execute steps sequentially
        for step in plan["steps"]:
            agent = step.get("agent")
            action = step.get("action")
            args = step.get("args", {}) or {}

            # -----------------------------------
            # DATA AGENT OPERATIONS
            # -----------------------------------
            if agent == "data":
                # 1) Get a single customer
                if action == "get_customer":
                    raw_id = args.get("id")
                    cid = self._parse_customer_id(raw_id)

                    if cid is None:
                        messages.append({
                            "from": "RouterAgent",
                            "to": "CustomerDataAgent",
                            "content": "Attempted get_customer without a valid numeric ID – step skipped",
                        })
                        answer_chunks.append(
                            "I could not look up a specific customer because the ID was not valid."
                        )
                        continue

                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"get_customer(id={cid})",
                    })
                    customer = self.data.get_customer(cid)
                    messages.append({
                        "from": "CustomerDataAgent",
                        "to": "RouterAgent",
                        "content": "returned customer record",
                    })
                    answer_chunks.append(self.support.summarize_customer(customer))

                # 2) Update customer fields
                elif action == "update_customer":
                    raw_id = args.get("id")
                    cid = self._parse_customer_id(raw_id)
                    fields = args.get("fields", {}) or {}

                    if cid is None:
                        messages.append({
                            "from": "RouterAgent",
                            "to": "CustomerDataAgent",
                            "content": "Attempted update_customer without a valid numeric ID – step skipped",
                        })
                        answer_chunks.append(
                            "Could not update customer because the ID was not valid."
                        )
                        continue

                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"update_customer(id={cid}, fields={fields})",
                    })
                    self.data.update_customer(cid, fields)
                    messages.append({
                        "from": "CustomerDataAgent",
                        "to": "RouterAgent",
                        "content": "customer updated",
                    })
                    answer_chunks.append(f"Updated customer {cid} with fields: {fields}")

                # 3) Get ticket history for a single customer
                elif action == "get_history":
                    raw_id = args.get("id")
                    cid = self._parse_customer_id(raw_id)

                    if cid is None:
                        messages.append({
                            "from": "RouterAgent",
                            "to": "CustomerDataAgent",
                            "content": "Attempted get_history without a valid numeric ID – step skipped",
                        })
                        answer_chunks.append(
                            "Could not fetch ticket history because the customer ID was not valid."
                        )
                        continue

                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"get_customer_history(id={cid})",
                    })
                    history = self.data.get_history(cid)
                    messages.append({
                        "from": "CustomerDataAgent",
                        "to": "RouterAgent",
                        "content": "returned ticket history",
                    })
                    answer_chunks.append(self.support.summarize_tickets(history))

                # 4) Create ticket
                elif action == "create_ticket":
                    raw_id = args.get("id")
                    cid = self._parse_customer_id(raw_id)
                    issue = args.get("issue", "") or ""
                    pri = args.get("priority", "medium") or "medium"

                    if cid is None:
                        messages.append({
                            "from": "RouterAgent",
                            "to": "CustomerDataAgent",
                            "content": "Attempted create_ticket without a valid numeric ID – step skipped",
                        })
                        answer_chunks.append(
                            "Could not create a ticket because the customer ID was not valid."
                        )
                        continue

                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"create_ticket(id={cid}, issue='{issue}', priority='{pri}')",
                    })
                    self.data.create_ticket(cid, issue, pri)
                    messages.append({
                        "from": "CustomerDataAgent",
                        "to": "RouterAgent",
                        "content": "ticket created",
                    })
                    answer_chunks.append(
                        f"Created a {pri} priority ticket for customer {cid}: {issue}"
                    )

                # 5) List customers (for aggregate-style queries)
                elif action == "list_customers":
                    status = args.get("status")
                    limit = args.get("limit", 20)

                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"list_customers(status={status}, limit={limit})",
                    })
                    customers = self.data.list_customers(
                        status=status if status else "active",
                        limit=limit if isinstance(limit, int) else 20,
                    )
                    messages.append({
                        "from": "CustomerDataAgent",
                        "to": "RouterAgent",
                        "content": "returned customer list",
                    })
                    answer_chunks.append(
                        self.support.summarize_customers(
                            customers,
                            status=status,
                        )
                    )

                # Unknown data action — log and continue
                else:
                    messages.append({
                        "from": "RouterAgent",
                        "to": "CustomerDataAgent",
                        "content": f"Unknown data action '{action}' – step ignored",
                    })
                    answer_chunks.append(
                        f"(Router skipped unknown data action '{action}'.)"
                    )

            # -----------------------------------
            # SUPPORT AGENT OPERATIONS
            # -----------------------------------
            elif agent == "support":
                # Final answer aggregation
                if action == "final_answer":
                    messages.append({
                        "from": "RouterAgent",
                        "to": "SupportAgent",
                        "content": "build_final_answer(parts)",
                    })
                    final = self.support.build_final_answer(answer_chunks)
                    messages.append({
                        "from": "SupportAgent",
                        "to": "RouterAgent",
                        "content": "returned final user answer",
                    })

                    return {
                        "answer": final,
                        "log": messages,
                        "state": {"messages": messages},
                    }

                # Unknown support action — log and continue
                else:
                    messages.append({
                        "from": "RouterAgent",
                        "to": "SupportAgent",
                        "content": f"Unknown support action '{action}' – step ignored",
                    })
                    answer_chunks.append(
                        f"(Router skipped unknown support action '{action}'.)"
                    )

            # -----------------------------------
            # Unknown agent — log and continue
            # -----------------------------------
            else:
                messages.append({
                    "from": "RouterAgent",
                    "to": "Unknown",
                    "content": f"Unknown agent '{agent}' – step ignored",
                })
                answer_chunks.append(
                    f"(Router skipped unknown agent '{agent}'.)"
                )

        # Fallback — if LLM forgot final_answer step entirely
        messages.append({
            "from": "RouterAgent",
            "to": "SupportAgent",
            "content": "no explicit final_answer step; building answer directly",
        })
        final = self.support.build_final_answer(answer_chunks)
        messages.append({
            "from": "SupportAgent",
            "to": "RouterAgent",
            "content": "returned final user answer (fallback)",
        })

        return {
            "answer": final,
            "log": messages,
            "state": {"messages": messages},
        }
