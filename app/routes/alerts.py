# app/routes/alerts.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Request Models
class PriceAlertRequest(BaseModel):
    alert_name: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1, max_length=10)
    operator: str = Field(..., pattern="^(>|<|>=|<=|==|!=)$")
    value: float = Field(..., gt=0)
    notes: Optional[str] = None

class GrowthAlertRequest(BaseModel):
    alert_name: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1, max_length=10)
    metric: str = Field(..., pattern="^(revenue_growth|profit_growth|avg_revenue_growth)$")
    operator: str = Field(..., pattern="^(>|<|>=|<=)$")
    value: float = Field(..., ge=-100, le=1000)
    notes: Optional[str] = None

class ScreenerAlertRequest(BaseModel):
    alert_name: str = Field(..., min_length=1)
    dsl: dict  # The DSL query to run
    notes: Optional[str] = None

@router.post("/price")
async def create_price_alert(
    user_id: int = Query(..., description="User ID"),
    request: PriceAlertRequest = None
):
    """Create price-based alert"""
    try:
        result = AlertService.create_alert(user_id, {
            "alert_type": "price",
            "alert_name": request.alert_name,
            "symbol": request.symbol,
            "operator": request.operator,
            "value": request.value,
            "notes": request.notes
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/growth")
async def create_growth_alert(
    user_id: int = Query(..., description="User ID"),
    request: GrowthAlertRequest = None
):
    """Create growth-based alert"""
    try:
        result = AlertService.create_alert(user_id, {
            "alert_type": "growth",
            "alert_name": request.alert_name,
            "symbol": request.symbol,
            "metric": request.metric,
            "operator": request.operator,
            "value": request.value,
            "notes": request.notes
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_alerts(
    user_id: int = Query(..., description="User ID"),
    alert_type: Optional[str] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get user's alerts"""
    try:
        alerts = AlertService.get_alerts(user_id, alert_type, is_active)
        return {
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    user_id: int = Query(..., description="User ID")
):
    """Delete an alert"""
    try:
        result = AlertService.delete_alert(alert_id, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: int,
    user_id: int = Query(..., description="User ID"),
    is_active: bool = Query(..., description="Enable or disable alert")
):
    """Enable or disable an alert"""
    try:
        result = AlertService.toggle_alert(alert_id, user_id, is_active)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check")
async def check_alerts(
    user_id: Optional[int] = Query(None, description="User ID (optional)")
):
    """Manually trigger alert checking"""
    try:
        triggered = AlertService.check_alerts(user_id)
        return {
            "status": "success",
            "triggered_alerts": triggered,
            "count": len(triggered)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))