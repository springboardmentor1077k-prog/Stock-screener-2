from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def get_user_id(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


@router.post("/add")
def add_watchlist(company_id: int, authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO watchlist (user_id, company_id)
        VALUES (?, ?)
    """, (user_id, company_id))

    conn.commit()
    conn.close()

    return {"message": "Added to watchlist"}


@router.get("/")
def get_watchlist(authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.symbol, s.company_name
        FROM watchlist w
        JOIN symbols s ON w.company_id = s.id
        WHERE w.user_id=?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{"symbol": r[0], "company": r[1]} for r in rows]


@router.delete("/remove")
def remove_watchlist(company_id: int, authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM watchlist
        WHERE user_id=? AND company_id=?
    """, (user_id, company_id))

    conn.commit()
    conn.close()

    return {"message": "Removed"}