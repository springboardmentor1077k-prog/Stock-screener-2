from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

import sqlite3
import os
import logging
import json
import re
import time

from backend.services.schemas import DSLQuery
from backend.services.llm_parser import parse_natural_language_to_dsl
from backend.services.compiler import compile_dsl_to_sql
from backend.services.query_interpreter import interpret_query
from backend.services.auth_service import verify_token
from backend.cache.redis_cache import get_cached_query, cache_query
from backend.utils.query_logger import log_query

from backend.api.auth.auth_routes import router as auth_router
from backend.api.watchlist.watchlist_routes import router as watchlist_router
from backend.api.alerts.alerts_routes import router as alerts_router
from backend.api.markets.markets_routes import router as markets_routes
from backend.api.portfolio.portfolio_routes import router as portfolio_router

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from contextlib import asynccontextmanager
import threading
from backend.api.alerts.alerts_routes import background_alert_checker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=background_alert_checker)
    thread.daemon = True
    thread.start()
    yield


app = FastAPI(
    title="AI Stock Screener API",
    description="Natural language stock screener powered by LLM + SQL compiler",
    version="1.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(watchlist_router, prefix="/watchlist", tags=["Watchlist"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(markets_routes, prefix="/markets", tags=["Markets"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio"])


class QueryRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 5
    sort_by: str | None = None
    order: str = "descending"


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


@app.get("/")
def root():
    return {"message": "AI Stock Screener API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    error_msg = exc.errors()[0].get("msg")

    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "code": "INVALID_FIELD",
            "message": error_msg
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong. Please try again later."
        }
    )


@app.post("/query")
@limiter.limit("10/minute")
async def process_query(
    request: Request,
    body: QueryRequest,
    authorization: str = Header(...)
):

    # ---------- AUTH ----------
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    logger.info(f"User {user_id} query: {body.query}")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError("Database file not found")

    page = max(body.page, 1)
    page_size = max(min(body.page_size, 50), 1)

    # ---------- SORT ----------
    allowed_sort_fields = [
        "pe_ratio",
        "market_cap",
        "revenue",
        "profit_margin",
        "ebitda"
    ]

    sort_by = body.sort_by if body.sort_by in allowed_sort_fields else "pe_ratio"
    order = body.order if body.order in ["ascending", "descending"] else "descending"


    # ---------- PARSE ----------
    interpreted_query = interpret_query(body.query)
    raw_dsl_dict = parse_natural_language_to_dsl(interpreted_query)

    # ---------- SAFE CONDITIONS ----------
    conditions = raw_dsl_dict.get("conditions", [])
    if not isinstance(conditions, list):
        conditions = []

    words = body.query.lower().split()

    # ---------- FORCE PE FILTER ----------
    pe_match = re.search(r"pe\s*ratio\s*(less than|<)\s*(\d+)", body.query.lower())

    if pe_match:
        conditions.append({
            "field": "pe_ratio",
            "operator": "<",
            "value": float(pe_match.group(2))
        })

    # ---------- FORCE SECTOR ----------
    if "it" in words or "technology" in words:
        conditions.append({
            "field": "sector",
            "operator": "=",
            "value": "Technology"
        })

    raw_dsl_dict["conditions"] = conditions

    # ---------- VALIDATION ----------
    validated_dsl = DSLQuery(**raw_dsl_dict)

    
    # ---------- CACHE ----------
    cache_key = f"{validated_dsl.model_dump()}:{sort_by}:{order}:{page}:{page_size}"

    cached = get_cached_query(cache_key, page, page_size)
    if cached:
        logger.info("Cache hit")
        return cached

    # ---------- SQL ----------
    base_sql, base_params = compile_dsl_to_sql(
        validated_dsl.model_dump(),
        sort_by=sort_by,
        order=order
    )

    # ---------- PAGINATION ----------
    offset = (page - 1) * page_size

    paginated_sql = base_sql + " LIMIT ? OFFSET ?"
    paginated_params = base_params + [page_size, offset]

    # ---------- COUNT QUERY ----------

    if base_params:
        count_sql = base_sql.split("ORDER BY")[0]
        count_sql = f"SELECT COUNT(*) FROM ({count_sql}) as subquery"
    else:
        # No filters → fast count
        count_sql = """
        SELECT COUNT(*)
        FROM symbols s
        JOIN fundamentals f ON s.id = f.company_id
        """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if base_params:
            cursor.execute(count_sql, base_params)
        else:
            cursor.execute(count_sql)

        total_results = cursor.fetchone()[0]


        start_time = time.time()

        cursor.execute(paginated_sql, paginated_params)
        rows = cursor.fetchall()

        end_time = time.time()
        execution_time = end_time - start_time

        logger.info(f"Query Execution Time: {execution_time:.4f} seconds")

        cursor.execute("""
        INSERT INTO search_history (user_id, query_text, parsed_dsl)
        VALUES (?, ?, ?)
        """, (
            user_id,
            body.query,
            json.dumps(validated_dsl.model_dump())
        ))

        conn.commit()

    log_query(body.query, paginated_sql, execution_time)

    results = [dict(row) for row in rows]

    response_data = {
        "status": "success",
        "user_id": user_id,
        "parsed_dsl": validated_dsl.model_dump(),
        "page": page,
        "page_size": page_size,
        "total_results": total_results,
        "count": len(results),
        "data": results
    }

    # ---------- CACHE STORE ----------
    cache_query(cache_key, page, page_size, response_data)

    return response_data


@app.get("/history")
def get_search_history(authorization: str = Header(...)):

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT query_text, created_at
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """, (user_id,))

        rows = cursor.fetchall()

    return [dict(row) for row in rows]