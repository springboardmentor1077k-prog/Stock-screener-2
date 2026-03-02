from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Literal
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from google import genai
from typing import Optional
from datetime import date
from datetime import datetime
import traceback
import os
import json
import re
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database import engine
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
# ============================================================
# REDIS CONFIG (ADDED)
# ============================================================

redis_client = None

# ============================================================
# RATE LIMITING
# ============================================================

limiter = Limiter(key_func=get_remote_address)
# ============================================================
# STANDARD RESPONSE FORMAT (ADDED FOR CONSISTENCY)
# ============================================================
def success_response(data=None, message="Success"):
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(code: str, message: str, layer: str, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "layer": layer,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
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
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(
        code="HTTP_ERROR",
        message=exc.detail,
        layer="APPLICATION",
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return error_response(
        code="INVALID_REQUEST_BODY",
        message="Invalid request format.",
        layer="API_GATEWAY",
        status_code=400
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="Unexpected system error.",
        layer="SYSTEM",
        status_code=500
    )


app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Slow down.",
        layer="API_GATEWAY",
        status_code=429
    )

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
# DSL CONFIGURATION (STEP 1)
# ============================================================

ALLOWED_FIELDS = {
    "pe_ratio": "numeric",
    "eps": "numeric",
    "revenue": "numeric",
    "debt": "numeric",
    "market_cap": "numeric",
    "revenue_growth": "numeric",
    "price_change_1y": "numeric",
    "sector": "string",
    "reported_date": "date"
}

ALLOWED_OPERATORS = ["<", "<=", ">", ">=", "="]
ALLOWED_LOGIC = ["AND", "OR"]

# ============================================================
# DSL SCHEMA (STEP 2)
# ============================================================

class Condition(BaseModel):
    field: str
    operator: str
    value: str | float | int


class TimeFilter(BaseModel):
    type: Literal["latest", "year", "range"]
    value: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class DSLRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filters: list[Condition]
    logic: Literal["AND", "OR"] = "AND"
    time_filter: Optional[TimeFilter] = None
    sort_field: Optional[str] = None
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: Optional[int] = 50

# ============================================================
# STEP 3: DSL VALIDATION LAYER
# ============================================================
def validate_dsl(dsl: DSLRequest):

    # -----------------------------
    # 1) Filters must exist
    # -----------------------------
    if not dsl.filters or len(dsl.filters) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one filter is required"
        )

    # -----------------------------
    # 2) Validate each condition
    # -----------------------------
    for condition in dsl.filters:

        # ---- Field whitelist check ----
        if condition.field not in ALLOWED_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {condition.field}"
            )

        # ---- Operator whitelist check ----
        if condition.operator not in ALLOWED_OPERATORS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid operator: {condition.operator}"
            )

        # ---- Type validation ----
        field_type = ALLOWED_FIELDS[condition.field]

        if field_type == "numeric":
            try:
                float(condition.value)
            except:
                raise HTTPException(
                    status_code=400,
                    detail=f"{condition.field} requires numeric value"
                )

        elif field_type == "string":
            if not isinstance(condition.value, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"{condition.field} requires string value"
                )

        elif field_type == "date":
            try:
                datetime.strptime(condition.value, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=400,
                    detail="Date must be in YYYY-MM-DD format"
                )

    # -----------------------------
    # 3️) Validate Logic
    # -----------------------------
    if dsl.logic not in ALLOWED_LOGIC:
        raise HTTPException(
            status_code=400,
            detail="Invalid logical operator"
        )

    # -----------------------------
    # 4️) Validate Time Filter
    # -----------------------------
    if dsl.time_filter:
        if dsl.time_filter.type == "year":
            if not dsl.time_filter.value:
                raise HTTPException(
                    status_code=400,
                    detail="Year value required for time_filter"
                )

        if dsl.time_filter.type == "range":
            if not dsl.time_filter.from_date or not dsl.time_filter.to_date:
                raise HTTPException(
                    status_code=400,
                    detail="Both from_date and to_date required"
                )

    # -----------------------------
    # 5️) Validate Limit
    # -----------------------------
    if dsl.limit:
        if not (1 <= dsl.limit <= 100):
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
            
            
            
    # Detect numeric contradictions
    field_ranges = {}

    for condition in dsl.filters:
        if ALLOWED_FIELDS[condition.field] == "numeric":
            value = float(condition.value)

            if condition.field not in field_ranges:
                field_ranges[condition.field] = {"min": None, "max": None}

            if condition.operator in [">", ">="]:
                field_ranges[condition.field]["min"] = value

            if condition.operator in ["<", "<="]:
                field_ranges[condition.field]["max"] = value

    for field, bounds in field_ranges.items():
        if bounds["min"] is not None and bounds["max"] is not None:
            if bounds["min"] > bounds["max"]:
                raise HTTPException(
                    status_code=400,
                    detail="Conflicting conditions detected."
                )
    return True


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return success_response(message="AI Stock Platform Backend Running 🚀")

# ============================================================
# COMPANIES ENDPOINTS (NEW)
# ============================================================

@app.get("/companies")
def get_companies():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, symbol, company_name, sector
            FROM symbols
        """)).fetchall()

    return success_response(data=[
        {
            "id": r[0],
            "symbol": r[1],
            "company_name": r[2],
            "sector": r[3]
        }
        for r in rows
    ])


@app.get("/companies/{symbol}")
def get_company(symbol: str):
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT id, symbol, company_name, sector
            FROM symbols
            WHERE symbol = :symbol
        """), {"symbol": symbol.upper()}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    return success_response(data={
        "id": row[0],
        "symbol": row[1],
        "company_name": row[2],
        "sector": row[3]
    })
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
# STEP 4: LLM PARSER SERVICE
# ============================================================

