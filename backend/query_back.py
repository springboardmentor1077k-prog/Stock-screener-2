from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_parser import generate_dsl
from dsl_validator import validate_dsl
from sql_builder import build_safe_query
from execution import execute_query
import logging
import json
import redis
import json
from datetime import datetime
from decimal import Decimal

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


r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

#Cache using redis
def generate_cache_key(sql, values):
    key = sql + "|" + json.dumps(values, sort_keys=True)
    return f"query_cache:{hash(key)}"



def serialize_results(results):
    def convert(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj

    return json.dumps(results, default=convert)




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

class QueryRequest(BaseModel):
    nl_query: str


@app.post("/query")
def query_endpoint(request: QueryRequest):

    # Step 1: Generate DSL
    dsl = generate_dsl(request.nl_query)
    
    
    if not dsl:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "code": "QUERY_NOT_UNDERSTOOD",
                "message": "We could not understand your query. Please retype it clearly using supported financial metrics."
            }
        )
    print("DSL OUTPUT:", dsl)

    logger.info("Generated DSL:\n%s", json.dumps(dsl, indent=2))

    # Step 2: Validate DSL
    validation_error = validate_dsl(dsl)
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    # Step 3: Convert DSL → SQL 
    result = build_safe_query(dsl)

    if not result:
        raise HTTPException(
        status_code=500,
        detail={"message": "Failed to build query"}
    )

    sql, values = result
    cache_key = generate_cache_key(sql, values)
    cached_data = r.get(cache_key)
    
    if cached_data:
        logger.info("CACHE HIT .....")
        results = json.loads(cached_data)
        
        
    else:
        logger.info("CACHE MISS  going to querying DB")
        results = execute_query(sql, values)
        
        r.setex(
        cache_key,
        300,  
        serialize_results(results)
    )
         
        
    
    # nl_query = request.nl_query
   
    
    
    logger.info("Structured Query:")
    logger.info("SQL: %s", sql)
    logger.info("VALUES: %s", values)

    
    return {
        "status": "success",
        "message": "Query validated successfully.",
        "count": len(results),
        "data": results
    }