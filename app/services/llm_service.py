import json
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a strict JSON DSL generator.

Return ONLY valid JSON in this format:
{
  "logic": "AND",
  "conditions": [
    {"field": "pe_ratio", "operator": "<", "value": 10}
  ],
  "limit": 10
}

Allowed fields:
sector, pe_ratio, peg_ratio, debt_fcf, promoter_holding, revenue, ebitda

Do not include explanation.
"""

def generate_dsl(query: str):
    print("1st")
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    print("2nd")

    content = response.choices[0].message.content
    print("LLM RAW OUTPUT:", content)
    print("3rd")
    return json.loads(content)