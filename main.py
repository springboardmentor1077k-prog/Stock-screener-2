from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import get_connection
import traceback

app = FastAPI()

# -------- Request Model --------
class QueryRequest(BaseModel):
    query: str

# -------- Mock LLM (NL → DSL) --------
def mock_llm_to_dsl(nl_query: str):
    nl_query = nl_query.lower()

    dsl = {
        "filters": [],
        "sort_by": None,
        "order": "asc",
        "limit": 10
    }

    if "pe ratio less than" in nl_query:
        value = int(nl_query.split("pe ratio less than")[1].split()[0])
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": "<",
            "value": value
        })

    if "descending" in nl_query:
        dsl["order"] = "desc"

    if "limit" in nl_query:
        value = int(nl_query.split("limit")[1].strip())
        dsl["limit"] = value

    dsl["sort_by"] = "pe_ratio"

    return dsl

# -------- DSL Validator --------
def validate_dsl(dsl):
    allowed_fields = ["pe_ratio", "revenue", "ebitda"]

    for f in dsl["filters"]:
        if f["field"] not in allowed_fields:
            raise ValueError("Invalid field in filter")

# -------- DSL → SQL --------
def build_sql_from_dsl(dsl):
    base_query = """
    SELECT s.symbol, s.company_name, f.pe_ratio, f.revenue
    FROM symbols s
    JOIN fundamentals f ON f.company_id = s.id
    """

    conditions = []
    values = []

    for f in dsl["filters"]:
        conditions.append(f"f.{f['field']} {f['operator']} %s")
        values.append(f["value"])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    if dsl["sort_by"]:
        base_query += f" ORDER BY f.{dsl['sort_by']} {dsl['order']}"

    base_query += " LIMIT %s"
    values.append(dsl["limit"])

    return base_query, values

# -------- /query Endpoint --------
@app.post("/query")
def run_query(request: QueryRequest):
    try:
        dsl = mock_llm_to_dsl(request.query)
        validate_dsl(dsl)
        sql, values = build_sql_from_dsl(dsl)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, values)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "dsl": dsl,
            "count": len(results),
            "data": results
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")