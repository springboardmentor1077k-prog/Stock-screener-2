from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from database import engine
from backend.auth_dependency import get_current_user

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


# -----------------------------
# Add stock to portfolio
# -----------------------------
@router.post("/create")
def create_portfolio(symbol: str, quantity: int, user=Depends(get_current_user)):

    with engine.begin() as conn:

        # find company id
        company = conn.execute(text("""
            SELECT id FROM symbols
            WHERE symbol = :symbol
        """), {"symbol": symbol}).fetchone()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # insert portfolio row
        conn.execute(text("""
            INSERT INTO portfolio (user_id, company_id, quantity)
            VALUES (:user_id, :company_id, :quantity)
        """), {
            "user_id": user["id"],
            "company_id": company.id,
            "quantity": quantity
        })

    return {"message": "Stock added to portfolio"}


# -----------------------------
# Get my portfolio
# -----------------------------
@router.get("/")
def get_portfolio(user=Depends(get_current_user)):

    with engine.connect() as conn:

        rows = conn.execute(text("""
            SELECT s.symbol, p.quantity
            FROM portfolio p
            JOIN symbols s ON p.company_id = s.id
            WHERE p.user_id = :user_id
        """), {"user_id": user["id"]}).fetchall()

    return rows