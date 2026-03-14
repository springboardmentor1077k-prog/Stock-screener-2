from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.db import get_connection
import traceback
from app.execution_engine import execute_query

app = FastAPI()

# -------- Request Model --------
class QueryRequest(BaseModel):
    query: str


# ==========================================================
# FIELD → TABLE MAPPING DICTIONARY (Required by Task)
# ==========================================================
FIELD_TABLE_MAP = {
    "pe_ratio": ("f", "pe_ratio"),
    "revenue": ("f", "revenue"),
    "ebitda": ("f", "ebitda"),
    "symbol": ("s", "symbol"),
    "company_name": ("s", "company_name")
}


# ==========================================================
# MOCK LLM (Natural Language → DSL)
# ==========================================================
def mock_llm_to_dsl(nl_query: str):
    nl_query = nl_query.lower()

    dsl = {
        "filters": [],
        "sort_by": None,
        "order": "asc",
        "limit": 10
    }

    # Example: "pe ratio less than 20"
    if "pe ratio less than" in nl_query:
        try:
            value = int(nl_query.split("pe ratio less than")[1].split()[0])
            dsl["filters"].append({
                "field": "pe_ratio",
                "operator": "<",
                "value": value
            })
        except:
            pass

    # Sorting
    if "descending" in nl_query:
        dsl["order"] = "desc"

    if "ascending" in nl_query:
        dsl["order"] = "asc"

    # Limit
    if "limit" in nl_query:
        try:
            value = int(nl_query.split("limit")[1].strip())
            dsl["limit"] = value
        except:
            pass

    # Default sorting field
    dsl["sort_by"] = "pe_ratio"

    return dsl


# ==========================================================
# DSL VALIDATOR
# ==========================================================
def validate_dsl(dsl):
    allowed_fields = FIELD_TABLE_MAP.keys()

    for f in dsl["filters"]:
        if f["field"] not in allowed_fields:
            raise ValueError("Invalid field in filter")

    if dsl["sort_by"] and dsl["sort_by"] not in allowed_fields:
        raise ValueError("Invalid sort field")


# ==========================================================
# DSL → SQL COMPILER
# ==========================================================
def build_sql_from_dsl(dsl):
    base_query = """
    SELECT s.symbol, s.company_name, f.pe_ratio, f.revenue
    FROM symbols s
    JOIN fundamentals f ON f.company_id = s.id
    """

    conditions = []
    values = []

    # Build WHERE conditions dynamically
    for f in dsl["filters"]:
        table_alias, column = FIELD_TABLE_MAP[f["field"]]
        conditions.append(f"{table_alias}.{column} {f['operator']} %s")
        values.append(f["value"])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    # ORDER BY
    if dsl["sort_by"]:
        table_alias, column = FIELD_TABLE_MAP[dsl["sort_by"]]
        base_query += f" ORDER BY {table_alias}.{column} {dsl['order']}"

    # LIMIT (always parameterized)
    base_query += " LIMIT %s"
    values.append(dsl["limit"])

    return base_query, values


# ==========================================================
# /query ENDPOINT
# ==========================================================
@app.post("/query")
def run_query(request: QueryRequest):
    try:
        # 1️⃣ NL → DSL
        dsl = mock_llm_to_dsl(request.query)

        # 2️⃣ Validate DSL
        validate_dsl(dsl)

        # 3️⃣ DSL → SQL
        sql, values = build_sql_from_dsl(dsl)

        # 4️⃣ Execute Query
        results = execute_query(sql, values)

        return {
            "status": "success",
            "dsl": dsl,
            "generated_sql": sql,
            "parameters": values,
            "count": len(results),
            "data": results
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )