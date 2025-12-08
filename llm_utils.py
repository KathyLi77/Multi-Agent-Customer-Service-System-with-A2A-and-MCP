# llm_utils.py
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# -------------------------------------
# Initialize OpenAI Client
# -------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing. Please set it in your environment.")

client = OpenAI(api_key=API_KEY)

# Toggle debugging
DEBUG_LLM = True


# ============================================================
# Basic LLM Call (text response)
# ============================================================
def ask_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> str:
    """
    Calls OpenAI Chat and returns plain text from the first message.
    Ensures no NoneType issues and strips whitespace.
    """

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content
    if content is None:
        return ""

    text = content.strip()

    if DEBUG_LLM:
        print("\n===== RAW LLM OUTPUT =====")
        print(text)
        print("==========================\n")

    return text


# ============================================================
# LLM JSON Parser (robust)
# ============================================================
def ask_llm_json(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Calls LLM and extracts JSON reliably.
    Strategy:
      1. Read full response
      2. Try to extract the first { ... } block
      3. Try json.loads on extracted segment
      4. Try json.loads on raw full text
      5. Otherwise return {}
    """

    text = ask_llm(system_prompt, user_prompt, model=model)

    # 1. Find first JSON block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_candidate = text[start : end + 1]

        try:
            return json.loads(json_candidate)
        except Exception:
            pass

    # 2. Try parse whole text
    try:
        return json.loads(text)
    except Exception:
        pass

    # 3. Final fallback
    if DEBUG_LLM:
        print("❌ Could not parse JSON from LLM:\n", text)

    return {}

