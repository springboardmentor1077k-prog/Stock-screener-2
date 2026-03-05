from fastapi import APIRouter, Depends
from sqlalchemy import text

from database import engine
from backend.auth_dependency import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/create")
def create_alert(symbol: str, target_price: float, user=Depends(get_current_user)):

    with engine.begin() as conn:

        company = conn.execute(text("""
            SELECT id FROM symbols
            WHERE symbol = :symbol
        """), {"symbol": symbol}).fetchone()

        if not company:
            return {"error": "Company not found"}

        conn.execute(text("""
            INSERT INTO alerts (company_id, target_price)
            VALUES (:company_id, :target_price)
        """), {
            "company_id": company.id,
            "target_price": target_price
        })

    return {"message": "Alert created"}