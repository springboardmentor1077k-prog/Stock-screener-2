from fastapi import APIRouter, HTTPException, Header
from database_back import get_connection
from jwt_decode import decode_jwt

router = APIRouter()


@router.post("/buy-stock")
def buy_stock(data: dict, authorization: str = Header()):
    try:
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_email = payload.get("email")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s",
            (user_email,)
        )
        user_id = cursor.fetchone()[0]

        # 🏢 Get company_id
        cursor.execute(
            "SELECT symbol_id FROM symbol WHERE company_symbol = %s",
            (data["symbol"],)
        )
        company = cursor.fetchone()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        company_id = company[0]

        buy_qty = int(data["quantity"])
        buy_price = float(data["buy_price"])

        # LIMIT CHECK (max 10 per day)
        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM portfolio
            WHERE user_id = %s AND company_id = %s
            AND DATE(added_on) = CURRENT_DATE
        """, (user_id, company_id))

        today_qty = cursor.fetchone()[0]

        if today_qty + buy_qty > 10:
            raise HTTPException(status_code=400, detail="Daily limit exceeded (max 10 stocks)")

        # Check if already exists
        cursor.execute(
            "SELECT quantity FROM portfolio WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Update quantity
            cursor.execute("""
                UPDATE portfolio
                SET quantity = quantity + %s,
                    buy_price = %s
                WHERE user_id = %s AND company_id = %s
            """, (buy_qty, buy_price, user_id, company_id))
        else:
            #Insert new row
            cursor.execute("""
                INSERT INTO portfolio (user_id, company_id, quantity, buy_price)
                VALUES (%s, %s, %s, %s)
            """, (user_id, company_id, buy_qty, buy_price))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "message": "Stock bought successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))