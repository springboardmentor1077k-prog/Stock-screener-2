import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time
import logging

load_dotenv()

# We strictly initialize the client, but fail gracefully if key is missing during dev
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key and api_key != "your-openai-api-key-here" else None

# Bottleneck 1: Configurable timeout
OPENAI_TIMEOUT = 10 # seconds

# Task 1: LLM Response Cache
LLM_CACHE = {}
LLM_CACHE_LIMIT = 100
LLM_CACHE_TIMEOUT = 300 # 5 minutes
LLM_CACHE_HITS = 0
LLM_CACHE_MISSES = 0

def get_llm_cache_size():
    return len(LLM_CACHE)

def get_llm_cache_stats():
    return {"hits": LLM_CACHE_HITS, "misses": LLM_CACHE_MISSES}

def clear_llm_cache():
    LLM_CACHE.clear()

def parse_nl_to_dsl(user_query: str) -> dict:
    """
    Takes natural language query and ONLY returns strict JSON format.
    Checks the in-memory cache first to avoid expensive API calls.
    """
    global LLM_CACHE_HITS, LLM_CACHE_MISSES
    cache_key = user_query.lower().strip()
    now = time.time()
    
    if cache_key in LLM_CACHE:
        timestamp, cached_dsl = LLM_CACHE[cache_key]
        if now - timestamp < LLM_CACHE_TIMEOUT:
            LLM_CACHE_HITS += 1
            logging.info("LLM cache hit — skipping API call")
            return cached_dsl
        else:
            del LLM_CACHE[cache_key]
            
    LLM_CACHE_MISSES += 1
    result = _parse_nl_to_dsl_internal(user_query)
    
    # Store in cache if no parsing error
    if "error" not in result:
        if len(LLM_CACHE) >= LLM_CACHE_LIMIT:
            oldest_key = min(LLM_CACHE.keys(), key=lambda k: LLM_CACHE[k][0])
            del LLM_CACHE[oldest_key]
        LLM_CACHE[cache_key] = (now, result)
        
    return result

def _fallback_local_parser(user_query: str) -> dict:
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
         
    # Detect time filters specifically
    time_filter = None
    q_match = re.search(r'last\s+(\d+)\s+quarters?', q)
    if q_match:
        time_filter = {
            "type": "last_m_quarters",
            "value": int(q_match.group(1))
        }
        
    if not conditions:
        return {"error": "Could not understand the query. Try something like: Show me stocks with PE ratio less than 20"}
        
    result = {
        "where": {
            "logic": "AND",
            "conditions": conditions
        }
    }
    
    if time_filter:
        result["time_filter"] = time_filter
        
    return result

def _parse_nl_to_dsl_internal(user_query: str) -> dict:
    """
    Takes natural language query and ONLY returns strict JSON format.
    No SQL generation, no database access, no extra text formatting.
    """
    if not client:
        return _fallback_local_parser(user_query)
    # -----------------------------------------------
        
    system_prompt = """
    You are an AI Stock Screener parser. Your ONLY job is to convert natural language to strict JSON DSL.
    
    Allowed fields: pe_ratio, revenue, ebitda, debt_to_equity, revenue_growth, eps_growth
    Allowed operators: =, !=, <, <=, >, >=
    
    Format:
    {
      "where": {
        "conditions": [
          {"field": "...", "operator": "...", "value": 123}
        ],
        "logic": "AND"
      },
      "time_filter": {
        "type": "last_m_quarters",
        "value": 4
      }
    }
    
    CRITICAL RULES:
    1. Output pure JSON only. No markdown, no conversation, no markdown blocks like ```json.
    2. Do NOT generate SQL.
    3. Do NOT make up fields. Only use the allowed fields.
    4. "time_filter" is optional. Only include it if the user asks for a specific timeframe in quarters, e.g. "last 4 quarters".
    5. The value for time_filter must be an integer between 1 and 12.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0,  # We want deterministic, robotic answers
            timeout=OPENAI_TIMEOUT  # Bottleneck 1: 10s timeout
        )
        
        strict_json_string = response.choices[0].message.content.strip()
        dsl_object = json.loads(strict_json_string)
        return dsl_object
        
    except json.JSONDecodeError:
        return _fallback_local_parser(user_query)
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            # Bottleneck 1: Explicit timeout error
            return {"error": "Query processing timed out. Please try a simpler query."}
        
        logging.warning(f"OpenAI failed, falling back. Error: {e}")
        return _fallback_local_parser(user_query)
