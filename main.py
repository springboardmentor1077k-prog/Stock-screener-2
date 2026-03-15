from fastapi import FastAPI

from llm_parser import parse_query
from validator import validate_dsl
from sql_compiler import compile_sql
from query_executor import execute_query
from result_formatter import format_results

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Stock AI Backend Running"}


@app.post("/query")
def query(user_query: str):

    try:

        dsl = parse_query(user_query)

        validate_dsl(dsl)

        sql, params = compile_sql(dsl)

        rows = execute_query(sql, params)

        result = format_results(rows)

        return result

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }