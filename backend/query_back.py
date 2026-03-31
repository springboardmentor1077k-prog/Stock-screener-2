from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llm_parser import generate_dsl
from dsl_validator import validate_dsl
from sql_builder import build_safe_query
from execution import execute_query
import logging
import json
import redis
from datetime import datetime
from decimal import Decimal
import hashlib



#Debug Log
'''
def log_query(prompt, dsl, sql, values, results):

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "dsl": dsl,
        "sql": sql,
        "values": values,
        "results": results
    }

    with open("logs_outputs/query_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
'''


r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

#Cache using redis
def generate_cache_key(sql, values):
    
    key = sql + json.dumps(values, sort_keys=True)
    return "query_cache:" + hashlib.md5(key.encode()).hexdigest()


#LLM cache

def get_nl_cache_key(nl_query: str):
    return "nl_cache:" + hashlib.md5(nl_query.strip().lower().encode()).hexdigest()


def serialize_results(results):
    def convert(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    return json.dumps(results, default=convert)





def validate_dsl_rules(dsl: dict, nl_query: str = ""):

    print("VALIDATING DSL:", dsl)
    if not dsl:
        query = nl_query.lower()

        
        if any(word in query for word in ["tcs", "infosys", "reliance", "hdfc"]):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "COMPANY_NOT_ALLOWED",
                    "message": "Company-specific queries are not allowed.",
                    "suggestion": "Use only financial filters like: pe less than 20"
                }
            )

        
        if "growth" in query and not any(op in query for op in [">", "<", "above", "below"]):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "GROWTH_DIRECTION_MISSING",
                    "message": "Growth direction not specified.",
                    "suggestion": "Example: revenue growth greater than 10%"
                }
            )

        import re
        match = re.search(r"\b(\d+)\s*quarter", query)
        if match and int(match.group(1)) > 4:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "TIME_EXCEEDS_LIMIT",
                    "message": "Maximum allowed time range is 4 quarters.",
                    "suggestion": "Use up to last 4 quarters"
                }
            )

       
        raise HTTPException(
            status_code=422,
            detail={
                "error": "QUERY_NOT_UNDERSTOOD",
                "message": "We could not understand your query.",
                "suggestion": "Try: pe less than 20 AND peg greater than 1"
            }
        )

    

    if "company" in dsl:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "COMPANY_NOT_ALLOWED",
                "message": "Company-specific queries are not allowed.",
                "suggestion": "Use only financial filters"
            }
        )

    conditions = dsl.get("conditions", [])

    if any("growth" in c.get("field", "") for c in conditions):
        if not any(c.get("operator") in [">", "<", "="] for c in conditions):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "GROWTH_DIRECTION_MISSING",
                    "message": "Growth direction not specified.",
                    "suggestion": "Example: revenue_growth greater than 10"
                }
            )

    time_filter = dsl.get("time_filter")

    if time_filter and time_filter.get("value", 0) > 4:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "TIME_EXCEEDS_LIMIT",
                "message": "Maximum allowed time range is 4 quarters.",
                "suggestion": "Use up to last 4 quarters"
            }
        )

    return True


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

class QueryRequest(BaseModel):
    nl_query: str


@router.post("/query")
def query_endpoint(request: QueryRequest):
    
    # Step 1: Generate DSL
    nl_query = request.nl_query.strip()
    nl_cache_key = get_nl_cache_key(nl_query)
    cached_dsl = r.get(nl_cache_key)
    if cached_dsl:
        logger.info("NL CACHE HIT (Skipping LLM)")
        dsl = json.loads(cached_dsl)
        
    else:
        logger.info("NL CACHE MISS → calling LLM")

        dsl = generate_dsl(nl_query)
        
        # if not dsl:
        #     raise HTTPException(
        #     status_code=422,
        #     detail={
        #         "status": "error",
        #         "code": "QUERY_NOT_UNDERSTOOD",
        #         "message": "We could not understand your query. Please retype it clearly using supported financial metrics."
        #     }
        # )
        
        
        
        
        validate_dsl_rules(dsl, nl_query)
        print("DSL OUTPUT:", dsl)
        logger.info("Generated DSL:\n%s", json.dumps(dsl, indent=2))

        # store DSL
        r.setex(nl_cache_key, 300, json.dumps(dsl))
    
    

    

    # Step 2: Validate DSL
    validation_error = validate_dsl(dsl)
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    # Step 3: Convert DSL ----> SQL 
    result = build_safe_query(dsl)

    if not result:
        raise HTTPException(
        status_code=500,
        detail={"message": "Failed to build query"}
    )

    sql, values = result
    
    
    #Step 4: SQL ----> Result  
    cache_key = generate_cache_key(sql, values)
    cached_data = r.get(cache_key)
    
    if cached_data:
        logger.info("CACHE HIT .....")
        return json.loads(cached_data)
        
        
    else:
        logger.info("CACHE MISS  going to querying DB")
        results = execute_query(sql, values)
        response = {
        "status": "success",
        "count": len(results),
        "data": results}
        
        
        r.setex(
        cache_key,
        300,  
        json.dumps(response, default=str)
    )
         
    
    logger.info("Structured Query:")
    logger.info("SQL: %s", sql)
    logger.info("VALUES: %s", values)

    
    return {
        "status": "success",
        "message": "Query validated successfully.",
        "count": len(results),
        "data": results
    }