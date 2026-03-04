import json
import google.generativeai as genai
import os

# Set your API key here or in environment variables
genai.configure(api_key="AIzaSyD8hIifr0Sh0JrHV6aGcX_dlEiOPycpPpU") 

def parse_natural_language_to_dsl(user_query: str) -> dict:
    """
    Sends the user query to LLM and forces it to return ONLY a JSON DSL.
    """
    prompt = f"""
    You are a strictly constrained parser. Convert the following natural language query into a structured DSL JSON format.
    
    Rules:
    1. Output MUST be valid JSON only. Do not include explanations, markdown formatting, or SQL.
    2. Allowed fields: pe_ratio, debt, market_cap, revenue, ebitda, promoter_holding. Do not invent new fields.
    3. Allowed operators: <, >, <=, >=, =.
    4. Logic must be "AND" or "OR".
    
    Expected JSON Structure:
    {{
      "conditions": [
        {{"field": "pe_ratio", "operator": "<", "value": 15}}
      ],
      "logic": "AND"
    }}
    
    User Query: "{user_query}"
    """
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    try:
        response = model.generate_content(prompt)
        # Strip out markdown code blocks if the LLM adds them
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        dsl_dict = json.loads(clean_json)
        return dsl_dict
    except Exception as e:
        # If LLM returns malformed JSON, we raise an error to be handled gracefully
        raise ValueError("LLM returned malformed JSON or failed to parse.")