from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_parser import generate_dsl
from dsl_validator import validate_dsl
from sql_builder import build_safe_query
import logging
import json


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

    logger.info("Generated DSL:\n%s", json.dumps(dsl, indent=2))

    # Step 2: Validate DSL
    validation_error = validate_dsl(dsl)
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    # Step 3: Convert DSL → SQL (log only)
    sql, values = build_safe_query(dsl)

    logger.info("Structured Query:")
    logger.info("SQL: %s", sql)
    logger.info("VALUES: %s", values)

    # 🔒 Do NOT return DSL or SQL
    return {
        "status": "success",
        "message": "Query validated successfully."
    }