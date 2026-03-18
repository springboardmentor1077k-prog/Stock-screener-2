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
    print("USING GEMINI KEY:", api_key[:15])

    client = genai.Client(api_key=api_key)


   
    prompt = f"""
  You are a STRICT DSL generator.

  Convert the user query into JSON DSL.

  Allowed fields:
  pe, peg, promoter_holding, ebitda, debt_free_cash, revenue, net_profit
  
  
  Additional derived fields:
  revenue_growth, ebitda_growth, net_profit_growth, debt_free_cash_growth
  
  Growth rules:

1. If the query mentions "growth", "increase", "decrease", "change", "trend":
   → use *_growth fields

Examples:
- "revenue growth > 10%" → field = revenue_growth
- "ebitda increased by 5%" → field = ebitda_growth
- "profit growth" → field = net_profit_growth

2. Growth ALWAYS requires time context.
If time is missing, assume last 4 quarters.

3. Growth queries MUST use:
→ entity = historical_metrics (or symbol if mixed with fundamentals)

4. Growth value is always in percentage.


Examples:


User Query:
show companies with revenue growth greater than 10%

  DSL:
  {{
 "entity":"historical_metrics",
 "logic":"AND",
 "conditions":[
   {{"field":"revenue_growth","operator":">","value":10}}
 ],
 "time_filter":{{
   "type":"last_n_quarters",
   "value":4
 }},
 "limit":20
  }}
  

  User Query:
  show companies with revenue growth above 15% in last 4 quarters

  DSL:
  {{
  "entity":"historical_metrics",
  "logic":"AND",
  "conditions":[
   {{"field":"revenue_growth","operator":">","value":15}}
  ],
  "time_filter":{{
   "type":"last_n_quarters",
   "value":4
  }},
  "limit":20
  }}
  
  
  User Query:
  show companies with increasing revenue trend over last 4 quarters

  DSL:
  {{
 "entity":"historical_metrics",
 "analysis":"trend",
 "metric":"revenue",
 "direction":"increase",
 "period":4,
 "limit":20
  }}
  
  
  
  User Query:
  show companies with pe < 20 and revenue growth above 10% in last 4 quarters

  DSL:
  {{
 "entity":"symbol",
 "logic":"AND",
 "conditions":[
   {{"field":"pe","operator":"<","value":20}},
   {{"field":"revenue_growth","operator":">","value":10}}
 ],
 "time_filter":{{
   "type":"last_n_quarters",
   "value":4
 }},
 "limit":20
}}


  Entity rules:

  1. fundamentals
  Use when the query asks for current snapshot financial metrics.
  Fields:
  pe, peg, promoter_holding, ebitda, debt_free_cash

  Example:
  show companies with ebitda > 1000
  → entity = fundamentals

  2. historical_metrics
  Use ONLY when the query explicitly refers to time.

  Examples of time phrases:
  last quarter
  last N quarters
  last year
  past months
  historical trend

  Fields:
  revenue, ebitda, net_profit, debt_free_cash

  Example:
  show companies with ebitda greater than 100000 in the last 3 quarters
  → entity = historical_metrics

  3. symbol
  Use when the query mixes metrics that come from different tables.

  Example:
show companies with pe < 20 and revenue last 3 quarters
→ entity = symbol

Important rule:

- If query has NO time → fundamentals
- If query has time → historical_metrics
- If query has growth → ALWAYS historical_metrics (or symbol if mixed)

Time rule:

If the query contains a time condition such as:
last N quarters, last year, past months

then include:

"time_filter": {{
  "type": "last_n_quarters",
  "value": N
}}

If no time condition exists, do NOT include time_filter.


  Examples:

  User Query:
  show companies with pe less than 20

  DSL:
  {{
  "entity":"fundamentals",
  "logic":"AND",
  "conditions":[
   {{"field":"pe","operator":"<","value":20}}
  ],
  "limit":20
  }}

  User Query:
  show companies with ebitda greater than 1000000

DSL:
{{
 "entity":"fundamentals",
 "logic":"AND",
 "conditions":[
   {{"field":"ebitda","operator":">","value":1000000}}
 ],
 "limit":20
}}

User Query:
show companies with pe < 50 and ebitda for the past 3 quarters

  DSL:
  {{
 "entity":"symbol",
 "logic":"AND",
 "conditions":[
   {{"field":"pe","operator":"<","value":50}},
   {{"field":"ebitda","operator":">","value":0}}
 ],
 "time_filter": {{
   "type":"last_n_quarters",
   "value":3
  }},
 "limit":20
  }}

  Rules:
  Return JSON only.
  If query cannot be parsed return:
  {{ "error":"QUERY_NOT_UNDERSTOOD" }}

  User Query:
  {nl_query}
  """    
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

        raw = response.text.strip()

        # Remove markdown if Gemini wraps JSON
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        dsl = json.loads(cleaned)
        print("RAW LLM OUTPUT:", raw)
        print("CLEANED JSON:", cleaned)

        if "error" in dsl:
            return None

        return dsl

    except Exception as e:
        print("GEMINI ERROR:", str(e))

        if "429" in str(e):
          return {"error": "RATE_LIMIT_EXCEEDED"}

        return {"error": "QUERY_NOT_UNDERSTOOD"}

