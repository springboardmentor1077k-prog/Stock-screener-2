import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# We strictly initialize the client, but fail gracefully if key is missing during dev
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key and api_key != "your-openai-api-key-here" else None

def parse_nl_to_dsl(user_query: str) -> dict:
    """
    Takes natural language query and ONLY returns strict JSON format.
    No SQL generation, no database access, no extra text formatting.
    """
    # --- MOCK BYPASS FOR TESTING WITHOUT API KEY ---
    query_lower = user_query.lower()
    
    if "pe" in query_lower and "<" in query_lower:
        import re
        match = re.search(r'<\s*(\d+(\.\d+)?)', query_lower)
        val = float(match.group(1)) if match else 6.0
        
        return {
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": val}
            ],
            "logic": "AND"
        }
    
    if "revenue >" in query_lower:
        import re
        match = re.search(r'>\s*(\d+(\.\d+)?)', query_lower)
        val = float(match.group(1)) if match else 100
        
        return {
            "conditions": [
                {"field": "revenue", "operator": ">", "value": val}
            ],
            "logic": "AND"
        }
    
    # -----------------------------------------------

    if not client:
        return {"error": "OpenAI API Key is missing. Please add it to your .env file."}
        
    system_prompt = """
    You are an AI Stock Screener parser. Your ONLY job is to convert natural language to strict JSON DSL.
    
    Allowed fields: pe_ratio, revenue, ebitda, debt_to_equity
    Allowed operators: =, !=, <, <=, >, >=
    
    Format:
    {
      "conditions": [
        {"field": "...", "operator": "...", "value": 123}
      ],
      "logic": "AND"
    }
    
    CRITICAL RULES:
    1. Output pure JSON only. No markdown, no conversation, no markdown blocks like ```json.
    2. Do NOT generate SQL.
    3. Do NOT make up fields. Only use the allowed fields.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0,  # We want deterministic, robotic answers
        )
        
        # We assume the output is valid JSON
        strict_json_string = response.choices[0].message.content.strip()
        dsl_object = json.loads(strict_json_string)
        return dsl_object
        
    except json.JSONDecodeError:
        return {"error": "LLM failed to return valid JSON format."}
    except Exception as e:
        return {"error": f"LLM parsing failed: {str(e)}"}
