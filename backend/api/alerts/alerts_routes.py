from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os
import json
import threading
import time


from backend.services.auth_service import verify_token

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


# ---------- AUTH ----------
def get_user_id(authorization: str):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id


# ---------- ALERT EVALUATION ----------
def evaluate_condition(condition, cursor):
    symbol = condition["symbol"]
    metric = condition["metric"]
    operator = condition["operator"]
    value = float(condition["value"])

    cursor.execute("""
        SELECT 
            f.current_price AS current_price,
            f.pe_ratio AS pe_ratio,
            f.revenue AS revenue,
            f.profit_margin AS profit_margin
        FROM fundamentals f
        JOIN symbols s ON s.id = f.company_id
        WHERE s.symbol = ?
        ORDER BY f.report_date DESC
        LIMIT 1
    """, (symbol,))

    row = cursor.fetchone()
    if not row:
        return False

    data = {
        "current_price": float(row["current_price"]),
        "pe_ratio": float(row["pe_ratio"]),
        "revenue": float(row["revenue"]),
        "profit_margin": float(row["profit_margin"])
    }

    if metric not in data:
        return False

    actual_value = data[metric]

    if operator == ">":
        return actual_value > value
    elif operator == "<":
        return actual_value < value
    elif operator == ">=":
        return actual_value >= value
    elif operator == "<=":
        return actual_value <= value
    elif operator == "==":
        return actual_value == value

    return False


# ---------- HELPER: FORMAT TRIGGER MESSAGE ----------
def format_trigger_message(condition):
    metric_names = {
        "current_price": "Current Price",
        "pe_ratio": "P/E Ratio",
        "revenue": "Revenue",
        "profit_margin": "Profit Margin"
    }

    operator_text = {
        ">": "went above",
        "<": "went below",
        ">=": "reached or went above",
        "<=": "reached or went below",
        "==": "became equal to"
    }

    metric = metric_names.get(condition["metric"], condition["metric"])
    operator = operator_text.get(condition["operator"], condition["operator"])
    value = condition["value"]

    return f"{condition['symbol']} triggered: {metric} {operator} {value}"


# ---------- CREATE ALERT ----------
@router.post("/create")
def create_alert(condition: dict, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    required_fields = ["symbol", "metric", "operator", "value"]
    for field in required_fields:
        if field not in condition:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (user_id, condition_json, is_active)
        VALUES (?, ?, 1)
    """, (user_id, json.dumps(condition)))

    conn.commit()
    conn.close()

    return {"message": "Alert created"}


# ---------- GET ALL ALERTS ----------
@router.get("/")
def get_alerts(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, condition_json, is_active, created_at, triggered_message, triggered_at
        FROM alerts
        WHERE user_id=?
        ORDER BY is_active DESC, created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    alerts = []
    for row in rows:
        alerts.append({
            "id": row["id"],
            "condition": json.loads(row["condition_json"]),
            "is_active": row["is_active"],
            "created_at": row["created_at"],
            "triggered_message": row["triggered_message"],
            "triggered_at": row["triggered_at"]
        })

    return alerts


# ---------- GET ACTIVE ALERTS ----------
@router.get("/active")
def get_active_alerts(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, condition_json, created_at
        FROM alerts
        WHERE user_id=? AND is_active=1
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    alerts = []
    for row in rows:
        alerts.append({
            "id": row["id"],
            "condition": json.loads(row["condition_json"]),
            "created_at": row["created_at"]
        })

    return alerts


# ---------- GET TRIGGERED ALERTS ----------
@router.get("/triggered")
def get_triggered_alerts(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, condition_json, triggered_message, triggered_at
        FROM alerts
        WHERE user_id=? AND is_active=0
        ORDER BY triggered_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    alerts = []
    for row in rows:
        alerts.append({
            "id": row["id"],
            "condition": json.loads(row["condition_json"]),
            "triggered_message": row["triggered_message"],
            "triggered_at": row["triggered_at"]
        })

    return alerts


# ---------- DELETE ALERT ----------
@router.delete("/delete/{alert_id}")
def delete_alert(alert_id: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM alerts
        WHERE id = ? AND user_id = ?
    """, (alert_id, user_id))

    conn.commit()
    conn.close()

    return {"message": "Alert deleted"}


