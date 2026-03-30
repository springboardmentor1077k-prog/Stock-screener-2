import os
import json
import logging
import asyncio
import redis
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.db import get_connection, release_connection
from backend.auth import create_access_token, verify_token, get_password_hash, verify_password
from backend.llm import parse_nl_to_dsl
from backend.compiler import validate_dsl, compile_sql_from_dsl
from backend.portfolio_routes import router as portfolio_router
logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Stock Screener API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(portfolio_router)
# Setup Redis safely
try:
    redis_client = redis.StrictRedis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"), 
        port=int(os.getenv("REDIS_PORT", 6379)), 
        decode_responses=True
    )
    redis_client.ping()
except Exception:
    redis_client = None
    logging.warning("Redis is not available.")

# Pydantic Models for Input Validation
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class QueryRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 10
    sort_by: str = "pe_ratio"
    sort_order: str = "asc"

@app.get("/")
@limiter.limit("10/minute")
def read_root(request: Request):
    return {"status": "Advanced Screener API is running securely!"}

@app.post("/register")
@limiter.limit("5/minute")
def register(request: Request, user: RegisterRequest):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        with conn.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (user.username, user.email))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username or Email already exists")
            
            # Insert new user with hashed password (no plain text passwords)
            hashed_pw = get_password_hash(user.password)
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (user.username, user.email, hashed_pw))
            conn.commit()
            return {"message": "User registered successfully"}
    finally:
        release_connection(conn)

@app.post("/login")
@limiter.limit("10/minute")
def login(request: Request, user: LoginRequest):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username=%s", (user.username,))
            db_user = cursor.fetchone()
            
            if not db_user or not verify_password(user.password, db_user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            # JWT Token Authentication with user_id and expiration
            token = create_access_token({"sub": db_user['username'], "user_id": db_user['id']})
            # Sensitive data like db_user fields are NOT returned in response
            return {"access_token": token, "token_type": "bearer"}
    finally:
        release_connection(conn)

@app.post("/ask_ai")
@limiter.limit("30/minute")
def ask_ai(request: Request, data: QueryRequest, username: str = Depends(verify_token)):
    # 1. OPTIONAL: Check Redis Cache First
    cache_key = f"query_cache:{data.query}:{data.page}:{data.limit}:{data.sort_by}:{data.sort_order}"
    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return {"source": "Redis Cache", "data": json.loads(cached_result)}
    
    # 2. Parsing: Natural Language -> JSON DSL via ChatGPT
    dsl_data = parse_nl_to_dsl(data.query)
    if "error" in dsl_data:
        raise HTTPException(status_code=400, detail=dsl_data["error"])
        
    # Inject UI sorting/pagination directives gracefully
    dsl_data["limit"] = data.limit
    dsl_data["page"] = data.page
    dsl_data["order_by"] = [{"field": data.sort_by, "direction": data.sort_order}]
        
    # 3. Validation: Validate DSL rigidly on incoming requests
    is_valid, err_msg = validate_dsl(dsl_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation Failed: {err_msg}")
        
    # 4. Compiler: DSL -> Safe Parameterized SQL
    sql_query, parameters = compile_sql_from_dsl(dsl_data)

    
    # 5. Database Execution (PostgreSQL Source of Truth)
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Connection Failed.")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # We strictly pass parameters separated from SQL securely
            cursor.execute(sql_query, tuple(parameters))
            results = cursor.fetchall()
            
            # Format results so any Decimals are handled nicely by json dumps natively
            clean_results = [{k: float(v) if not isinstance(v, str) and v is not None else v for k, v in row.items()} for row in results]
            
            # Security: Do NOT expose internal sql_query or parameters to client API responses
            response_data = {"dsl": dsl_data, "data": clean_results, "source": "Database"}
            
            # 6. Store in Cache (if Redis is running) with TTL
            if redis_client:
                redis_client.setex(cache_key, 300, json.dumps(clean_results, default=str)) # Cache for 5 mins
                
            return response_data
    except Exception as e:
        logging.error(f"SQL Error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while executing the query.")
    finally:
        release_connection(conn)

@app.get("/companies")
@limiter.limit("60/minute")
def get_companies(request: Request, username: str = Depends(verify_token)):
    """Cached list of available companies"""
    cache_key = "cache:companies"
    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return {"source": "Redis", "data": json.loads(cached_result)}
            
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Connection Failed.")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id, symbol, company_name, sector FROM symbols ORDER BY symbol ASC")
            results = cursor.fetchall()
            response_data = {"data": results, "source": "Database"}
            if redis_client:
                redis_client.setex(cache_key, 3600, json.dumps(results, default=str)) # 1 hr TTL
            return response_data
    finally:
        release_connection(conn)

@app.get("/fundamentals/{symbol}")
@limiter.limit("60/minute")
def get_fundamentals(request: Request, symbol: str, username: str = Depends(verify_token)):
    """Cached latest fundamentals for a symbol"""
    symbol = symbol.upper()
    cache_key = f"cache:fundamentals:{symbol}"
    
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return {"source": "Redis", "data": json.loads(cached)}
            
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Connection Failed.")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            query = """
                SELECT f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity
                FROM fundamentals f
                JOIN symbols s ON s.id = f.company_id
                WHERE s.symbol = %s
                LIMIT 1
            """
            cursor.execute(query, (symbol,))
            res = cursor.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Fundamentals not found for symbol")
                
            clean_res = {k: float(v) if not isinstance(v, str) and v is not None else v for k, v in res.items()}
            response_data = {"data": clean_res, "source": "Database"}
            if redis_client:
                redis_client.setex(cache_key, 1800, json.dumps(clean_res, default=str)) # 30 mins TTL
            return response_data
    finally:
        release_connection(conn)


# External API Optimization Tasks
async def fetch_external_data_task():
    """ Runs periodically to fetch from external providers without impacting live user requests. """
    while True:
        try:
            logging.info("Background Process: Ingesting external API data...")
            # Simulated: Here we would fetch external source data and store securely in our DB.
            # Only storing into DB allows the database to stay as the Single Source of Truth.
            
            # Proper Cache Invalidation logic
            if redis_client:
                # Find cache keys to invalidate
                keys = redis_client.keys("query_cache:*")
                if keys:
                    redis_client.delete(*keys)
                redis_client.delete("cache:companies")
                
                fund_keys = redis_client.keys("cache:fundamentals:*")
                if fund_keys:
                    redis_client.delete(*fund_keys)
                    
                logging.info("Background Process: Cache formally invalidated with new data available.")
                
        except Exception as e:
            logging.error(f"Background task error: {e}")
            
        await asyncio.sleep(86400)  # Refresh periodically (e.g., 24 hrs or customizable scale)

@app.on_event("startup")
async def startup_event():
    # Automatically kickstart the cron task when uvicorn starts the FastAPI backend
    asyncio.create_task(fetch_external_data_task())
