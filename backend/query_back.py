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
    results = execute_query(sql, values)
    
    nl_query = request.nl_query
    # log_query(nl_query, dsl, sql, values, results)
    
    
    logger.info("Structured Query:")
    logger.info("SQL: %s", sql)
    logger.info("VALUES: %s", values)

    
    return {
        "status": "success",
        "message": "Query validated successfully.",
        "count": len(results),
        "data": results
    }