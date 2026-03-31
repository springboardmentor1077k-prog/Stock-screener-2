import os
import time
import json
import logging
import asyncio
import redis
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from backend.db import get_connection, release_connection, fetch_cached_screener_results, get_results_cache_size, clear_results_cache, get_active_db_connections, get_recent_slow_queries
from backend.auth import create_access_token, verify_token, get_password_hash, verify_password
from backend.llm import parse_nl_to_dsl, get_llm_cache_size, clear_llm_cache, get_llm_cache_stats
from backend.compiler import validate_dsl, compile_sql_from_dsl, get_sql_cache_size, clear_sql_cache
from backend.portfolio_logic import get_price_cache_stats, clear_price_cache
from backend.portfolio_routes import router as portfolio_router
logging.basicConfig(level=logging.INFO)

# Bottleneck 4 / Dashboard Tracking
RESPONSE_TIMES_MS = []

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Stock Screener API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Bottleneck 3: Compress API responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    # Bottleneck 3: Response time header
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
    
    # Dashboard Tracking (Last 10 average)
    if not request.url.path.startswith("/cache"):
        RESPONSE_TIMES_MS.insert(0, duration_ms)
        if len(RESPONSE_TIMES_MS) > 10:
            RESPONSE_TIMES_MS.pop()
            
    return response

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
    # Bottleneck 3: Default limit explicitly trimmed to 20 for Network bandwidth optimizations
    limit: int = 20
    sort_by: str = "pe_ratio"
    sort_order: str = "asc"
    time_filter: Optional[int] = None

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
            return {"access_token": token, "token_type": "bearer", "user_id": db_user['id']}
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
        
    # Inject UI time filter directive if selected
    if data.time_filter is not None and data.time_filter > 0:
        dsl_data["time_filter"] = {
            "type": "last_m_quarters",
            "value": data.time_filter
        }
        
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
            results = fetch_cached_screener_results(cursor, sql_query, tuple(parameters))
            
            # Format results so any Decimals are handled nicely by json dumps natively
            clean_results = [{k: float(v) if not isinstance(v, str) and v is not None else v for k, v in row.items()} for row in results]
            
            # Bottleneck 3: Strip unselected payload columns completely if specifically requested
            if "select" in dsl_data and isinstance(dsl_data["select"], list) and len(dsl_data["select"]) > 0:
                allowed_cols = set(dsl_data["select"] + ["company_name", "symbol", "sector"])
                filtered_results = []
                for row in clean_results:
                    filtered_results.append({k: v for k, v in row.items() if k in allowed_cols})
                clean_results = filtered_results

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

# ==========================================
# Task 5: Cache Endpoints
# ==========================================
@app.get("/cache/stats")
def cache_stats():
    price_stats = get_price_cache_stats()
    llm_stats = get_llm_cache_stats()
    
    return {
        "llm": get_llm_cache_size(),
        "sql": get_sql_cache_size(),
        "db": get_results_cache_size(),
        "prices": price_stats["entries"],
        "price_hits": price_stats["hits"],
        "price_misses": price_stats["misses"],
        "llm_hits": llm_stats["hits"],
        "llm_misses": llm_stats["misses"]
    }

@app.post("/cache/clear_all")
def clear_all_caches():
    clear_llm_cache()
    clear_sql_cache()
    clear_results_cache()
    clear_price_cache()
    return {"message": "All caches cleared successfully"}

# ==========================================
# Bottleneck 4 / Dashboard: Performance Endpoint
# ==========================================
@app.get("/performance/dashboard")
def get_performance_dashboard(debug: str = "false"):
    if debug.lower() != "true":
        raise HTTPException(status_code=403, detail="Debug mode not active.")
        
    avg_response = sum(RESPONSE_TIMES_MS) / len(RESPONSE_TIMES_MS) if len(RESPONSE_TIMES_MS) > 0 else 0
    
    price_stats = get_price_cache_stats()
    llm_stats = get_llm_cache_stats()
    
    total_db_cache_hits = price_stats['hits'] + llm_stats['hits']
    total_db_cache_misses = price_stats['misses'] + llm_stats['misses']
    total_ops = total_db_cache_hits + total_db_cache_misses
    
    hit_rate = (total_db_cache_hits / total_ops * 100) if total_ops > 0 else 0.0
    
    return {
        "avg_response_time_ms": round(avg_response, 2),
        "cache_hit_rate_pct": round(hit_rate, 2),
        "active_db_connections": get_active_db_connections(),
        "slow_queries": get_recent_slow_queries()
    }

# ==========================================
# Bottleneck 2: Pre-compute background logic
# ==========================================
def refresh_screener_summary():
    """APScheduler Background job running every hour to pre-compute database aggregation."""
    logging.info("APScheduler: Starting hour pre-compute refresh...")
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            query = """
                SELECT s.sector, AVG(f.pe_ratio) as avg_pe, SUM(f.revenue) as total_revenue, COUNT(*) as comp_count
                FROM symbols s 
                JOIN fundamentals f ON s.id = f.company_id 
                GROUP BY s.sector
            """
            cur.execute(query)
            results = cur.fetchall()
            
            # We assume results exist and json serialization
            clean = [{k: float(v) if not isinstance(v, str) and v is not None else v for k, v in row.items()} for row in results]
            
            cur.execute(
                "INSERT INTO screener_cache (cache_key, data, updated_at) VALUES ('sector_summary', %s, CURRENT_TIMESTAMP) "
                "ON CONFLICT(cache_key) DO UPDATE SET data=EXCLUDED.data, updated_at=EXCLUDED.updated_at;",
                (json.dumps(clean, default=str),)
            )
            conn.commit()
            logging.info("APScheduler: Refreshed screener_cache perfectly.")
    except Exception as e:
        logging.error(f"Background refresh failed: {str(e)}")
    finally:
        release_connection(conn)

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_screener_summary, 'interval', minutes=60)
scheduler.start()

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
