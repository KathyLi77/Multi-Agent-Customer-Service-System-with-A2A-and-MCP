
# agents/router_agent.py

from typing import Any, Dict, List, Optional
import json

from llm_utils import ask_llm_json
from agents.data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent


ROUTER_SYSTEM_PROMPT = """
You are the RouterAgent in a multi-agent customer service system.

Sub-agents:

1) CustomerDataAgent (short name: "data")
   - Handles ALL interactions with the customer database and tickets
     via MCP tools (get_customer, list_customers, update_customer,
     get_customer_history, create_ticket).
   - You should send it a clear instruction like:
       "Verify this customer, update their email, and fetch their ticket history."

2) SupportAgent (short name: "support")
   - Generates the final user-facing explanation of what happened.
   - Takes the user query, conversation log, and data agent results,
     and crafts a friendly answer + A2A log.

INPUT to you (RouterAgent) will be JSON:

{
  "user_query": "<original user query>",
  "messages": [
    {"from": "User", "to": "RouterAgent", "content": "..."}
  ]
}

You MUST respond with ONLY valid JSON of the form:

{
  "need_data": true or false,
  "data_instruction": "<string>",
  "support_instruction": "<string>"
}

Semantics:

- need_data:
    true  -> you expect the CustomerDataAgent to run MCP tools.
    false -> you think no data calls are required (SupportAgent can answer directly).

- data_instruction:
    A short natural-language description of what the CustomerDataAgent should do
    (e.g., "Look up customer 10, update their email to X, then show their ticket history.").

- support_instruction:
    Brief guidance for what the SupportAgent should emphasize in the final answer
    (e.g., "Explain that we updated their email and summarize their open tickets.").

Rules:
- ALWAYS include all three keys: need_data, data_instruction, support_instruction.
- DO NOT include explanations outside the JSON.
- DO NOT include comments or markdown.
- If you set need_data=false, data_instruction can be "".

If the data_results and data_note indicate that the data agent could not
perform the requested actions or retrieve the requested data, you must:

- Explain the limitation or failure clearly but briefly.
- Avoid pretending that the operation succeeded.
- Suggest what the user can do next (e.g., check their ID, contact human support, try a simpler query).

IMPORTANT:
- Include exactly ONE "A2A LOG" section.
- Do NOT print the full raw conversation log.
- Keep the A2A LOG high-level and concise.


"""


class RouterAgent:
    """
    RouterAgent:
    - Uses an LLM to decide how to delegate work to sub-agents.
    - Calls CustomerDataAgent (LLM + MCP tools) when needed.
    - Calls SupportAgent (LLM) to produce the final user-facing answer.
    """

    def __init__(self) -> None:
        self.data = CustomerDataAgent()
        self.support = SupportAgent()

    def route(self, query: str) -> Dict[str, Any]:
        """
        Public entrypoint used by tests.
        """
        return self.run(query)

    def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        High-level orchestration:

        1) Log user's message.
        2) Ask Router LLM how to delegate (need_data, instructions).
        3) Optionally call CustomerDataAgent.handle() (LLM + MCP tools).
        4) Call SupportAgent.build_final_answer() (LLM).
        5) Return final answer + log + state (messages).
        """
        messages: List[Dict[str, str]] = [
            {"from": "User", "to": "RouterAgent", "content": query}
        ]

        # 1) Ask Router LLM for delegation plan
        router_payload = {
            "user_query": query,
            "messages": messages,
        }

        plan = ask_llm_json(
            ROUTER_SYSTEM_PROMPT,
            json.dumps(router_payload),
        )

        if not isinstance(plan, dict):
            plan = {}

        need_data = bool(plan.get("need_data", True))
        data_instruction = plan.get("data_instruction", "") or ""
        support_instruction = plan.get("support_instruction", "") or ""

        # 2) Optionally call the data agent (LLM + MCP tools)
        data_output: Dict[str, Any] = {
            "note": "",
            "results": [],
            "messages": messages,
        }

        if need_data:
            messages.append({
                "from": "RouterAgent",
                "to": "CustomerDataAgent",
                "content": data_instruction or "Handle this user request using MCP tools.",
            })

            data_output = self.data.handle(
                user_query=query,
                messages=messages,
                instruction=data_instruction or query,
            )

            # keep updated messages list from data agent
            messages = data_output.get("messages", messages)

        # 3) Call the support agent (LLM) for the final answer
        messages.append({
            "from": "RouterAgent",
            "to": "SupportAgent",
            "content": support_instruction or "Generate the final answer for the user.",
        })

        final_answer = self.support.build_final_answer(
            user_query=query,
            messages=messages,
            data_output=data_output,
        )

        messages.append({
            "from": "SupportAgent",
            "to": "RouterAgent",
            "content": "Returned final user answer.",
        })

        return {
            "answer": final_answer,
            "log": messages,
            "state": {"messages": messages},
        }
