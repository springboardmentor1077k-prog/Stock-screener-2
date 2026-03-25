import json
import google.generativeai as genai
import os
from functools import lru_cache  

genai.configure(api_key="AIzaSyD8hIifr0Sh0JrHV6aGcX_dlEiOPycpPpU") 

# @lru_cache adds in-memory caching. 
@lru_cache(maxsize=100)
def parse_natural_language_to_dsl(user_query: str) -> dict:
    prompt = f"""
    You are a strictly constrained parser. Convert the following natural language query into a structured DSL JSON format.
    
    Rules:
    1. Output MUST be valid JSON only.
    2. Allowed fields: pe_ratio, debt, market_cap, revenue, ebitda, promoter_holding, revenue_growth.
    3. Allowed operators: <, >, <=, >=, =.
    4. Logic must be "AND" or "OR".
    5. If the user asks for historical trends (e.g., "last 4 quarters"), include "time_filter": "last_4_quarters".
    
    Expected JSON Structure:
    {{
      "conditions": [
        {{"field": "revenue_growth", "operator": ">", "value": 10}}
      ],
      "logic": "AND",
      "time_filter": "last_4_quarters"
    }}
    
    User Query: "{user_query}"
    """
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        dsl_dict = json.loads(clean_json)
        return dsl_dict
    except Exception as e:
        raise ValueError("LLM returned malformed JSON or failed to parse.")