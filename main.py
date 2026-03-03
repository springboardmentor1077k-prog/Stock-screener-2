from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from compiler import build_sql_from_dsl
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
from dotenv import load_dotenv
load_dotenv(override=True)
print("Loaded API KEY:", os.getenv("GEMINI_API_KEY"))
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
#if ai_client:
    #print("Listing available models...")
    #for model in ai_client.models.list():
      #  print(model.name)
if ai_client:
    print("Gemini client initialized.")
else:
    print("Gemini client NOT initialized.")

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
    type: Literal["last_n_quarters", "year", "range"]
    value: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class DSLNode(BaseModel):
    logic: Literal["AND", "OR"]
    conditions: list[Condition] = []
    nested: Optional["DSLNode"] = None

DSLNode.model_rebuild()

class DSLRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root: DSLNode
    time_filter: Optional[TimeFilter] = None
    sort_field: Optional[str] = None
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: Optional[int] = 50

# ============================================================
# STEP 3: DSL VALIDATION LAYER
# ============================================================
def validate_node(node: DSLNode, field_ranges=None):

    if field_ranges is None:
        field_ranges = {}

    if not node.conditions or len(node.conditions) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one condition required"
        )

    if node.logic not in ALLOWED_LOGIC:
        raise HTTPException(
            status_code=400,
            detail="Invalid logical operator"
        )

    for condition in node.conditions:

        if condition.field not in ALLOWED_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid field: {condition.field}"
            )

        if condition.operator not in ALLOWED_OPERATORS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid operator: {condition.operator}"
            )

        field_type = ALLOWED_FIELDS[condition.field]

        if field_type == "numeric":
            try:
                value = float(condition.value)
            except:
                raise HTTPException(
                    status_code=400,
                    detail=f"{condition.field} requires numeric value"
                )

            # Numeric contradiction detection
            if condition.field not in field_ranges:
                field_ranges[condition.field] = {"min": None, "max": None}

            if condition.operator in [">", ">="]:
                if field_ranges[condition.field]["min"] is None:
                    field_ranges[condition.field]["min"] = value
                else:
                    field_ranges[condition.field]["min"] = max(
                        field_ranges[condition.field]["min"], value
                    )

            if condition.operator in ["<", "<="]:
                if field_ranges[condition.field]["max"] is None:
                    field_ranges[condition.field]["max"] = value
                else:
                    field_ranges[condition.field]["max"] = min(
                        field_ranges[condition.field]["max"], value
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

    # Check contradictions
    for field, bounds in field_ranges.items():
        if bounds["min"] is not None and bounds["max"] is not None:
            if bounds["min"] > bounds["max"]:
                raise HTTPException(
                    status_code=400,
                    detail="Conflicting conditions detected."
                )

    if node.nested:
        validate_node(node.nested, field_ranges)


def validate_dsl(dsl: DSLRequest):

    validate_node(dsl.root)

    # Time filter validation
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

    if dsl.limit:
        if not (1 <= dsl.limit <= 100):
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
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
You are a deterministic query translator.

Translate the user query EXACTLY into structured JSON.

Rules:
- DO NOT invent new fields.
- DO NOT change the meaning of the query.
- DO NOT add extra filters.
- Only use fields that appear in the query.

Allowed fields:
pe_ratio, eps, revenue, debt, market_cap,
revenue_growth, price_change_1y, sector, reported_date

Allowed operators:
<, <=, >, >=, =

If the query contains:
"and" → logic = AND
"or" → logic = OR

If no time filter is mentioned:
"time_filter": null

If no sorting mentioned:
"sort_field": null
"sort_order": "desc"

If no limit mentioned:
"limit": 50

Return EXACTLY this format:

{{
  "root": {{
    "logic": "AND or OR",
    "conditions": [
      {{
        "field": "field_name",
        "operator": "operator",
        "value": number or string
      }}
    ]
  }},
  "time_filter": null,
  "sort_field": null,
  "sort_order": "desc",
  "limit": 50
}}

Return ONLY valid JSON.
No explanation.
No markdown.

User Query:
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
    #  Wrap flat DSL into root structure if needed
    if "root" not in parsed_json:
        parsed_json = {
            "root": {
                "logic": parsed_json.get("logic", "AND"),
                "conditions": parsed_json.get("conditions", []),
                "nested": parsed_json.get("nested")
            },
            "time_filter": parsed_json.get("time_filter"),
            "sort_field": parsed_json.get("sort_field"),
            "sort_order": parsed_json.get("sort_order"),
            "limit": parsed_json.get("limit")
        }

    print("FIXED DSL STRUCTURE:", parsed_json)

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

    query, params = build_sql_from_dsl(dsl)

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

    '''with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO query_history (user_id, raw_query, parsed_filters)
            VALUES (:user_id, :raw_query, :parsed_filters)
        """), {
            "user_id": current_user["id"],
            "raw_query": payload.query,
            "parsed_filters": json.dumps(parsed_json)
        })'''

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