def parse_query_with_llm(query_text: str):

    if not ai_client:
        raise HTTPException(status_code=500, detail="AI service not configured.")

    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Return ONLY valid JSON.

Schema:
{{
  "filters": [
    {{
      "field": "pe_ratio | eps | revenue | debt | market_cap | revenue_growth | price_change_1y | sector | reported_date",
      "operator": "< | <= | > | >= | =",
      "value": number or string
    }}
  ],
  "logic": "AND or OR",
  "time_filter": {{
      "type": "latest | year | range",
      "value": number (if type=year),
      "from_date": "YYYY-MM-DD" (if type=range),
      "to_date": "YYYY-MM-DD" (if type=range)
  }},
  "sort_field": "optional field name",
  "sort_order": "asc or desc",
  "limit": number
}}

Query:
{query_text}
"""
    )

    raw = response.candidates[0].content.parts[0].text.strip()

    # Remove markdown if Gemini adds it
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except:
        raise HTTPException(
    status_code=400,
    detail="AI returned invalid structured output.")

    return parsed
# ============================================================
# SQL COMPILER
# ============================================================

def build_dynamic_query(dsl: DSLRequest):
    where_clauses = []
    params = {}

    for i, condition in enumerate(dsl.filters):
        param_name = f"value_{i}"

        # Choose correct table alias
        if condition.field == "sector":
            column = f"s.{condition.field}"
        else:
            column = f"f.{condition.field}"

        where_clauses.append(
            f"{column} {condition.operator} :{param_name}"
        )

        params[param_name] = condition.value
    
    
    # Apply time filter
    if dsl.time_filter:
        if dsl.time_filter.type == "year":
            where_clauses.append("EXTRACT(YEAR FROM f.reported_date) = :year")
            params["year"] = dsl.time_filter.value

        elif dsl.time_filter.type == "range":
            where_clauses.append("f.reported_date BETWEEN :from_date AND :to_date")
            params["from_date"] = dsl.time_filter.from_date
            params["to_date"] = dsl.time_filter.to_date

    # ALWAYS build logic_string
    logic_string = f" {dsl.logic} ".join(where_clauses)

    final_query = f"""
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
        WHERE {logic_string}
    """
    print("\n SQL COMPILER INTERNALS")
    print("WHERE CLAUSES:", where_clauses)
    print("LOGIC USED:", dsl.logic)
    
    return text(final_query), params




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
# SCREENER ENDPOINT (UPGRADED – SAFE + CACHE + STABLE)
# ============================================================

@app.post("/screener")
@limiter.limit("5/minute")
def screener(
    request: Request,                 # REQUIRED for slowapi
    payload: NLRequest,               # Your body model
    current_user: dict = Depends(get_current_user)
):
    print("\n==============================")
    print(" SCREENER PIPELINE STARTED")
    print("User Query:", payload.query)
    print("==============================")

    # NEW DSL FLOW
    try:
        parsed_json = parse_query_with_llm(payload.query)

    except Exception as e:
        print("⚠ Gemini failed:", str(e))

        # If quota exceeded or AI fails
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable. Please try again later."
        )

    print("\n LLM OUTPUT:")
    print("RAW DSL FROM LLM:", parsed_json)

    try:
        dsl = DSLRequest(**parsed_json)
        validate_dsl(dsl)
        print(" DSL VALIDATION PASSED")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid structured query."
        )
    

    # --------------------------------------------------------
    # REDIS CACHE
    # --------------------------------------------------------

    cache_key = f"screener:{json.dumps(parsed_json, sort_keys=True)}"
    cached = None
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
        except:
            cached = None

    if cached:
        print(" CACHE HIT — Returning Cached Results")
        print("==============================\n")
        return success_response(data=json.loads(cached))

    # --------------------------------------------------------
    # DATABASE QUERY
    # --------------------------------------------------------
    print("\n SQL COMPILER STAGE")
    print(" Compiling DSL → SQL...")

    query, params = build_dynamic_query(dsl)

    print(" COMPILED SQL:")
    print(query)

    print(" SQL PARAMETERS:")
    print(params)

    with engine.connect() as conn:
        print("\n GENERATED SQL:")
        print(query)
        print("SQL Params:", params)
        rows = conn.execute(query, params).fetchall()

    results = [
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

    print("\n DB Results Count:", len(results))

    # --------------------------------------------------------
    # SCORING (UNCHANGED)
    # --------------------------------------------------------

    for r in results:
        r["score"] = score_stock(r)

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    print("\n SCORING PHASE COMPLETE")
    print("Top 3 Stocks After Ranking:")
    for stock in results[:3]:
        print(stock["symbol"], "Score:", stock["score"])

    # --------------------------------------------------------
    # STORE CACHE (10 minutes)
    # --------------------------------------------------------

    if redis_client:
        try:
            redis_client.setex(cache_key, 600, json.dumps(results))
        except:
            pass

    # --------------------------------------------------------
    # QUERY HISTORY LOG (UNCHANGED)
    # --------------------------------------------------------

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO query_history (user_id, raw_query, parsed_filters)
            VALUES (:user_id, :raw_query, :parsed_filters)
        """), {
            "user_id": current_user["id"],
            "raw_query": payload.query,
            "parsed_filters": json.dumps(parsed_json)
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
