from fastapi import APIRouter, HTTPException
from database_back import get_connection
import re
import json

router = APIRouter()

ALLOWED_METRICS = ["pe", "peg", "ebitda", "promoter_holding"]


# PARSER

def parse_query(query: str):
    query = query.lower().strip()

    words = query.split()
    company = None

    # detect company (first word if not metric)
    if words[0] not in ALLOWED_METRICS:
        company = words[0]
        query = query[len(company):].strip()

    parts = re.split(r"\s+and\s+", query)

    conditions = []
    pattern = r"(pe|peg|ebitda|promoter_holding)\s*(<|>|=)\s*(\d+(\.\d+)?)"

    for part in parts:
        match = re.search(pattern, part)
        if not match:
            return None

        conditions.append({
            "metric": match.group(1),
            "operator": match.group(2),
            "value": float(match.group(3))
        })

    return {
        "company": company,
        "conditions": conditions
    }



# SQL BUILDER

def build_sql(parsed, company_id=None):
    where = []
    values = []

    for cond in parsed["conditions"]:
        where.append(f"{cond['metric']} {cond['operator']} %s")
        values.append(cond["value"])

    if company_id:
        where.append("f.symbol_id = %s")
        values.append(company_id)

    query = f"""
        SELECT s.company_symbol
        FROM fundamentals f
        JOIN symbol s ON f.symbol_id = s.symbol_id
        WHERE {' AND '.join(where)}
        LIMIT 5
    """

    return query, values



# ADD ALERT

@router.post("/add-alert")
def add_alert(data: dict):
    try:
        parsed = parse_query(data.get("query", ""))

        if not parsed:
            raise HTTPException(400, "Invalid query format")

        conn = get_connection()
        cursor = conn.cursor()

        
        # FIND COMPANY
        
        company_id = None
        company_name = None

        if parsed["company"]:
            cursor.execute("""
                SELECT symbol_id, company_name
                FROM symbol
                WHERE LOWER(company_name) LIKE %s
                OR LOWER(company_symbol) LIKE %s
                LIMIT 1
            """, (f"%{parsed['company']}%", f"%{parsed['company']}%"))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(400, "Company not found")

            company_id = row[0]
            company_name = row[1]

        
        # CHECK DUPLICATE
        
        cursor.execute("""
            SELECT alert_id FROM alert_master
            WHERE company_id IS NOT DISTINCT FROM %s
            AND conditions = %s
        """, (company_id, json.dumps(parsed["conditions"])))

        row = cursor.fetchone()

        if row:
            alert_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO alert_master (company_id, conditions)
                VALUES (%s, %s)
                RETURNING alert_id
            """, (company_id, json.dumps(parsed["conditions"])))
            alert_id = cursor.fetchone()[0]

        
        # LINK USER (STATIC USER = 1)
        
        cursor.execute("""
            INSERT INTO user_alerts (user_id, alert_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (1, alert_id))

        conn.commit()
        conn.close()

        return {"status": "Alert added"}

    except HTTPException:
        raise

    except Exception as e:
        print("ADD ERROR:", e)
        raise HTTPException(500, "Internal error")



# GET ALERTS

@router.get("/get-alerts")
def get_alerts():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ua.id, am.company_id, am.conditions, s.company_name
            FROM user_alerts ua
            JOIN alert_master am ON ua.alert_id = am.alert_id
            LEFT JOIN symbol s ON am.company_id = s.symbol_id
            WHERE ua.user_id = 1 AND ua.is_active = TRUE
        """)

        rows = cursor.fetchall()
        conn.close()

        return {
            "data": [
                {
                    "id": r[0],
                    "company_id": r[1],
                    "conditions": r[2],
                    "company_name": r[3]
                }
                for r in rows
            ]
        }

    except Exception as e:
        print("GET ERROR:", e)
        return {"data": []}



# CHECK ALERTS

@router.get("/check-alerts")
def check_alerts():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT am.alert_id, am.company_id, am.conditions
            FROM user_alerts ua
            JOIN alert_master am ON ua.alert_id = am.alert_id
            WHERE ua.user_id = 1 AND ua.is_active = TRUE
        """)

        alerts = cursor.fetchall()

        triggered = []

        for alert_id, company_id, conditions in alerts:

            parsed = {"conditions": conditions}
            query, values = build_sql(parsed, company_id)

            cursor.execute(query, values)
            matches = cursor.fetchall()

            if matches:
                triggered.append({
                    "alert_id": alert_id,
                    "companies": [m[0] for m in matches]
                })

        conn.close()

        return {"triggered": triggered}

    except Exception as e:
        print("CHECK ERROR:", e)
        return {"triggered": []}



# DELETE ALERT

@router.delete("/delete-alert/{id}")
def delete_alert(id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM user_alerts
            WHERE id = %s AND user_id = 1
        """, (id,))

        if cursor.rowcount == 0:
            raise HTTPException(404, "Alert not found")

        conn.commit()
        conn.close()

        return {"status": "Deleted"}

    except HTTPException:
        raise

    except Exception as e:
        print("DELETE ERROR:", e)
        raise HTTPException(500, "Delete failed")