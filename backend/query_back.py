from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from llm_parser import generate_dsl
from dsl_validator import validate_dsl
from sql_builder import build_safe_query

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
                "message": "Unable to interpret query"
            }
        )

    print("\n GENERATED DSL:")
    print(dsl)

    # Step 2: Validate DSL
    validation_error = validate_dsl(dsl)

    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    # Step 3: Convert DSL → Structured Query (SQL)
    sql, values = build_safe_query(dsl)

    print("\n STRUCTURED QUERY:")
    print("SQL:", sql)
    print("VALUES:", values)

    # Only return structured information (no DB execution)
    return {
        "status": "success",
        "dsl": dsl,
        "structured_query": {
            "sql": sql,
            "values": values
        }
    }