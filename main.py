from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import sqlite3
import os

from schemas import DSLQuery
from llm_parser import parse_natural_language_to_dsl
from compiler import compile_dsl_to_sql

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

# Global Error Handler for Pydantic Validation Errors
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

# Global Error Handler for General/LLM Errors to prevent server crash
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
    # Step 1: Send raw natural language to LLM Parser
    raw_dsl_dict = parse_natural_language_to_dsl(request.query)
    
    # Step 2: Pass output through strict Pydantic Validator
    validated_dsl = DSLQuery(**raw_dsl_dict)
    
    # Step 3: Compile validated DSL into parameterized SQL
    sql_query, params = compile_dsl_to_sql(validated_dsl.model_dump())
    
    # Step 4: Execution Layer - Connect to DB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'stocks.db')
    
    conn = sqlite3.connect(db_path)
    # This row_factory automatically converts database rows into dictionary format
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Execute the query securely
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()

    # 🔥 Ikkada pettu bava mana debugging prints:
    print("🔥 SQL QUERY:", sql_query)
    print("🔥 PARAMS:", params)
    print("🔥 TOTAL ROWS FETCHED:", len(rows))

    # Convert row objects to standard Python dictionaries
    results = [dict(row) for row in rows]

    # Convert row objects to standard Python dictionaries
    results = [dict(row) for row in rows]
    conn.close()
    
    # Step 5: Return the final formatted API response
    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "debug_info": {
            "compiled_sql": sql_query
        }
    }