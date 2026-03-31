from fastapi import APIRouter, HTTPException, Header
from database_back import get_connection
import re
import json
from jwt_decode import decode_jwt
router = APIRouter()

ALLOWED_METRICS = ["pe", "peg", "ebitda", "promoter_holding"]
ALLOWED_OPERATORS = {"<", ">", "="}
BLACKLIST = ["drop", "delete", "insert", "update", "alter", "--", ";"]




#get the jwt token for user specific datas
def get_user_id_from_token(authorization: str, cursor):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    user_email = payload.get("email")

    cursor.execute(
        "SELECT user_id FROM users WHERE email = %s",
        (user_email,)
    )

    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user[0]





def normalize_query(query: str):
    query = query.lower().strip()

    replacements = {
        "less than": "<",
        "greater than": ">",
        "equal to": "=",
        "equals": "=",
        "more than": ">"
    }

    for k, v in replacements.items():
        query = query.replace(k, v)

    return query


# PARSER



def parse_query(query: str):
    query = query.lower().strip()

    for word in BLACKLIST:
        if word in query:
            return None
        
    words = query.split()
    company = None

    if words:
        first_word = words[0]


        if first_word not in ["pe", "peg", "ebitda", "promoter_holding",
                         "revenue", "profit", "cash"]:
        
        # allow only safe company tokens
            if re.match(r"^[a-zA-Z0-9]+$", first_word):
                company = first_word
                query = query[len(first_word):].strip()
    
    
    
    
    # NORMALIZATION
    
    replacements = {
        "less than": "<",
        "greater than": ">",
        "more than": ">",
        "above": ">",
        "below": "<",
        "equal to": "=",
        "equals": "="
    }

    for k, v in replacements.items():
        query = query.replace(k, v)

    
    # DETECT TIME
    
    time_match = re.search(r"(last|past)\s*(\d+)?\s*quarter", query)

    time_filter = None
    if time_match:
        n = time_match.group(2)
        time_filter = int(n) if n else 1

    
    # SPLIT CONDITIONS
    
    parts = re.split(r"\s+and\s+", query)

    conditions = []

    has_growth = False
    has_fundamental = False

    for part in parts:
        part = part.strip()

        
        # DETECT GROWTH
        
        if any(word in part for word in ["growth", "increase", "decrease", "trend"]):
            has_growth = True

            if "revenue" in part:
                field = "revenue_growth"
            elif "ebitda" in part:
                field = "ebitda_growth"
            elif "profit" in part:
                field = "net_profit_growth"
            elif "cash" in part:
                field = "debt_free_cash_growth"
            else:
                return None

        else:
            
            # NORMAL METRICS
            
            match = re.search(r"(pe|peg|ebitda|promoter_holding)\s*(<|>|=)\s*(\d+(\.\d+)?)", part)
            if not match:
                return None

            field = match.group(1)
            has_fundamental = True

        
        # EXTRACT OPERATOR + VALUE
        
        match = re.search(r"(<|>|=)\s*(\d+(\.\d+)?)", part)
        if not match:
            return None

        operator = match.group(1)
        value = float(match.group(2))

        conditions.append({
            "field": field,
            "operator": operator,
            "value": value
        })

    
    # ENTITY LOGIC
    
    if has_growth and has_fundamental:
        entity = "symbol"
    elif has_growth:
        entity = "historical_metrics"
    else:
        entity = "fundamentals"

    
    # DEFAULT TIME FOR GROWTH
    
    if has_growth and not time_filter:
        time_filter = 4

    return {
        "entity": entity,
        "conditions": conditions,
        "time_filter": time_filter,
        "company": company
    }
    


# SQL BUILDER


def build_sql(parsed, company_id=None):
    where = []
    values = []

    entity = parsed.get("entity", "fundamentals")
    time_filter = parsed.get("time_filter")

    
    # CONDITION BUILDING
    
    for cond in parsed["conditions"]:

        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]

        if operator not in ALLOWED_OPERATORS:
            raise ValueError("Invalid operator")

        # Map fields to correct table alias
        if field.endswith("_growth") or field in ["revenue", "net_profit"]:
            where.append(f"h.{field} {operator} %s")
        else:
            where.append(f"f.{field} {operator} %s")

        values.append(value)

    
    # COMPANY FILTER
    
    if company_id is not None:
        where.append("s.symbol_id = %s")
        values.append(company_id)

    
    # ENTITY HANDLING
    
    if entity == "fundamentals":
        base_query = """
            FROM fundamentals f
            JOIN symbol s ON f.symbol_id = s.symbol_id
        """

    elif entity == "historical_metrics":
        base_query = """
            FROM historical_metrics h
            JOIN symbol s ON h.symbol_id = s.symbol_id
        """

    else:  # symbol (mixed query)
        base_query = """
            FROM symbol s
            LEFT JOIN fundamentals f ON s.symbol_id = f.symbol_id
            LEFT JOIN historical_metrics h ON s.symbol_id = h.symbol_id
        """

    
    # TIME FILTER (ONLY FOR HISTORICAL)
    
    if time_filter and entity != "fundamentals":
        where.append("h.quarter >= (SELECT MAX(quarter) - %s FROM historical_metrics)")
        values.append(time_filter)

    
    # FINAL QUERY
    
    query = f"""
        SELECT DISTINCT s.company_symbol, s.company_name
        {base_query}
        WHERE {' AND '.join(where)}
        LIMIT 5
    """

    return query, values



