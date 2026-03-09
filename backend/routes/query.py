from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.llm.parser import parse_query
from backend.dsl.validator import validate_dsl
from backend.compiler.sql_compiler import compile_dsl_to_sql
from backend.execution.query_executor import execute_query

router = APIRouter(prefix="/query", tags=["Query"])


class QueryRequest(BaseModel):
    query: str


@router.post("/")
def run_query(request: QueryRequest):

    try:

        # NL → DSL
        dsl = parse_query(request.query)

        # DSL validation
        validate_dsl(dsl)

        # DSL → SQL
        sql, params = compile_dsl_to_sql(dsl)

        # SQL execution
        results = execute_query(sql, params)

        return {
            "dsl": dsl,
            "sql": sql,
            "params": params,
            "results": results
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
    
        print("QUERY PIPELINE ERROR:", str(e))
    
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
