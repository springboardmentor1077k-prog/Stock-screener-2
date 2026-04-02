from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
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
import re

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

# --- Models for Input Validation (Task 2) ---

class PortfolioAddRequest(BaseModel):
    user_id: int = Field(..., description="The ID of the user owning the portfolio")
    symbol: str = Field(..., description="Stock symbol (max 20 chars, letters and dots)")
    quantity: int = Field(..., gt=0, description="Positive integer quantity")
    buy_price: float = Field(..., ge=1.0, description="Minimum investment per share is 1.0 to ensure P&L accuracy")

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[a-zA-Z.]+$', v) or len(v) > 20:
             raise ValueError("symbol must be letters/dots only, max 20 characters")
        return v.upper()

class PortfolioUpdateRequest(BaseModel):
    user_id: int = Field(..., description="The ID of the user owning the portfolio")
    symbol: str = Field(..., description="Stock symbol")
    new_quantity: int = Field(..., gt=0, description="Positive integer quantity")
    new_buy_price: float = Field(..., ge=1.0, description="Minimum investment per share is 1.0 to ensure P&L accuracy")

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[a-zA-Z.]+$', v) or len(v) > 20:
             raise ValueError("symbol must be letters/dots only, max 20 characters")
        return v.upper()

class PortfolioRemoveRequest(BaseModel):
    user_id: int = Field(..., description="The ID of the user owning the portfolio")
    symbol: str = Field(..., description="Stock symbol")

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[a-zA-Z.]+$', v) or len(v) > 20:
             raise ValueError("symbol must be letters/dots only, max 20 characters")
        return v.upper()

# --- Endpoints ---

@router.post("/add")
def add_holding(request: PortfolioAddRequest, current_user: dict = Depends(verify_token)):
    """
    Endpoint 1: Add a new stock holding. (Task 3: Ownership check)
    """
    # Task 3: Access Control
    if current_user['user_id'] != request.user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own portfolio.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", 
                           (request.user_id, request.symbol))
            existing = cursor.fetchone()
            
            if existing:
                # Merge holdings
                new_qty = existing['quantity'] + request.quantity
                new_avg_price = calculate_average_buy_price(
                    existing['quantity'], float(existing['buy_price']), 
                    request.quantity, request.buy_price
                )
                # SAFE: parameterized query - no injection risk
                cursor.execute(
                    "UPDATE portfolio SET quantity=%s, buy_price=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s",
                    (new_qty, new_avg_price, request.user_id, request.symbol)
                )
            else:
                # SAFE: parameterized query - no injection risk
                cursor.execute(
                    "INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (%s, %s, %s, %s)",
                    (request.user_id, request.symbol, request.quantity, request.buy_price)
                )
            
            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (%s, %s, 'BUY', %s, %s)",
                (request.user_id, request.symbol, request.quantity, request.buy_price)
            )
            
            conn.commit()
            return {"message": f"Successfully added {request.quantity} shares of {request.symbol} to portfolio."}
    finally:
        release_connection(conn)

@router.put("/update")
def update_holding(request: PortfolioUpdateRequest, current_user: dict = Depends(verify_token)):
    # Task 3: Access Control
    if current_user['user_id'] != request.user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own portfolio.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", 
                           (request.user_id, request.symbol))
            existing = cursor.fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail=f"No holding found for {request.symbol}")
            
            new_qty = existing['quantity'] + request.new_quantity
            new_avg_price = calculate_average_buy_price(
                existing['quantity'], float(existing['buy_price']), 
                request.new_quantity, request.new_buy_price
            )
            
            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "UPDATE portfolio SET quantity=%s, buy_price=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND symbol=%s",
                (new_qty, new_avg_price, request.user_id, request.symbol)
            )
            
            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price) VALUES (%s, %s, 'BUY', %s, %s)",
                (request.user_id, request.symbol, request.new_quantity, request.new_buy_price)
            )
            
            conn.commit()
            return {"message": f"Updated {request.symbol} holding to {new_qty} shares with new avg price {new_avg_price}"}
    finally:
        release_connection(conn)

@router.delete("/remove")
def remove_holding(request: PortfolioRemoveRequest, current_user: dict = Depends(verify_token)):
    # Task 3: Access Control
    if current_user['user_id'] != request.user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own portfolio.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute("SELECT quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s", (request.user_id, request.symbol))
            existing = cursor.fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail=f"No holding found for {request.symbol}")
            
            qty = existing['quantity']
            current_mkt_price = get_current_price(request.symbol)
            realized_gain = calculate_realized_pnl(float(existing['buy_price']), current_mkt_price, qty)
            
            # SAFE: parameterized query - no injection risk
            cursor.execute("DELETE FROM portfolio WHERE user_id=%s AND symbol=%s", (request.user_id, request.symbol))
            
            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price, realized_pnl) VALUES (%s, %s, 'SELL', %s, %s, %s)",
                (request.user_id, request.symbol, qty, current_mkt_price, realized_gain)
            )
            
            conn.commit()
            return {"message": f"Successfully removed {request.symbol} from portfolio."}
    finally:
        release_connection(conn)

@router.post("/cache/clear")
def clear_portfolio_cache(current_user: dict = Depends(verify_token)):
    clear_price_cache()
    return {"message": "Price cache cleared successfully."}

@router.get("/{user_id}")
def get_user_holdings(user_id: int, current_user: dict = Depends(verify_token)):
    # Task 3: Access Control
    if current_user['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own portfolio.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute("SELECT symbol, quantity, buy_price FROM portfolio WHERE user_id=%s", (user_id,))
            holdings = cursor.fetchall()
            
            symbols = [h['symbol'] for h in holdings]
            current_prices = get_multiple_prices(symbols)
            
            result = []
            for h in holdings:
                symbol = h['symbol']
                qty = h['quantity']
                avg_buy_price = float(h['buy_price'])
                current_price = current_prices.get(symbol, 0.0)
                price_fetched = current_price > 0.0
                pnl_data = calculate_unrealized_pnl(avg_buy_price, current_price, qty)
                result.append({
                    "symbol": symbol, "quantity": qty, "buy_price": avg_buy_price,
                    "current_price": current_price, "price_fetched": price_fetched, **pnl_data
                })
            
            return result
    finally:
        release_connection(conn)

@router.get("/{user_id}/summary")
def get_portfolio_summary(user_id: int, current_user: dict = Depends(verify_token)):
    # Task 3: Access Control checked implicitly by calling get_user_holdings
    holdings = get_user_holdings(user_id, current_user)
    summary = calculate_portfolio_summary(holdings)
    return summary
