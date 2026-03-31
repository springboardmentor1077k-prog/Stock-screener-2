from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def get_user_id(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed")

    return user_id


# ---------- ADD TO WATCHLIST ----------
@router.post("/add")
def add_watchlist(company_id: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO watchlist (user_id, company_id)
            VALUES (?, ?)
        """, (user_id, company_id))

        conn.commit()

        if cursor.rowcount == 0:
            return {"message": "Already in watchlist"}
        else:
            return {"message": "Added to watchlist"}

    except:
        raise HTTPException(status_code=500, detail="Unable to add to watchlist")

    finally:
        conn.close()


# ---------- GET WATCHLIST ----------
@router.get("/")
def get_watchlist(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

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
            FROM watchlist w
            JOIN symbols s ON w.company_id = s.id
            JOIN fundamentals f ON s.id = f.company_id
            WHERE w.user_id=?
        """, (user_id,))

        rows = cursor.fetchall()

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
        raise HTTPException(status_code=500, detail="Unable to fetch watchlist")

    finally:
        conn.close()

# ---------- REMOVE FROM WATCHLIST ----------
@router.delete("/remove")
def remove_watchlist(company_id: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM watchlist
            WHERE user_id=? AND company_id=?
        """, (user_id, company_id))

        conn.commit()

        return {"message": "Removed from watchlist"}

    except:
        raise HTTPException(status_code=500, detail="Unable to remove from watchlist")

    finally:
        conn.close()