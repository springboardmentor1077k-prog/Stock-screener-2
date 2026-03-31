from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.db import get_connection, release_connection
from backend.auth import verify_token
# Importing the new standardized logic functions
from backend.portfolio_logic import (
    get_current_price, 
    get_multiple_prices,
    clear_price_cache,
    calculate_unrealized_pnl, 
    calculate_average_buy_price, 
    calculate_portfolio_summary,
    calculate_realized_pnl
)
import psycopg2.extras
import logging

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

# --- Models for Input Validation ---

class PortfolioAddRequest(BaseModel):
    user_id: int
    symbol: str
    quantity: int
    buy_price: float

class PortfolioUpdateRequest(BaseModel):
    user_id: int
    symbol: str
    new_quantity: int
    new_buy_price: float

class PortfolioRemoveRequest(BaseModel):
    user_id: int
    symbol: str

# --- Endpoints ---

@router.post("/add")
def add_holding(request: PortfolioAddRequest, username: str = Depends(verify_token)):
    """
    Endpoint 1: Add a new stock holding or update existing with average cost.
    Also records a BUY transaction in the immutable ledger.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            symbol = request.symbol.upper()
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", 
                           (request.user_id, symbol))
            existing = cursor.fetchone()
            
            if existing:
                # Merge: Calculate new average price using standardized logic
                new_qty = existing['quantity'] + request.quantity
                new_avg_price = calculate_average_buy_price(
                    existing['quantity'], float(existing['buy_price']), 
                    request.quantity, request.buy_price
                )
                cursor.execute(
                    "UPDATE portfolio SET quantity=%s, buy_price=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s",
                    (new_qty, new_avg_price, request.user_id, symbol)
                )
            else:
                # Create: New holding
                cursor.execute(
                    "INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (%s, %s, %s, %s)",
                    (request.user_id, symbol, request.quantity, request.buy_price)
                )
            
            # Record transaction (as BUY)
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (%s, %s, 'BUY', %s, %s)",
                (request.user_id, symbol, request.quantity, request.buy_price)
            )
            
            conn.commit()
            return {"message": f"Successfully added {request.quantity} shares of {symbol} to portfolio."}
    finally:
        release_connection(conn)

@router.put("/update")
def update_holding(request: PortfolioUpdateRequest, username: str = Depends(verify_token)):
    """
    Endpoint 2: Update an existing holding and recalculate average buy price.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            symbol = request.symbol.upper()
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", 
                           (request.user_id, symbol))
            existing = cursor.fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail=f"No holding found for {symbol}")
            
            # Recalculate average (assuming this update acts as an additional buy/blend)
            new_qty = existing['quantity'] + request.new_quantity
            new_avg_price = calculate_average_buy_price(
                existing['quantity'], float(existing['buy_price']), 
                request.new_quantity, request.new_buy_price
            )
            
            cursor.execute(
                "UPDATE portfolio SET quantity=%s, buy_price=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s",
                (new_qty, new_avg_price, request.user_id, symbol)
            )
            
            # Record in transactions
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (%s, %s, 'BUY', %s, %s)",
                (request.user_id, symbol, request.new_quantity, request.new_buy_price)
            )
            
            conn.commit()
            return {"message": f"Updated {symbol} holding to {new_qty} shares with new avg price {new_avg_price}"}
    finally:
        release_connection(conn)

@router.delete("/remove")
def remove_holding(request: PortfolioRemoveRequest, username: str = Depends(verify_token)):
    """
    Endpoint 3: Deletes the portfolio entry completely and records a SELL transaction.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            symbol = request.symbol.upper()
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", (request.user_id, symbol))
            existing = cursor.fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail=f"No holding found for {symbol}")
            
            qty = existing['quantity']
            # Calculate realized P&L (assuming we liquidate at current market price)
            current_mkt_price = get_current_price(symbol)
            realized_gain = calculate_realized_pnl(float(existing['buy_price']), current_mkt_price, qty)
            
            # Delete from portfolio
            cursor.execute("DELETE FROM portfolio WHERE user_id=%s AND symbol=%s", (request.user_id, symbol))
            
            # Record transaction (as SELL) with realized P&L
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price, realized_pnl) VALUES (%s, %s, 'SELL', %s, %s, %s)",
                (request.user_id, symbol, qty, current_mkt_price, realized_gain)
            )
            
            conn.commit()
            return {"message": f"Successfully removed {symbol} from portfolio."}
    finally:
        release_connection(conn)

@router.post("/cache/clear")
def clear_portfolio_cache(username: str = Depends(verify_token)):
    """
    Clears the in-memory price cache to force fresh data fetch.
    """
    clear_price_cache()
    return {"message": "Price cache cleared successfully."}

@router.get("/{user_id}")
def get_user_holdings(user_id: int, username: str = Depends(verify_token)):
    """
    Endpoint 4: Fetches all holdings for a user with live price computations using standardized logic.
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT symbol, quantity, buy_price FROM portfolio WHERE user_id=%s", (user_id,))
            holdings = cursor.fetchall()
            
            # Use batch fetch for all symbols at once to optimize performance
            symbols = [h['symbol'] for h in holdings]
            current_prices = get_multiple_prices(symbols)
            
            result = []
            for h in holdings:
                symbol = h['symbol']
                qty = h['quantity']
                avg_buy_price = float(h['buy_price'])
                
                current_price = current_prices.get(symbol, 0.0)
                price_fetched = current_price > 0.0
                
                # Standardized P&L calculation
                pnl_data = calculate_unrealized_pnl(avg_buy_price, current_price, qty)
                
                # Combine results for the API response
                result.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "buy_price": avg_buy_price,
                    "current_price": current_price,
                    "price_fetched": price_fetched,
                    **pnl_data
                })
            
            return result
    finally:
        release_connection(conn)

@router.get("/{user_id}/summary")
def get_portfolio_summary(user_id: int, username: str = Depends(verify_token)):
    """
    Endpoint 5: Combined portfolio summary metrics using standardized aggregate logic.
    """
    # Fetch all holdings first (each with individual calculations)
    holdings = get_user_holdings(user_id, username)
    # Perform aggregation using the new standardized function
    summary = calculate_portfolio_summary(holdings)
    return summary
