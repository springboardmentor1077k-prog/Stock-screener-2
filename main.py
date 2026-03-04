from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from schemas import DSLQuery
from llm_parser import parse_natural_language_to_dsl

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

# Global Error Handler for Pydantic Validation Errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    # Extracts the exact error message we wrote in schemas.py
    error_msg = exc.errors()[0].get("msg")
    
    # Strictly following the PDF error format
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
            "code": "INTERNAL_PARSING_ERROR",
            "message": str(exc)
        }
    )

@app.post("/query")
async def process_query(request: QueryRequest):
    # Step 1: Send raw natural language to LLM Parser
    raw_dsl_dict = parse_natural_language_to_dsl(request.query)
    
    # Step 2: Pass the LLM output through our strict Pydantic Validator (Guardrails)
    # If this fails, the validation_exception_handler above catches it automatically
    validated_dsl = DSLQuery(**raw_dsl_dict)
    
    # Step 3: Return the safely parsed and validated DSL
    return {
        "status": "success",
        "parsed_dsl": validated_dsl.model_dump()
    }