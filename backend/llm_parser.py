import os
import json
from google import genai


def generate_dsl(nl_query: str):
    """
    Converts natural language into DSL JSON.
    No validation.
    No DB logic.
    Only structure generation.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a STRICT DSL generator.

Convert the user query into JSON with this EXACT structure:

{{
  "entity": "fundamentals",
  "conditions": [
    {{
      "field": "pe | peg | promoter_holding | ebitda | debt_free_cash",
      "operator": "= | != | > | < | >= | <=",
      "value": number
    }}
  ],
  "logic": "AND",
  "limit": 50
}}

Rules:
- If the query contains financial metrics (PE, PEG, EBITDA, promoter holding, debt free cash),
  entity MUST be "fundamentals".
- Only allowed fields.
- Only allowed operators.
- Only AND logic unless multiple conditions require OR.
- Return JSON only.
- If unclear return:
  {{ "error": "QUERY_NOT_UNDERSTOOD" }}

User Query:
{nl_query}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

        dsl = json.loads(response.text)

        if "error" in dsl:
            return None

        return dsl

    except Exception:
        return None