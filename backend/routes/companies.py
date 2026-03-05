from fastapi import APIRouter
from sqlalchemy import text
from database import engine
from backend.cache import redis_client
import json

router = APIRouter(prefix="/companies", tags=["Companies"])


# ---------------------------------------
# Get all companies (CACHED)
# ---------------------------------------
@router.get("/")
def get_companies():

    cache_key = "companies_list"

    # 1️⃣ Check Redis cache
    cached_data = redis_client.get(cache_key)

    if cached_data:
        return json.loads(cached_data)

    # 2️⃣ Fetch from database
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, symbol, company_name, sector
            FROM symbols
        """)).fetchall()

    companies = [
        {
            "id": r.id,
            "symbol": r.symbol,
            "company_name": r.company_name,
            "sector": r.sector
        }
        for r in rows
    ]

    # 3️⃣ Store in Redis (TTL = 60 seconds)
    redis_client.setex(cache_key, 60, json.dumps(companies))

    return companies


# ---------------------------------------
# Get single company
# ---------------------------------------
@router.get("/{symbol}")
def get_company(symbol: str):

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT id, symbol, company_name, sector
            FROM symbols
            WHERE symbol = :symbol
        """), {"symbol": symbol.upper()}).fetchone()

    if not row:
        return {"error": "Company not found"}

    return {
        "id": row.id,
        "symbol": row.symbol,
        "company_name": row.company_name,
        "sector": row.sector
    }