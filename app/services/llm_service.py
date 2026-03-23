# app/services/llm_service.py
import json
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a strict JSON DSL generator for a stock screener.

Return ONLY valid JSON in this format:
{
  "logic": "AND",
  "conditions": [
    {"field": "sector", "operator": "=", "value": "IT"},
    {"field": "pe_ratio", "operator": "<", "value": 20}
  ],
  "time_filter": {"range": "last_4_quarters"},
  "limit": 10
}

For growth queries, use special condition types:

1. Growth conditions:
   {"metric": "revenue_growth", "operator": ">", "value": 10, "time_range": "last_4_quarters"}

2. Trend conditions:
   {"direction": "increasing", "confidence": 0.7, "time_range": "last_4_quarters"}

Allowed fields: sector, pe_ratio, peg_ratio, debt_fcf, promoter_holding, revenue, ebitda
Allowed operators: =, <, >, <=, >=, !=
Allowed growth metrics: revenue_growth, profit_growth, avg_revenue_growth
Allowed time ranges: last_quarter, last_4_quarters, last_8_quarters, last_12_quarters
Allowed trend directions: increasing, decreasing, volatile

Examples:
- "Companies with revenue growth > 10%": 
  {"conditions": [{"metric": "revenue_growth", "operator": ">", "value": 10}]}

- "Stocks showing increasing revenue trend": 
  {"conditions": [{"direction": "increasing", "confidence": 0.7}]}

Do not include explanation. Return ONLY the JSON.
"""

def generate_dsl(query: str):
    print("Calling LLM for query:", query)
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    print("LLM RAW OUTPUT:", content)
    
    # Clean the response (remove markdown code blocks if present)
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "")
    elif content.startswith("```"):
        content = content.replace("```", "")
    
    return json.loads(content)