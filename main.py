from fastapi import FastAPI, Query
from llm_parser import parse_query
from sql_compiler import compile_sql
from query_executor import execute_query

app = FastAPI()


@app.post("/query")
def query(user_query: str = Query(...)):
    try:
        # Step 1: Parse query → DSL
        dsl = parse_query(user_query)

        # Step 2: Convert DSL → SQL
        sql = compile_sql(dsl)

        # Step 3: Execute SQL
        results = execute_query(sql)

        return {
            "status": "success",
            "count": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }