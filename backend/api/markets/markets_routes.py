from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def verify_user(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    return user_id


# ---------- GET ALL COMPANIES ----------
@router.get("/")
def get_markets(authorization: str = Header(...)):
    verify_user(authorization)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                s.id,
                s.symbol,
                s.company_name,
                s.sector,
                f.pe_ratio,
                f.market_cap,
                f.revenue,
                f.ebitda,
                f.profit_margin
            FROM symbols s
            JOIN fundamentals f ON s.id = f.company_id
            ORDER BY s.company_name
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "company_id": r[0],
                "symbol": r[1],
                "company_name": r[2],
                "sector": r[3],
                "pe_ratio": r[4],
                "market_cap": r[5],
                "revenue": r[6],
                "ebitda": r[7],
                "profit_margin": r[8]
            }
            for r in rows
        ]

    except:
        raise HTTPException(status_code=500, detail="Unable to fetch markets data")