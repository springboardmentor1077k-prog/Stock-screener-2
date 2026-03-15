from execution_layer import run_query
from fastapi import FastAPI
from execution_layer import run_query

app = FastAPI()

@app.get("/query")

def query_data(sql_query: str):

    result = run_query(sql_query)

    return result
