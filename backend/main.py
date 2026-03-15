from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

import sqlite3
import os
import logging
import json

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

from backend.services.sentiment_service import get_market_news

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware


# -----------------------------
# LOGGING CONFIGURATION
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# RATE LIMITER
# -----------------------------
limiter = Limiter(key_func=get_remote_address)


# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(
    title="AI Stock Screener API",
    description="Natural language stock screener powered by LLM + SQL compiler",
    version="1.0"
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# -----------------------------
# REGISTER ROUTERS
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(watchlist_router, prefix="/watchlist", tags=["Watchlist"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])


# -----------------------------
# REQUEST MODEL
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 5


# -----------------------------
# DATABASE PATH
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {"message": "AI Stock Screener API is running"}


# -----------------------------
# HEALTH
# -----------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# -----------------------------
# MARKET NEWS
# -----------------------------
@app.get("/news/{company}")
def get_news(company: str):
    return get_market_news(company)


# -----------------------------
# ERROR HANDLING
# -----------------------------
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
            "message": str(exc)
        }
    )


# -----------------------------
# MAIN QUERY ENDPOINT
# -----------------------------
@app.post("/query")
@limiter.limit("10/minute")
async def process_query(
    request: QueryRequest,
    authorization: str = Header(...)
):

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]

    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    logger.info(f"User {user_id} query: {request.query}")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError("Database file not found")

    # -----------------------------
    # CACHE
    # -----------------------------
    cached = get_cached_query(request.query)

    if cached:
        logger.info("Cache hit for query")
        return cached

    # -----------------------------
    # QUERY INTERPRETER
    # -----------------------------
    interpreted_query = interpret_query(request.query)

    logger.info(f"Interpreted Query: {interpreted_query}")

    # -----------------------------
    # NL → DSL
    # -----------------------------
    raw_dsl_dict = parse_natural_language_to_dsl(interpreted_query)

    validated_dsl = DSLQuery(**raw_dsl_dict)

    logger.info(f"Parsed DSL: {validated_dsl.model_dump()}")

    # -----------------------------
    # SQL COMPILER
    # -----------------------------
    sql_query, params = compile_dsl_to_sql(validated_dsl.model_dump())

    page = max(request.page, 1)
    page_size = max(min(request.page_size, 50), 1)

    offset = (page - 1) * page_size

    sql_query += " LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    # -----------------------------
    # EXECUTE SQL
    # -----------------------------
    with sqlite3.connect(DB_PATH) as conn:

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(sql_query, params)
        rows = cursor.fetchall()

        cursor.execute("""
        INSERT INTO search_history (user_id, query_text, parsed_dsl)
        VALUES (?, ?, ?)
        """, (
            user_id,
            request.query,
            json.dumps(validated_dsl.model_dump())
        ))

        conn.commit()

    log_query(request.query, sql_query)

    results = [dict(row) for row in rows]

    response_data = {
        "status": "success",
        "user_id": user_id,
        "parsed_dsl": validated_dsl.model_dump(),
        "page": page,
        "page_size": page_size,
        "count": len(results),
        "data": results
    }

    cache_query(request.query, response_data)

    return response_data


# -----------------------------
# USER SEARCH HISTORY
# -----------------------------
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