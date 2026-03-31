from fastapi import APIRouter, Header, HTTPException
from backend.services.auth_service import verify_token
from backend.services.llm_parser import parse_natural_language_to_dsl, fallback_parser
from backend.services.compiler import compile_dsl_to_sql
from backend.services.schemas import DSLQuery
from backend.database.db import execute_query

router = APIRouter()


@router.post("/")
async def run_query(payload: dict, authorization: str = Header(...)):

    print("\n================ NEW QUERY =================")

    # ---------- AUTH ----------
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    # ---------- INPUT ----------
    query_text = payload.get("query")

    if not query_text:
        raise HTTPException(status_code=400, detail="Please enter a valid query")

    page = payload.get("page", 1)
    page_size = payload.get("page_size", 5)

    # ---------- SORT ----------

    sort_by = payload.get("sort_by") or dsl.get("sort_by", "pe_ratio")
    order = payload.get("order", "descending")

    # ---------- PARSER ----------
    try:
        dsl = parse_natural_language_to_dsl(query_text)
    except:
        dsl = fallback_parser(query_text)

    # ---------- SAFE STRUCTURE ----------
    if "conditions" not in dsl or not isinstance(dsl["conditions"], list):
        dsl["conditions"] = []

    if "logic" not in dsl:
        dsl["logic"] = "AND"

    if "time_filter" not in dsl:
        dsl["time_filter"] = None

    # ---------- FIELD NORMALIZATION ----------
    FIELD_MAP = {
        "pe ratio": "pe_ratio",
        "pe": "pe_ratio",
        "market cap": "market_cap",
        "profit margin": "profit_margin",
        "price growth": "price_growth"
    }

    cleaned_conditions = []

    # ---------- NORMAL CONDITIONS ----------
    for cond in dsl["conditions"]:
        field = cond.get("field", "").lower().strip()
        field = FIELD_MAP.get(field, field)

        operator = cond.get("operator", ">")
        value = cond.get("value", 0)

        try:
            value = float(value)
        except:
            value = 0

        if field:
            cleaned_conditions.append({
                "field": field,
                "operator": operator,
                "value": value
            })

    # ---------- APPLY ----------
    if cleaned_conditions:
        dsl["conditions"] = cleaned_conditions

    # Do NOT call fallback again here — it will overwrite DSL
    # ---------- VALIDATION ----------
    try:
        dsl_query = DSLQuery(**dsl)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query parameters")
    
    print("FINAL DSL:", dsl_query.model_dump())

    # ---------- SQL ----------
    sql_query, params = compile_dsl_to_sql(
        dsl_query.model_dump(),
        sort_by=sort_by,
        order=order
    )

    print("\nSQL:", sql_query)

    # ---------- DATABASE ----------
    results = await execute_query(sql_query, params)

    print("ROWS:", len(results))

    # ---------- NO RESULTS SAFE MESSAGE ----------
    if not results:
        raise HTTPException(status_code=404, detail="No matching stocks found")
    
    #  ---------- FORCE CORRECT SORTING IN PYTHON ----------
    def clean_number(val):
        try:
            if val is None:
                return 0
            val = str(val).replace(",", "").strip().lower()
            if val == "nan" or val == "":
                return 0
            return float(val)
        except:
            return 0


    if results and sort_by in results[0]:
        results = sorted(
            results,
            key=lambda x: clean_number(x.get(sort_by)),
            reverse=(order == "descending")
        )


    # ---------- PAGINATION (AFTER SORTING) ----------
    start = (page - 1) * page_size
    end = start + page_size
    paginated_results = results[start:end]


    return {
        "data": paginated_results,
        "cached": False,
        "total_results": len(results)
    }

@router.get("/history")
async def get_search_history(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    import sqlite3, os
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query_text
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 4
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return {"history": [r[0] for r in rows]}