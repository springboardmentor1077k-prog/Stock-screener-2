from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import sqlite3
import os
import random

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


# ---------- REQUEST MODEL ----------
class PortfolioRequest(BaseModel):
    company_id: int
    quantity: int


# ---------- AUTH ----------
def get_user_id(Authorization: str):
    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = Authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


# ---------- ADD STOCK ----------
@router.post("/add")
def add_stock(data: PortfolioRequest, Authorization: str = Header(...)):

    user_id = get_user_id(Authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # GET CURRENT PRICE → STORE AS BUY PRICE
    cursor.execute("""
        SELECT current_price FROM fundamentals WHERE company_id=?
    """, (data.company_id,))
    
    price_row = cursor.fetchone()
    current_price = float(price_row[0]) if price_row and price_row[0] else 0.0
    variation = random.uniform(0.75, 1.25)
    buy_price = current_price * variation

    cursor.execute("""
        INSERT INTO portfolio (user_id, company_id, quantity, buy_price)
        VALUES (?, ?, ?, ?)
    """, (user_id, data.company_id, data.quantity, buy_price))

    conn.commit()
    conn.close()

    return {"message": "Stock added to portfolio"}

# ---------- DECREASE STOCK ----------
@router.post("/decrease")
def decrease_stock(data: PortfolioRequest, Authorization: str = Header(...)):

    user_id = get_user_id(Authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get latest buy entry
    cursor.execute("""
        SELECT id, quantity FROM portfolio
        WHERE user_id=? AND company_id=?
        ORDER BY added_at DESC
        LIMIT 1
    """, (user_id, data.company_id))

    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Stock not found in portfolio")

    row_id = row[0]
    qty = row[1]

    if qty > 1:
        # Reduce quantity in that row
        cursor.execute("""
            UPDATE portfolio
            SET quantity = quantity - 1
            WHERE id = ?
        """, (row_id,))
    else:
        # Delete only that transaction row
        cursor.execute("""
            DELETE FROM portfolio
            WHERE id = ?
        """, (row_id,))

    conn.commit()
    conn.close()

    return {"message": "Stock decreased"}

# ---------- GET PORTFOLIO ----------
@router.get("/")
def get_portfolio(Authorization: str = Header(...)):

    user_id = get_user_id(Authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            s.symbol,
            s.company_name,
            p.company_id,
            p.quantity,
            p.buy_price,
            f.current_price
        FROM portfolio p
        JOIN symbols s ON p.company_id = s.id
        JOIN fundamentals f ON s.id = f.company_id
        WHERE p.user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    results = []

    for r in rows:
        symbol = r[0]
        company = r[1]
        company_id = r[2]
        quantity = float(r[3] or 0)
        buy_price = float(r[4] or 0)
        current_price = float(r[5] or 0)

        investment_value = quantity * buy_price
        current_value = quantity * current_price
        profit_loss = current_value - investment_value
        profit_percent = (profit_loss / investment_value * 100) if investment_value else 0

        results.append({
            "symbol": symbol,
            "company": company,
            "company_id": company_id,
            "quantity": quantity,
            "buy_price": round(buy_price, 2),
            "current_price": round(current_price, 2),
            "investment_value": round(investment_value, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_percent": round(profit_percent, 2)
        })

    return results


# ---------- DELETE STOCK ----------
@router.delete("/remove")
def remove_stock(company_id: int, Authorization: str = Header(...)):

    user_id = get_user_id(Authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM portfolio
        WHERE user_id=? AND company_id=?
    """, (user_id, company_id))

    conn.commit()
    conn.close()

    return {"message": "Stock removed"}