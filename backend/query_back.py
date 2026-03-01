from fastapi import FastAPI
from pydantic import BaseModel
import redis
import json

from database_back import get_connection
from llm_parser import parse_with_llm
from dsl_validator import validate_dsl
from sql_builder import build_safe_query
from error_handel import structured_error

app = FastAPI()
cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

class QueryRequest(BaseModel):
    nl_query: str

@app.post("/query")
def query_endpoint(request: QueryRequest):

    # Rate limiting
    rate_key = f"rate:{request.nl_query}"
    if cache.get(rate_key):
        structured_error(429, "RATE_LIMIT_EXCEEDED",
                         "Too many requests. Try later.")
    cache.setex(rate_key, 5, "1")

    # Cache check
    if cache.get(request.nl_query):
        return {
            "status": "success",
            "source": "cache",
            "data": json.loads(cache.get(request.nl_query))
        }

    # LLM Parse
    try:
        dsl = parse_with_llm(request.nl_query)
    except:
        structured_error(422, "QUERY_NOT_UNDERSTOOD",
                         "Unable to interpret query")

    # Validate DSL
    error = validate_dsl(dsl)
    if error:
        structured_error(400, error,
                         "Invalid DSL structure")

    # Build SQL
    sql, values = build_safe_query(dsl)

    # DB Execution
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except:
        structured_error(500, "DATABASE_FETCH_ERROR",
                         "Unable to retrieve data")

    response = {
        "dsl": dsl,
        "count": len(rows),
        "results": rows
    }

    cache.setex(request.nl_query, 60, json.dumps(response))

    return {
        "status": "success",
        "source": "database",
        "data": response
    }