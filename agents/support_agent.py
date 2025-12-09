

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
