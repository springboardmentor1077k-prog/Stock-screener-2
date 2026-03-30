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
    # --- ADVANCED LOCAL MOCK NLP BYPASS ---
    # Since you don't have an OpenAI key, this smart regex engine localizes
    # simple queries (like "health companies with PE less than 20") locally!
    if not client:
        import re
        q = user_query.lower()
        conditions = []
        
        # Detect PE queries
        if "pe" in q:
            pe_less = re.search(r'(?:<|less|under|below)\s*(?:than\s*)?(\d+)', q)
            if pe_less:
                conditions.append({"field": "pe_ratio", "operator": "<", "value": int(pe_less.group(1))})
            else:
                pe_more = re.search(r'(?:>|greater|above|over)\s*(?:than\s*)?(\d+)', q)
                if pe_more:
                    conditions.append({"field": "pe_ratio", "operator": ">", "value": int(pe_more.group(1))})
        
        # Detect Revenue queries
        if "revenue" in q:
            rev_more = re.search(r'(?:>|greater|above|over)\s*(?:than\s*)?(\d+)', q)
            if rev_more:
                conditions.append({"field": "revenue", "operator": ">", "value": int(rev_more.group(1))})
            else:
                rev_less = re.search(r'(?:<|less|under|below)\s*(?:than\s*)?(\d+)', q)
                if rev_less:
                    conditions.append({"field": "revenue", "operator": "<", "value": int(rev_less.group(1))})
                    
        # Detect Sector categories
        if "health" in q:
            conditions.append({"field": "sector", "operator": "IN", "value": ["Healthcare"]})
        if "tech" in q:
            conditions.append({"field": "sector", "operator": "IN", "value": ["Technology"]})
        if "energy" in q:
             conditions.append({"field": "sector", "operator": "IN", "value": ["Energy"]})
             
        # Fallback if completely unrecognizable
        if not conditions:
            conditions.append({"field": "pe_ratio", "operator": "<", "value": 50}) # Safe default
            
        return {
            "where": {
                "logic": "AND",
                "conditions": conditions
            }
        }
    # -----------------------------------------------
        
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
