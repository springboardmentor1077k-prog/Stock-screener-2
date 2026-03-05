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

  Convert the user query into JSON DSL.

  Allowed fields:
  pe, peg, promoter_holding, ebitda, debt_free_cash, revenue, net_profit

  Entity rules:
  - fundamentals → pe, peg, promoter_holding
  - historical_metrics → revenue, ebitda, net_profit, debt_free_cash
  - symbol → when fields belong to both tables

  DSL structure:

  {{
  "entity": "...",
  "logic": "AND",
  "conditions": [
    {{
      "field": "...",
      "operator": "...",
      "value": number
    }}
  ],
  "time_filter": {{
    "type": "last_n_quarters",
    "value": number
  }},
  "limit": 12
  }}

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
  "limit":12
  }}

  User Query:
  show companies with ebitda greater than 1000000

  DSL:
  {{
 "entity":"historical_metrics",
 "logic":"AND",
 "conditions":[
   {{"field":"ebitda","operator":">","value":1000000}}
 ],
 "limit":12
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
 "limit":12
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
            model="gemini-2.5-flash",
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
        return None

