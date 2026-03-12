from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

import sqlite3
import os

from backend.services.schemas import DSLQuery
from backend.services.llm_parser import parse_natural_language_to_dsl
from backend.services.compiler import compile_dsl_to_sql


app = FastAPI(
    title="AI Stock Screener API",
    description="Natural language stock screener powered by LLM + SQL compiler",
    version="1.0"
)


class QueryRequest(BaseModel):
    query: str


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):

    error_msg = exc.errors()[0].get("msg")

    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "code": "INVALID_FIELD",
            "message": error_msg
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": str(exc)
        }
    )


@app.post("/query")
async def process_query(request: QueryRequest):

    # Step 1: Natural language → DSL
    raw_dsl_dict = parse_natural_language_to_dsl(request.query)

    # Step 2: Validate DSL using Pydantic
    validated_dsl = DSLQuery(**raw_dsl_dict)

    # Step 3: Compile DSL → SQL
    sql_query, params = compile_dsl_to_sql(validated_dsl)

    # Step 4: Database path
    db_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "database",
        "stock_screener.db"
    )

    if not os.path.exists(db_path):
        raise FileNotFoundError("Database file not found")

    # Step 5: Execute query safely
    with sqlite3.connect(db_path) as conn:

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(sql_query, params)

        rows = cursor.fetchall()

    # Step 6: Convert rows → JSON
    results = [dict(row) for row in rows]

    # Step 7: API response
    return {
        "status": "success",
        "parsed_dsl": validated_dsl.model_dump(),
        "count": len(results),
        "data": results,
        "debug": {
            "compiled_sql": sql_query,
            "params": params
        }
    }