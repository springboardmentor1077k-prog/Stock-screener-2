import os
import json
from openai import OpenAI
from dsl_validator import validate_dsl

def parse_with_llm(nl_query):

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
You are a STRICT DSL generator for a financial screening system.

You must convert the user's natural language query into STRICT JSON DSL.

The output MUST follow this EXACT structure:

{{
  "entity": "symbol | fundamentals | historical_metrics | portfolio | alert",
  "conditions": [
    {{
      "field": "pe | peg | promoter_holding | ebitda | debt_free_cash | created_on",
      "operator": "= | != | > | < | >= | <=",
      "value": number
    }}
  ],
  "logic": "AND | OR",
  "limit": number
}}

CRITICAL RULES:

1. Use ONLY the allowed entities listed above.
2. Use ONLY the allowed fields listed above.
3. Use ONLY the allowed operators.
4. Use ONLY "AND" or "OR" for logic.
5. If query refers to PE, PEG, EBITDA, promoter holding or debt free cash → entity MUST be "fundamentals".
6. Do NOT invent fields.
7. Do NOT invent entities.
8. Do NOT expose database schema.
9. Do NOT add explanations.
10. Do NOT wrap JSON in markdown.
11. If the query cannot be mapped strictly to the allowed DSL, return EXACTLY:

{{
  "error": "QUERY_NOT_UNDERSTOOD"
}}

User Query:
{nl_query}
"""

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)

    raw_output = response.choices[0].message.content.strip()

    return json.loads(raw_output)