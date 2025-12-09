

# agents/data_agent.py

from typing import Any, Dict, List
import json

from client.mcp_client import call_tool_sync
from llm_utils import ask_llm_json


DATA_AGENT_SYSTEM_PROMPT = """
You are the CustomerDataAgent in a multi-agent customer service system.

You can ONLY act by calling these MCP tools (they already exist in the host):

- get_customer
    args: { "customer_id": <int> }

- list_customers
    args: { "status": <string>, "limit": <int> }

- update_customer
    args: { "customer_id": <int>, "fields": { ... } }

- get_customer_history
    args: { "customer_id": <int> }

- create_ticket
    args: {
      "customer_id": <int>,
      "issue": <string>,
      "priority": "low" | "medium" | "high"
    }

You will receive JSON input from the RouterAgent:

{
  "user_query": "<original user query>",
  "instruction": "<what the Router wants you to do>",
  "messages": [
    {"from": "...", "to": "...", "content": "..."},
    ...
  ]
}

Your job:

1. Decide which of the above tools to call and in what order to achieve the instruction.
2. Use as few steps as reasonably possible (usually 1–4 steps).
3. Produce a small "note" summarizing what you did and what you found.

You MUST output ONLY valid JSON with the following shape:

{
  "steps": [
    {
      "tool": "<tool name from the list>",
      "args": { ... }   // arguments for that tool
    },
    ...
  ],
  "note": "<short natural-language summary of what you did and found>"
}

Rules:
- DO NOT call any tool that is not listed.
- DO NOT include explanations outside of the JSON.
- DO NOT include comments, markdown, or extra keys.
- If you cannot do anything useful, return { "steps": [], "note": "<why>" }.
"""


class CustomerDataAgent:
    """
    CustomerDataAgent:
    - Uses an LLM to plan which MCP tools to call and in what order.
    - Executes those MCP tool calls synchronously.
    """

    def handle(
        self,
        user_query: str,
        messages: List[Dict[str, str]],
        instruction: str,
    ) -> Dict[str, Any]:
        """
        Main LLM entrypoint for the data agent.

        Parameters
        ----------
        user_query:
            Original user query string.
        messages:
            Conversation log so far (router + previous agents).
        instruction:
            Instruction string from RouterAgent describing what to do.

        Returns
        -------
        dict with keys:
          - "note": short textual summary
          - "results": list of {tool, args, result}
          - "messages": updated messages list (including our note, if any)
        """
        # 1) Ask LLM for a JSON plan of tool calls
        payload = {
            "user_query": user_query,
            "instruction": instruction,
            "messages": messages,
        }

        plan = ask_llm_json(
            DATA_AGENT_SYSTEM_PROMPT,
            json.dumps(payload),
        )

        if not isinstance(plan, dict):
            plan = {}

        steps = plan.get("steps", []) or []
        note = plan.get("note", "") or ""

        # 2) Execute the planned tool calls via MCP
        results: List[Dict[str, Any]] = []

        for step in steps:
            if not isinstance(step, dict):
                continue

            tool = step.get("tool")
            args = step.get("args", {}) or {}

            if not tool:
                continue

            # Call MCP tool by name
            tool_result = call_tool_sync(tool, args)

            results.append({
                "tool": tool,
                "args": args,
                "result": tool_result,
            })

        # 3) Add our note to the messages log, if present
        if note:
            messages.append({
                "from": "CustomerDataAgent",
                "to": "RouterAgent",
                "content": note,
            })

        return {
            "note": note,
            "results": results,
            "messages": messages,
        }
