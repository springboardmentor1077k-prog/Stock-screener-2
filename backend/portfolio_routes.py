from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db import get_connection, release_connection
from backend.auth import verify_token
from backend.portfolio_logic import calculate_new_average_price, fetch_live_price
import psycopg2.extras

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

class TradeAction(BaseModel):
    symbol: str
    quantity: int
    price: float

@router.post("/trade")
def execute_trade(trade: TradeAction, action_type: str, username: str = Depends(verify_token)):
    """Handles both BUY and SELL operations, updating average costs and ledgers."""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            user_obj = cursor.fetchone()
            if not user_obj:
                raise HTTPException(status_code=404, detail="User not found")
            user_id = user_obj['id']

            # 1. Record the action in the immutable ledger
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                (user_id, trade.symbol.upper(), action_type.upper(), trade.quantity, trade.price)
            )

            # 2. Find existing portfolio position
            cursor.execute("SELECT quantity, average_buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", 
                           (user_id, trade.symbol.upper()))
            position = cursor.fetchone()

            if action_type.upper() == "BUY":
                if position:
                    # Update existing position using Average Cost Method
                    old_qty = position['quantity']
                    old_price = position['average_buy_price']
                    new_qty = old_qty + trade.quantity
                    new_avg_price = calculate_new_average_price(old_qty, old_price, trade.quantity, trade.price)
                    
                    cursor.execute(
                        "UPDATE portfolio SET quantity=%s, average_buy_price=%s, last_updated=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s",
                        (new_qty, new_avg_price, user_id, trade.symbol.upper())
                    )
                else:
                    # Create new position
                    cursor.execute(
                        "INSERT INTO portfolio (user_id, symbol, quantity, average_buy_price) VALUES (%s, %s, %s, %s)",
                        (user_id, trade.symbol.upper(), trade.quantity, trade.price)
                    )
            
            elif action_type.upper() == "SELL":
                if not position or position['quantity'] < trade.quantity:
                    raise HTTPException(status_code=400, detail="Not enough shares to sell.")
                
                new_qty = position['quantity'] - trade.quantity
                if new_qty == 0:
                    # Close position completely
                    cursor.execute("DELETE FROM portfolio WHERE user_id=%s AND symbol=%s", (user_id, trade.symbol.upper()))
                else:
                    # Partial sell: quantity decreases, but average_buy_price remains exactly the same!
                    cursor.execute("UPDATE portfolio SET quantity=%s, last_updated=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s", (new_qty, user_id, trade.symbol.upper()))
            
            conn.commit()
            return {"status": "success", "message": f"Successfully executed {action_type} for {trade.symbol}"}
    finally:
        release_connection(conn)

@router.get("/")
def get_portfolio_data(username: str = Depends(verify_token)):
    """Fetches holdings and computes dynamic P&L using live prices."""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            user_obj = cursor.fetchone()
            if not user_obj:
                raise HTTPException(status_code=404, detail="User not found")
            user_id = user_obj['id']
            
            cursor.execute("SELECT symbol, quantity, average_buy_price FROM portfolio WHERE user_id=%s", (user_id,))
            holdings = cursor.fetchall()

            portfolio_data = []
            total_invested = 0.0
            total_current_value = 0.0

            for h in holdings:
                symbol = h['symbol']
                qty = h['quantity']
                avg_price = float(h['average_buy_price'])
                
                live_price = fetch_live_price(symbol)
                
                invested = avg_price * qty
                current_val = live_price * qty
                unrealized_pnl = current_val - invested
                pct_change = ((live_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

                portfolio_data.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "buy_price": avg_price,
                    "current_price": live_price,
                    "pnl": round(unrealized_pnl, 2),
                    "pct_change": round(pct_change, 2),
                    "current_value": round(current_val, 2)
                })
                
                total_invested += invested
                total_current_value += current_val

            return {
                "holdings": portfolio_data,
                "summary": {
                    "total_invested": round(total_invested, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_pnl": round(total_current_value - total_invested, 2),
                    "total_pct_change": round(((total_current_value - total_invested) / total_invested) * 100, 2) if total_invested > 0 else 0
                }
            }
    finally:
        release_connection(conn)
