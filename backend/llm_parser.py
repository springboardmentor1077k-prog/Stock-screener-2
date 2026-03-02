import os
import json
import re
from google import genai


def generate_dsl(nl_query: str):
    """
    Converts natural language into DSL JSON.
    Only structure generation.
    No validation.
    No DB logic.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY missing")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a STRICT DSL generator.

Convert the user query into JSON with this structure:

{{
  "entity": "fundamentals",
  "logic": "AND | OR",
  "conditions": [
    {{
      "field": "pe | peg | promoter_holding | ebitda | debt_free_cash",
      "operator": "= | != | > | < | >= | <=",
      "value": number
    }},
    {{
      "logic": "AND | OR",
      "conditions": [
        {{
          "field": "...",
          "operator": "...",
          "value": number
        }}
      ]
    }}
  ],
  "limit": 50
}}

Rules:
- Nested logic is allowed.
- If parentheses are present in the query, use nested "conditions".
- Use AND/OR exactly as written in the query.
- Only allowed fields.
- Only allowed operators.
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

        raw = response.text.strip()

        # Remove markdown if Gemini wraps JSON
        cleaned = re.sub(r"```json|```", "", raw).strip()

        dsl = json.loads(cleaned)

        if "error" in dsl:
            return None

        return dsl

    except Exception as e:
        print("GEMINI ERROR:", str(e))
        return None

