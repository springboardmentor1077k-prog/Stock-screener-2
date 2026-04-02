from fastapi import FastAPI
from pydantic import BaseModel
from llm_parser import parse_query
from sql_compiler import compile_to_sql
from query_executor import execute_query
from redis_client import get_cache, set_cache
import psycopg2

app = FastAPI()

# ---------------- MODELS ----------------

class User(BaseModel):
    email: str
    password: str


# ---------------- DB CONNECTION ----------------

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="stocks_db",
        user="postgres",
        password="Taekookilu"
    )


# ---------------- AUTH ----------------

@app.post("/register")
def register(user: User):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
        if cursor.fetchone():
            return {"error": "User already exists"}

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (user.email, user.password)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Registered successfully"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/login")
def login(user: User):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (user.email, user.password)
        )

        if cursor.fetchone():
            return {"message": "Login successful"}
        else:
            return {"error": "Invalid credentials"}

    except Exception as e:
        return {"error": str(e)}


# ---------------- COMPANIES ----------------

@app.get("/companies")
def get_companies():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, company_name, symbol FROM companies")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [{"id": r[0], "name": r[1], "symbol": r[2]} for r in rows]

    except Exception as e:
        return {"error": str(e)}


@app.delete("/company/{symbol}")
def delete_company(symbol: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM companies WHERE symbol=%s", (symbol,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Company not found"}

        cursor.close()
        conn.close()

        return {"message": f"{symbol} deleted"}

    except Exception as e:
        return {"error": str(e)}


# ---------------- PRICE ----------------

@app.get("/company/{symbol}/price")
def get_price(symbol: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price FROM stock_prices WHERE symbol=%s ORDER BY date DESC LIMIT 1",
            (symbol,)
        )

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if row:
            return {"symbol": symbol, "price": row[0]}
        return {"error": "No data found"}

    except Exception as e:
        return {"error": str(e)}


@app.get("/company/{symbol}/price-history")
def get_price_history(symbol: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT date, price FROM stock_prices WHERE symbol=%s ORDER BY date DESC LIMIT 30",
            (symbol,)
        )

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [{"date": str(r[0]), "price": r[1]} for r in rows]

    except Exception as e:
        return {"error": str(e)}


# ---------------- ALERTS ----------------

@app.post("/alerts")
def create_alert(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO alerts (email, metric, condition, threshold) VALUES (%s,%s,%s,%s)",
            (data["email"], data["metric"], data["condition"], data["threshold"])
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Alert created"}

    except Exception as e:
        return {"error": str(e)}


@app.get("/alerts/{email}")
def get_alerts(email: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, metric, condition, threshold FROM alerts WHERE email=%s",
            (email,)
        )

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {"id": r[0], "metric": r[1], "condition": r[2], "threshold": r[3]}
            for r in rows
        ]

    except Exception as e:
        return {"error": str(e)}


@app.delete("/alerts/{id}")
def delete_alert(id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM alerts WHERE id=%s", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Alert not found"}

        cursor.close()
        conn.close()

        return {"message": f"Alert {id} deleted"}

    except Exception as e:
        return {"error": str(e)}


# ---------------- PORTFOLIO ----------------

@app.post("/portfolio")
def add_portfolio(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO portfolio (email, company_name, quantity, buy_price) VALUES (%s,%s,%s,%s)",
            (data["email"], data["company_name"], data["quantity"], data["buy_price"])
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Added to portfolio"}

    except Exception as e:
        return {"error": str(e)}


@app.get("/portfolio/{email}")
def get_portfolio(email: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, company_name, quantity, buy_price FROM portfolio WHERE email=%s",
            (email,)
        )

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {"id": r[0], "company": r[1], "quantity": r[2], "buy_price": r[3]}
            for r in rows
        ]

    except Exception as e:
        return {"error": str(e)}


@app.delete("/portfolio/{id}")
def delete_portfolio(id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM portfolio WHERE id=%s", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "Item not found"}

        cursor.close()
        conn.close()

        return {"message": f"Portfolio item {id} deleted"}

    except Exception as e:
        return {"error": str(e)}


# ---------------- DELETE USER ----------------

@app.delete("/user/{email}")
def delete_user(email: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE email=%s", (email,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"error": "User not found"}

        cursor.close()
        conn.close()

        return {"message": f"{email} deleted"}

    except Exception as e:
        return {"error": str(e)}


# ---------------- QUERY ENGINE ----------------

def save_query(user_query, source):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO query_history (user_query, source) VALUES (%s, %s)",
            (user_query, source)
        )

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("⚠️ Failed:", str(e))


@app.post("/query")
def query(user_query: str):
    try:
        cached = get_cache(user_query)

        if cached:
            save_query(user_query, "cache")
            return {"data": cached, "source": "cache"}

        dsl = parse_query(user_query)
        if not dsl:
            return {"error": "Invalid query"}

        sql, params = compile_to_sql(dsl)
        results = execute_query(sql, params)

        set_cache(user_query, results)
        save_query(user_query, "database")

        return {"data": results, "source": "database"}

    except Exception as e:
        return {"error": str(e)}
