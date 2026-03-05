from fastapi import APIRouter
from sqlalchemy import text
from database import engine

router = APIRouter()


@router.get("/companies")
def get_companies():

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, symbol, company_name, sector
            FROM symbols
        """)).fetchall()

    companies = []

    for r in rows:
        companies.append({
            "id": r[0],
            "symbol": r[1],
            "company_name": r[2],
            "sector": r[3]
        })

    return companies


@router.get("/companies/{symbol}")
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
        "id": row[0],
        "symbol": row[1],
        "company_name": row[2],
        "sector": row[3]
    }