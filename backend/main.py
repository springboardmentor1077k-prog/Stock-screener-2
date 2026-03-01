from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
import jwt
import json
import redis
import os
from datetime import datetime
from typing import List, Optional
from openai import OpenAI


# CONFIG


app = FastAPI()

ALLOWED_ENTITIES = [
    "symbol",
    "fundamentals",
    "historical_metrics",
    "portfolio",
    "alert"
]

ALLOWED_FIELDS = [
    "pe",
    "peg",
    "promoter_holding",
    "ebitda",
    "debt_free_cash",
    "created_on"
]

ALLOWED_OPERATORS = ["=", "!=", ">", "<", ">=", "<="]
ALLOWED_LOGIC = ["AND", "OR"]


# DATABASE


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )


# REDIS CACHE


cache = redis.Redis(host='localhost', port=6379, decode_responses=True)


# DSL MODEL


class Condition(BaseModel):
    field: str
    operator: str
    value: float

class DSLQuery(BaseModel):
    entity: str
    conditions: List[Condition]
    logic: str
    limit: Optional[int] = 50

class QueryRequest(BaseModel):
    nl_query: str


# LLM PARSER


def parse_with_llm(nl_query: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    Convert the following natural language query into STRICT JSON DSL.
    Only use allowed fields: {ALLOWED_FIELDS}
    Only use allowed operators: {ALLOWED_OPERATORS}
    Only use AND or OR.
    Reject unknown metrics.

    Natural Query:
    {nl_query}

    Output only JSON.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.choices[0].message.content)


# DSL VALIDATION


def validate_dsl(dsl: dict):

    if dsl["entity"] not in ALLOWED_ENTITIES:
        raise HTTPException(status_code=400, detail="Invalid entity")

    if dsl["logic"] not in ALLOWED_LOGIC:
        raise HTTPException(status_code=400, detail="Invalid logic operator")

    for cond in dsl["conditions"]:

        if cond["field"] not in ALLOWED_FIELDS:
            raise HTTPException(status_code=400, detail="Unsupported metric")

        if cond["operator"] not in ALLOWED_OPERATORS:
            raise HTTPException(status_code=400, detail="Invalid operator")

        if not isinstance(cond["value"], (int, float)):
            raise HTTPException(status_code=400, detail="Invalid value type")


# SAFE SQL BUILDER


def build_safe_query(dsl: dict):

    base_query = f"SELECT * FROM {dsl['entity']} WHERE "
    conditions = []
    values = []

    for cond in dsl["conditions"]:
        conditions.append(f"{cond['field']} {cond['operator']} %s")
        values.append(cond["value"])

    final_query = base_query + f" {dsl['logic']} ".join(conditions)
    final_query += f" LIMIT {dsl.get('limit',50)}"

    return final_query, values


# /QUERY ENDPOINT


@app.post("/query")
def query_endpoint(request: QueryRequest):

   
    cache_key = f"rate:{request.nl_query}"
    if cache.get(cache_key):
        raise HTTPException(status_code=429, detail="Too many requests")
    cache.setex(cache_key, 5, "1")

    # 2️⃣ Check cache first
    if cache.get(request.nl_query):
        return {
            "status": "success",
            "source": "cache",
            "data": json.loads(cache.get(request.nl_query))
        }


    try:
        dsl = parse_with_llm(request.nl_query)
    except Exception:
        raise HTTPException(status_code=422, detail="Query not understood")

  
    validate_dsl(dsl)

   
    sql, values = build_safe_query(dsl)

    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Database fetch error")


    response_data = {
        "dsl": dsl,
        "count": len(rows),
        "results": rows
    }


    cache.setex(request.nl_query, 60, json.dumps(response_data))

    return {
        "status": "success",
        "source": "database",
        "data": response_data
    }