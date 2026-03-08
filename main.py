from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from schemas import DSLQuery
from llm_parser import parse_natural_language_to_dsl

app = FastAPI()

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
            "code": "INTERNAL_PARSING_ERROR",
            "message": str(exc)
        }
    )


@app.post("/query")
async def process_query(request: QueryRequest):

    raw_dsl_dict = parse_natural_language_to_dsl(request.query)

    validated_dsl = DSLQuery(**raw_dsl_dict)

    return {
        "status": "success",
        "parsed_dsl": validated_dsl.model_dump()
    }