from fastapi import APIRouter, HTTPException, Header
from database_back import get_connection
from jwt_decode import decode_jwt
router = APIRouter()

@router.post("/sell-stock")
def sell_stock(data: dict, authorization: str = Header()):
    try:
        # 🔐 Extract token
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_email = payload.get("email")

        conn = get_connection()
        cursor = conn.cursor()

        # 👤 Get user_id
        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s",
            (user_email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user[0]

        # 🏢 Get company_id
        cursor.execute(
            "SELECT symbol_id FROM symbol WHERE company_symbol = %s",
            (data["symbol"],)
        )
        company = cursor.fetchone()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        company_id = company[0]

        sell_qty = int(data["quantity"])

        # 📊 Get current quantity
        cursor.execute(
            "SELECT quantity FROM portfolio WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Stock not in portfolio")

        current_qty = row[0]

        # ❌ Prevent oversell
        if sell_qty > current_qty:
            raise HTTPException(status_code=400, detail="Not enough shares")

        # 🔥 SELL LOGIC
        if sell_qty == current_qty:
            # Delete row (Sell All)
            cursor.execute(
                "DELETE FROM portfolio WHERE user_id = %s AND company_id = %s",
                (user_id, company_id)
            )
        else:
            # Reduce quantity
            cursor.execute(
                """
                UPDATE portfolio 
                SET quantity = quantity - %s 
                WHERE user_id = %s AND company_id = %s
                """,
                (sell_qty, user_id, company_id)
            )

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "message": "Sell executed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





