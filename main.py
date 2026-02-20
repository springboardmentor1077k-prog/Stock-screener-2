from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Literal
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from google import genai
import os
import json
import re

from database import engine
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
# ============================================================
# STANDARD RESPONSE FORMAT (ADDED FOR CONSISTENCY)
# ============================================================

def success_response(data=None, message="Success"):
    return {
        "status": "success",
        "message": message,
        "data": data
    }
# ============================================================
# GEMINI CONFIG
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
if ai_client:
    print("Listing available models...")
    for model in ai_client.models.list():
        print(model.name)


# ============================================================
# SCHEDULER SETUP
# ============================================================

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(evaluate_alerts, "interval", minutes=2)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# ============================================================
# Pydantic MODELS (Validation Layer)
# ============================================================

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: str
    password: str = Field(..., min_length=6)

class NLRequest(BaseModel):
    query: str = Field(..., min_length=5)

class PortfolioCreate(BaseModel):
    stock_symbol: str = Field(..., min_length=1, max_length=5)
    quantity: int = Field(..., gt=0)

class AlertCreate(BaseModel):
    stock_symbol: str = Field(..., min_length=1, max_length=5)
    metric: Literal["pe_ratio", "eps"]
    condition: Literal["<", ">"]
    threshold: float = Field(..., gt=0)

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return success_response(message="AI Stock Platform Backend Running 🚀")

# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/auth/register")
def register(data: RegisterRequest):

    with engine.connect() as conn:
        existing = conn.execute(text("""
            SELECT id FROM users
            WHERE username = :username OR email = :email
        """), {
            "username": data.username,
            "email": data.email
        }).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed = hash_password(data.password)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (username, email, hashed_password)
            VALUES (:username, :email, :password)
        """), {
            "username": data.username,
            "email": data.email,
            "password": hashed
        })

    return success_response(message="User registered successfully")



@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    with engine.connect() as conn:
        user = conn.execute(text("""
            SELECT id, username, hashed_password
            FROM users
            WHERE username = :username
        """), {"username": form_data.username}).fetchone()

    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user[1]})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ============================================================
# SCREENER ENGINE
# ============================================================

def run_screener(filters: dict):


    query = text("""
        SELECT s.symbol,
               s.sector,
               f.pe_ratio,
               f.eps,
               f.market_cap,
               f.revenue_growth,
               f.price_change_1y
        FROM symbols s
        JOIN fundamentals f 
            ON s.id = f.symbol_id
            AND f.reported_date = (
                SELECT MAX(f2.reported_date)
                FROM fundamentals f2
                WHERE f2.symbol_id = s.id
            )
        WHERE (:pe_limit IS NULL OR f.pe_ratio < :pe_limit)
        AND (:min_eps IS NULL OR f.eps > :min_eps)
        AND (:min_growth IS NULL OR f.revenue_growth > :min_growth)
        AND (:min_price_change IS NULL OR f.price_change_1y > :min_price_change)
        AND (:sector IS NULL OR LOWER(s.sector) = LOWER(:sector))
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, filters).fetchall()

    return [
        {
            "symbol": r[0],
            "sector": r[1],
            "pe_ratio": r[2],
            "eps": r[3],
            "market_cap": r[4],
            "revenue_growth": r[5],
            "price_change_1y": r[6]
        }
        for r in rows
    ]

def score_stock(stock):
    pe = float(stock.get("pe_ratio") or 0)
    eps = float(stock.get("eps") or 0)
    growth = float(stock.get("revenue_growth") or 0)
    momentum = float(stock.get("price_change_1y") or 0)

    pe_score = (1 / pe) if pe > 0 else 0
    growth_score = growth / 100
    momentum_score = momentum / 100

    return round(
        growth_score * 0.35 +
        pe_score * 0.25 +
        eps * 0.20 +
        momentum_score * 0.20,
        4
    )

# ============================================================
# SCREENER ENDPOINT (REST + GEMINI + LOGGING)
# ============================================================

