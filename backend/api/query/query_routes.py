from fastapi import APIRouter, Header, HTTPException
from backend.services.auth_service import verify_token
from backend.services.llm_parser import parse_natural_language_to_dsl
from backend.services.compiler import compile_dsl_to_sql
from backend.services.schemas import DSLQuery
from backend.database.db import execute_query
from backend.cache.redis_cache import get_cached_query, cache_query

router = APIRouter()


@router.post("/")
async def run_query(payload: dict, authorization: str = Header(...)):

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    query_text = payload.get("query")

    if not query_text:
        raise HTTPException(status_code=400, detail="Query required")

    # ---------- CACHE ----------
    cached = get_cached_query(query_text)

    if cached:
        return {"data": cached, "cached": True}

    # ---------- LLM PARSER ----------
    dsl = parse_natural_language_to_dsl(query_text)

    # ---------- VALIDATION ----------
    dsl_query = DSLQuery(**dsl)

    # ---------- SQL COMPILER ----------
    sql_query, params = compile_dsl_to_sql(dsl_query.model_dump())

    # ---------- DATABASE ----------
    results = await execute_query(sql_query, params)

    # ---------- CACHE ----------
    page = payload.get("page", 1)
    page_size = payload.get("page_size", 5)

    cached = get_cached_query(query_text, page, page_size)

    if cached:
        return {"data": cached, "cached": True}
    
    cache_query(query_text, page, page_size, results)