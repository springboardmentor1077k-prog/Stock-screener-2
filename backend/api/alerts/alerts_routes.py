from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os
import json

from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def get_user_id(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


@router.post("/create")
def create_alert(condition: dict, authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (user_id, condition_json)
        VALUES (?, ?)
    """, (user_id, json.dumps(condition)))

    conn.commit()
    conn.close()

    return {"message": "Alert created"}


@router.get("/")
def get_alerts(authorization: str = Header(...)):

    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, condition_json
        FROM alerts
        WHERE user_id=?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "condition": json.loads(r[1])} for r in rows]