# ADD ALERT
@router.post("/add-alert")
def add_alert(data: dict, authorization: str = Header()):
    try:
        parsed = parse_query(data.get("query", ""))

        if not parsed:
            raise HTTPException(400, "Invalid query format")

        conn = get_connection()
        cursor = conn.cursor()

        # FIND COMPANY
        company_id = None
        company_name = None
        
        company = parsed.get("company")

        if company:
            cursor.execute("""
                SELECT symbol_id, company_name
                FROM symbol
                WHERE LOWER(company_name) LIKE %s
                OR LOWER(company_symbol) LIKE %s
                ORDER BY LENGTH(company_name) ASC
                LIMIT 1
            """, (f"%{company}%", f"%{company}%"))

            row = cursor.fetchone()

            if not row:
                raise HTTPException(400, "Company not found")

            company_id = row[0]
            company_name = row[1]

        # CHECK DUPLICATE
        conditions_json = json.dumps(parsed["conditions"], sort_keys=True)

        cursor.execute("""
            SELECT alert_id FROM alert_master
            WHERE company_id IS NOT DISTINCT FROM %s
            AND conditions = %s
        """, (company_id, conditions_json))

        row = cursor.fetchone()   

        if row:
            alert_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO alert_master (company_id, conditions)
                VALUES (%s, %s)
                RETURNING alert_id
            """, (company_id, conditions_json))

            alert_id = cursor.fetchone()[0]   # ✅ FIXED (inside else)

        # LINK TO USER
        user_id = get_user_id_from_token(authorization, cursor)

        cursor.execute("""
            INSERT INTO user_alerts (user_id, alert_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (user_id, alert_id))

        conn.commit()
        cursor.close()   # ✅ added
        conn.close()

        return {"status": "Alert added"}

    except HTTPException:
        raise

    except Exception as e:
        print("ADD ERROR:", e)
        raise HTTPException(500, "Internal error")


# GET ALERTS

@router.get("/get-alerts")
def get_alerts(authorization: str = Header()):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        user_id = get_user_id_from_token(authorization, cursor)
        cursor.execute("""
    SELECT ua.id, am.alert_id, am.company_id, am.conditions, s.company_name
    FROM user_alerts ua
    JOIN alert_master am ON ua.alert_id = am.alert_id
    LEFT JOIN symbol s ON am.company_id = s.symbol_id
    WHERE ua.user_id = %s AND ua.is_active = TRUE
    """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return {
            "data": [
                {
                    "id": r[0],
                    "alert_id": r[1],
                    "company_id": r[2],
                    "conditions": r[3],
                    "company_name": r[4]
                }
                for r in rows
            ]
        }

    except Exception as e:
        print("GET ERROR:", e)
        return {"data": []}



# CHECK ALERTS

@router.get("/check-alerts")
def check_alerts(authorization: str = Header()):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        user_id = get_user_id_from_token(authorization, cursor)
        
        
        cursor.execute("""
        SELECT am.alert_id, am.company_id, am.conditions
        FROM user_alerts ua
        JOIN alert_master am ON ua.alert_id = am.alert_id
        WHERE ua.user_id = %s AND ua.is_active = TRUE
        """, (user_id,))

        alerts = cursor.fetchall()

        results = []

        for alert_id, company_id, conditions in alerts:

            parsed = {"conditions": conditions,  "entity": "symbol"}
            query, values = build_sql(parsed, company_id)

            cursor.execute(query, values)
            matches = cursor.fetchall()

            results.append({
            "alert_id": alert_id,
            "triggered": bool(matches),
            "companies": [
            {"symbol": m[0], "name": m[1]} for m in matches
        ]
    })

        conn.close()

        return {"alerts": results}

    except Exception as e:
        print("CHECK ERROR:", e)
        return {"triggered": []}



# DELETE ALERT

@router.delete("/delete-alert/{id}")
def delete_alert(id: int, authorization: str = Header()):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        user_id = get_user_id_from_token(authorization, cursor)
        
        cursor.execute("""
        DELETE FROM user_alerts
        WHERE id = %s AND user_id = %s
        """, (id, user_id))

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