# ---------- DEACTIVATE ALERT ----------
@router.put("/deactivate/{alert_id}")
def deactivate_alert(alert_id: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET is_active = 0
        WHERE id = ? AND user_id = ?
    """, (alert_id, user_id))

    conn.commit()
    conn.close()

    return {"message": "Alert deactivated"}


# ---------- REACTIVATE ALERT ----------
@router.put("/reactivate/{alert_id}")
def reactivate_alert(alert_id: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET is_active = 1,
            triggered_message = NULL,
            triggered_at = NULL
        WHERE id = ? AND user_id = ?
    """, (alert_id, user_id))

    conn.commit()
    conn.close()

    return {"message": "Alert reactivated"}


# ---------- GET SYMBOLS ----------
@router.get("/symbols")
def get_symbols():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, company_name FROM symbols")
    rows = cursor.fetchall()
    conn.close()

    return [{"symbol": r[0], "name": r[1]} for r in rows]


# ---------- CHECK ALERTS ----------
@router.get("/check")
def check_alerts(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, condition_json
        FROM alerts
        WHERE user_id=? AND is_active=1
    """, (user_id,))

    rows = cursor.fetchall()
    triggered_now = []

    for row in rows:
        alert_id = row["id"]
        condition = json.loads(row["condition_json"])

        cursor.execute("SELECT triggered_message FROM alerts WHERE id = ?", (alert_id,))
        existing = cursor.fetchone()["triggered_message"]

        if evaluate_condition(condition, cursor) and not existing:
            message = format_trigger_message(condition)

            cursor.execute("""
                UPDATE alerts
                SET is_active = 0,
                    triggered_message = ?,
                    triggered_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (message, alert_id))

            triggered_now.append(message)

    # Fetch triggered history
    cursor.execute("""
        SELECT id, condition_json, triggered_message, triggered_at
        FROM alerts
        WHERE user_id=? AND is_active=0
        ORDER BY triggered_at DESC
    """, (user_id,))

    history_rows = cursor.fetchall()

    conn.commit()
    conn.close()

    history = []
    for row in history_rows:
        history.append({
            "id": row["id"],
            "condition": json.loads(row["condition_json"]),
            "triggered_message": row["triggered_message"],
            "triggered_at": row["triggered_at"]
        })

    return {
        "triggered_now": triggered_now,
        "triggered_history": history
    }


# ---------- TRIGGERED ALERT COUNT ----------
@router.get("/triggered_count")
def triggered_count(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM alerts
        WHERE user_id=? AND is_active=0
    """, (user_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return {"count": count}


# ---------- RISK METER ----------
@router.get("/risk/{symbol}")
def get_risk(symbol: str, authorization: str = Header(...)):
    get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pe_ratio, profit_margin, revenue
        FROM fundamentals f
        JOIN symbols s ON s.id = f.company_id
        WHERE s.symbol = ?
        ORDER BY f.report_date DESC
        LIMIT 1
    """, (symbol,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"risk": "Unknown"}

    risk_score = 0

    if row["pe_ratio"] and row["pe_ratio"] > 30:
        risk_score += 1
    if row["profit_margin"] and row["profit_margin"] < 10:
        risk_score += 1
    if row["revenue"] and row["revenue"] < 0:
        risk_score += 1

    if risk_score == 0:
        return {"risk": "Low"}
    elif risk_score == 1:
        return {"risk": "Medium"}
    else:
        return {"risk": "High"}

@router.get("/current_value/{symbol}/{metric}")
def get_current_value(symbol: str, metric: str, authorization: str = Header(...)):
    get_user_id(authorization)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"""
        SELECT f.{metric}
        FROM fundamentals f
        JOIN symbols s ON s.id = f.company_id
        WHERE s.symbol = ?
        ORDER BY f.report_date DESC
        LIMIT 1
    """

    cursor.execute(query, (symbol,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"value": row[metric]}
    return {"value": None}

# ---------- BACKGROUND ALERT CHECKER ----------
def background_alert_checker():
    while True:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, condition_json, triggered_message FROM alerts WHERE is_active=1")
        rows = cursor.fetchall()

        for row in rows:
            alert_id = row["id"]
            condition = json.loads(row["condition_json"])
            existing = row["triggered_message"]

            if evaluate_condition(condition, cursor) and not existing:
                message = format_trigger_message(condition)

                cursor.execute("""
                    UPDATE alerts
                    SET is_active = 0,
                        triggered_message = ?,
                        triggered_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (message, alert_id))

                print(f"ALERT TRIGGERED: {condition['symbol']}")

        conn.commit()
        conn.close()

        time.sleep(60)  # every 1 minutes

