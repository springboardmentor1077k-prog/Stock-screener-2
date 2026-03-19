from fastapi import FastAPI, HTTPException, Header, Body
from pydantic import BaseModel
from database_back import get_connection
from jwt_decode import decode_jwt
app = FastAPI()




@app.post("/get-portfolio")
def get_portfolio(authorization: str = Header()):
    try:
        conn = None
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid or missing token")
        
        token = authorization.split(" ")[1]
        payload = decode_jwt(token)
        user_email = payload.get("email")
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name, user_id FROM users WHERE email = %s",
            (user_email,)
        )

        user_row = cursor.fetchone()
        
        
        if not user_row:
            raise HTTPException(status_code=404, detail="user not found Login first")
        
        username = user_row[0]
        user_id = user_row[1]
        
        
        #----------PORTFOLIO DETAILS--------
        
        cursor.execute("""
                SELECT 
                s.company_symbol,
                s.company_name,
                p.quantity,
                p.buy_price
            FROM portfolio p
            JOIN symbol s ON p.company_id = s.symbol_id
            WHERE p.user_id = %s""",
            (user_id,))
        
        
        port_data = cursor.fetchall()
        
        
        portfolio_details = [{
            
                "symbol": r[0],
                "name": r[1],
                "quantity": r[2],
                "buy_price": float(r[3])
            
        }
            for r in port_data]
        
       
        conn.close()

        return {
            "status": "success",
            "username": username,
            "data": portfolio_details
        }

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    
    finally:
        if conn:
            conn.close()
            
            