@app.post("/screener")
def screener(
    request: NLRequest,
    current_user: dict = Depends(get_current_user)
):
    print(">>> SCREENER ENDPOINT HIT <<<")

    query_text = request.query.lower()

    filters = {
        "pe_limit": None,
        "min_eps": None,
        "min_growth": None,
        "min_price_change": None,
        "sector": None
    }

    pe_match = re.search(r"(?:pe|p/e)[^\d]*(\d+)", query_text)
    if pe_match:
        filters["pe_limit"] = float(pe_match.group(1))

    eps_match = re.search(r"eps[^\d]*(\d+)", query_text)
    if eps_match:
        filters["min_eps"] = float(eps_match.group(1))

    if ai_client:
        print("Gemini is active")
        print("User query:", request.query)

        try:
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
    You are a financial query parser.

    Valid sectors:
    Technology
    Consumer Cyclical
    IT Services
    Energy
    Finance
    Healthcare

    If user mentions tech or technology, map it to "Technology".

    Return ONLY valid JSON.
    No explanation.
    No markdown.
    No extra text.

    Schema:
    {{
    "pe_limit": number or null,
    "min_eps": number or null,
    "min_growth": number or null,
    "min_price_change": number or null,
    "sector": string or null
    }}

    User query:
    {request.query}
    """
            )

            # 🔥 Proper Gemini extraction
            gemini_text = response.candidates[0].content.parts[0].text

            print("Gemini raw text:")
            print(gemini_text)

            cleaned = gemini_text.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            parsed = json.loads(cleaned)

            # Normalize sector
            if parsed.get("sector"):
                sector_map = {
                    "tech": "Technology",
                    "technology": "Technology",
                    "it": "IT Services",
                    "it services": "IT Services"
                }

                lower_sector = parsed["sector"].lower()
                if lower_sector in sector_map:
                    parsed["sector"] = sector_map[lower_sector]

            filters.update({
                k: v for k, v in parsed.items()
                if k in filters and v is not None
            })

            print("Parsed filters:", filters)

        except Exception as e:
            print("Gemini parsing failed:", e)
        print("FINAL FILTERS SENT TO SQL:", filters)

    results = run_screener(filters)

    for r in results:
        r["score"] = score_stock(r)

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO query_history (user_id, raw_query, parsed_filters)
            VALUES (:user_id, :raw_query, :parsed_filters)
        """), {
            "user_id": current_user["id"],
            "raw_query": request.query,
            "parsed_filters": json.dumps(filters)
        })

    return success_response(data=results)

# ============================================================
# PORTFOLIO CRUD (ID-Based REST)
# ============================================================

@app.post("/portfolio")
def add_to_portfolio(
    request: PortfolioCreate,
    current_user: dict = Depends(get_current_user)
):

    with engine.begin() as conn:

        symbol = conn.execute(text("""
            SELECT id FROM symbols WHERE symbol = :symbol
        """), {"symbol": request.stock_symbol}).fetchone()

        if not symbol:
            raise HTTPException(status_code=404, detail="Symbol not found")

        conn.execute(text("""
            INSERT INTO portfolio (user_id, symbol_id, quantity, added_at)
            VALUES (:user_id, :symbol_id, :quantity, NOW())
        """), {
            "user_id": current_user["id"],
            "symbol_id": symbol[0],
            "quantity": request.quantity
        })

    return success_response(message="Added to portfolio")


@app.get("/portfolio")
def get_portfolio(current_user: dict = Depends(get_current_user)):

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT p.id,
                   s.symbol,
                   p.quantity
            FROM portfolio p
            JOIN symbols s ON p.symbol_id = s.id
            WHERE p.user_id = :user_id
        """), {"user_id": current_user["id"]}).fetchall()

    return success_response(data=[
        {"id": r[0], "symbol": r[1], "quantity": r[2]}
        for r in rows
    ])


@app.delete("/portfolio/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    current_user: dict = Depends(get_current_user)
):

    with engine.begin() as conn:
        result = conn.execute(text("""
            DELETE FROM portfolio
            WHERE id = :id AND user_id = :user_id
        """), {
            "id": portfolio_id,
            "user_id": current_user["id"]
        })

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Portfolio entry not found")

    return success_response(message="Deleted successfully")

# ============================================================
# ALERTS CRUD (ID-Based REST)
# ============================================================

@app.post("/alerts")
def create_alert(
    request: AlertCreate,
    current_user: dict = Depends(get_current_user)
):

    with engine.begin() as conn:

        symbol = conn.execute(text("""
            SELECT id FROM symbols WHERE symbol = :symbol
        """), {"symbol": request.stock_symbol}).fetchone()

        if not symbol:
            raise HTTPException(status_code=404, detail="Symbol not found")

        conn.execute(text("""
            INSERT INTO alerts
            (user_id, stock_symbol, metric, condition, threshold)
            VALUES (:user_id, :stock_symbol, :metric, :condition, :threshold)
        """), {
            "user_id": current_user["id"],
            "stock_symbol": request.stock_symbol,
            "metric": request.metric,
            "condition": request.condition,
            "threshold": request.threshold
        })

    return success_response(message="Alert created")


@app.get("/alerts")
def get_alerts(current_user: dict = Depends(get_current_user)):

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, stock_symbol, metric, condition, threshold
            FROM alerts
            WHERE user_id = :user_id
        """), {"user_id": current_user["id"]}).fetchall()

    return success_response(data=[
        {
            "id": r[0],
            "stock_symbol": r[1],
            "metric": r[2],
            "condition": r[3],
            "threshold": r[4]
        }
        for r in rows
    ])


@app.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user)
):

    with engine.begin() as conn:
        result = conn.execute(text("""
            DELETE FROM alerts
            WHERE id = :id AND user_id = :user_id
        """), {
            "id": alert_id,
            "user_id": current_user["id"]
        })

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

    return success_response(message="Alert deleted")

# ============================================================
# ALERT EVALUATION ENGINE
# ============================================================

def evaluate_alerts():
    print("Checking alerts...")
