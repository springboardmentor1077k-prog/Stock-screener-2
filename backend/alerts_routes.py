from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from backend.db import get_connection, release_connection
from backend.auth import verify_token
import psycopg2.extras
import logging

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# --- Models ---
class AlertCreate(BaseModel):
    user_id: int
    symbol: str
    threshold_price: float = Field(..., gt=0)
    alert_type: str = Field(..., regex="^(PRICE_ABOVE|PRICE_BELOW)$")

class AlertUpdate(BaseModel):
    alert_id: int
    threshold_price: float = Field(..., gt=0)
    alert_type: str = Field(..., regex="^(PRICE_ABOVE|PRICE_BELOW)$")

# --- Endpoints ---

@router.post("/create")
def create_alert(data: AlertCreate, current_user: dict = Depends(verify_token)):
    if current_user['user_id'] != data.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized alert creation.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "INSERT INTO alerts (user_id, symbol, threshold_price, alert_type, is_active) VALUES (%s, %s, %s, %s, TRUE)",
                (data.user_id, data.symbol.upper(), data.threshold_price, data.alert_type)
            )
            conn.commit()
            return {"status": "success", "message": f"Alert created for {data.symbol}."}
    finally:
        release_connection(conn)

@router.get("/{user_id}")
def get_user_alerts(user_id: int, current_user: dict = Depends(verify_token)):
    if current_user['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # SAFE: parameterized query - no injection risk
            cursor.execute("SELECT id, symbol, threshold_price, alert_type, is_active FROM alerts WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
            alerts = cursor.fetchall()
            return {"status": "success", "data": alerts}
    finally:
        release_connection(conn)

@router.put("/update")
def update_alert(data: AlertUpdate, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cursor:
            # Check ownership
            cursor.execute("SELECT user_id FROM alerts WHERE id=%s", (data.alert_id,))
            row = cursor.fetchone()
            if not row or row[0] != current_user['user_id']:
                raise HTTPException(status_code=403, detail="Access denied.")

            # SAFE: parameterized query - no injection risk
            cursor.execute(
                "UPDATE alerts SET threshold_price=%s, alert_type=%s, is_active=TRUE WHERE id=%s",
                (data.threshold_price, data.alert_type, data.alert_id)
            )
            conn.commit()
            return {"status": "success", "message": "Alert updated successfully."}
    finally:
        release_connection(conn)

@router.delete("/remove/{alert_id}")
def remove_alert(alert_id: int, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM alerts WHERE id=%s", (alert_id,))
            row = cursor.fetchone()
            if not row or row[0] != current_user['user_id']:
                raise HTTPException(status_code=403, detail="Access denied.")

            # SAFE: parameterized query - no injection risk
            cursor.execute("DELETE FROM alerts WHERE id=%s", (alert_id,))
            conn.commit()
            return {"status": "success", "message": "Alert deleted."}
    finally:
        release_connection(conn)

@router.patch("/resolve/{alert_id}")
def resolve_alert(alert_id: int, current_user: dict = Depends(verify_token)):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM alerts WHERE id=%s", (alert_id,))
            row = cursor.fetchone()
            if not row or row[0] != current_user['user_id']:
                raise HTTPException(status_code=403, detail="Access denied.")

            # SAFE: parameterized query - no injection risk
            cursor.execute("UPDATE alerts SET is_active=FALSE WHERE id=%s", (alert_id,))
            conn.commit()
            return {"status": "success", "message": "Alert resolved."}
    finally:
        release_connection(conn)
