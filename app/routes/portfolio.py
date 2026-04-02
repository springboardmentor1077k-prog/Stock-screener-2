# app/routes/portfolio.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# Request Models
class AddStockRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Purchase price per share")
    notes: Optional[str] = Field(None, description="Optional notes")

class RemoveStockRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol to remove")
    quantity: Optional[int] = Field(None, gt=0, description="Quantity to sell (None = sell all)")

class WatchlistRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    alert_price: Optional[float] = Field(None, gt=0, description="Price alert threshold")
    notes: Optional[str] = None

# API Endpoints
@router.post("/add")
async def add_stock(
    user_id: int = Query(..., description="User ID"),
    request: AddStockRequest = None
):
    """Add stock to portfolio"""
    try:
        result = PortfolioService.add_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            notes=request.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/remove")
async def remove_stock(
    user_id: int = Query(..., description="User ID"),
    request: RemoveStockRequest = None
):
    """Remove stock from portfolio (full or partial sell)"""
    try:
        result = PortfolioService.remove_stock(
            user_id=user_id,
            symbol=request.symbol,
            quantity=request.quantity
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/holdings")
async def get_portfolio(
    user_id: int = Query(..., description="User ID"),
    include_transactions: bool = Query(False, description="Include transaction history")
):
    """Get user's complete portfolio with valuations"""
    try:
        result = PortfolioService.get_portfolio(user_id, include_transactions)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/summary")
async def get_portfolio_summary(
    user_id: int = Query(..., description="User ID")
):
    """Get portfolio summary statistics only"""
    try:
        result = PortfolioService.get_portfolio_summary(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "summary": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/transactions")
async def get_transactions(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of transactions to return")
):
    """Get transaction history"""
    try:
        transactions = PortfolioService.get_transaction_history(user_id, limit)
        return {
            "status": "success",
            "user_id": user_id,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/watchlist/add")
async def add_to_watchlist(
    user_id: int = Query(..., description="User ID"),
    request: WatchlistRequest = None
):
    """Add stock to watchlist"""
    try:
        result = PortfolioService.add_to_watchlist(
            user_id=user_id,
            symbol=request.symbol,
            alert_price=request.alert_price,
            notes=request.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/watchlist")
async def get_watchlist(
    user_id: int = Query(..., description="User ID")
):
    """Get user's watchlist"""
    try:
        result = PortfolioService.get_watchlist(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/watchlist/remove")
async def remove_from_watchlist(
    user_id: int = Query(..., description="User ID"),
    symbol: str = Query(..., description="Stock symbol to remove")
):
    """Remove stock from watchlist"""
    try:
        result = PortfolioService.remove_from_watchlist(user_id, symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")