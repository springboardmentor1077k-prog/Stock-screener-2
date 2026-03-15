from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


# ADD STOCK TO WATCHLIST
@router.post("/add")
def add_watchlist(company_id: int, authorization: str = Header(...)):

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO watchlist (user_id, company_id)
        VALUES (?, ?)
    """, (user_id, company_id))

    conn.commit()
    conn.close()

    return {"message": "Added to watchlist"}


# GET WATCHLIST
@router.get("/")
def get_watchlist(authorization: str = Header(...)):

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

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


# REMOVE STOCK
@router.delete("/remove")
def remove_watchlist(company_id: int, authorization: str = Header(...)):

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM watchlist
        WHERE user_id=? AND company_id=?
    """, (user_id, company_id))

    conn.commit()
    conn.close()

    return {"message": "Removed"}