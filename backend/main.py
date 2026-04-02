import os
import time
import json
import logging
import asyncio
import redis
import psycopg2
import psycopg2.extras
import re
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from backend.db import (
    get_connection, release_connection, fetch_cached_screener_results, 
    get_results_cache_size, clear_results_cache, get_active_db_connections, 
    get_recent_slow_queries, sanitize_log_data, logger
)
from backend.auth import create_access_token, verify_token, get_password_hash, verify_password
from backend.llm import parse_nl_to_dsl, get_llm_cache_size, clear_llm_cache, get_llm_cache_stats
from backend.compiler import validate_dsl, compile_sql_from_dsl, get_sql_cache_size, clear_sql_cache
from backend.portfolio_logic import get_price_cache_stats, clear_price_cache
from backend.portfolio_routes import router as portfolio_router
from backend.alerts_routes import router as alerts_router
from backend.portfolio_logic import get_current_price

# Bottleneck 4 / Dashboard Tracking
RESPONSE_TIMES_MS = []

from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Stock Screener API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Layer 4 Integration: Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to specific Streamlit host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bottleneck 3: Compress API responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        
        # Task 4 & 5: Structured Logging
        if not request.url.path.startswith("/cache"):
            log_payload = {
                "endpoint": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2)
            }
            logger.info(f"API Request - {json.dumps(sanitize_log_data(log_payload))}")
            
            # Dashboard Tracking
            RESPONSE_TIMES_MS.insert(0, duration_ms)
            if len(RESPONSE_TIMES_MS) > 10:
                RESPONSE_TIMES_MS.pop()
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_payload = {
            "endpoint": request.url.path,
            "error_type": type(e).__name__,
            "message": str(e),
            "duration_ms": round(duration_ms, 2)
        }
        logger.error(f"API Error - {json.dumps(sanitize_log_data(error_payload))}")
        raise e

app.include_router(portfolio_router)
app.include_router(alerts_router)

# ==========================================
# Task 4 & 5 Integration: Alerts Background Trigger Job
# ==========================================
def check_triggered_alerts():
    """Background task to trigger price alerts."""
    logging.info("APScheduler: Checking all active alerts...")
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, user_id, symbol, threshold_price, alert_type FROM alerts WHERE is_active=TRUE")
            all_active = cur.fetchall()
            for alert in all_active:
                cur_price = get_current_price(alert['symbol'])
                if cur_price <= 0: continue
                triggered = False
                if alert['alert_type'] == 'PRICE_ABOVE' and cur_price >= float(alert['threshold_price']):
                    triggered = True
                elif alert['alert_type'] == 'PRICE_BELOW' and cur_price <= float(alert['threshold_price']):
                    triggered = True
                if triggered:
                    logging.warning(f"ALERT TRIGGERED: {alert['symbol']} reached {cur_price} for User {alert['user_id']}")
                    cur.execute("UPDATE alerts SET is_active=FALSE WHERE id=%s", (alert['id'],))
            conn.commit()
    except Exception as e:
        logging.error(f"Alert check failed: {str(e)}")
    finally:
        release_connection(conn)

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
    logger.warning("Redis is not available.")

# Pydantic Models for Input Validation (Task 2)
class LoginRequest(BaseModel):
    username: str = Field(..., description="User login handle")
    password: str = Field(..., description="User password")

class RegisterRequest(BaseModel):
    username: str = Field(..., description="Desired user login handle")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., description="Strong secret key")

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language stock query (3-500 chars)")
    page: int = Field(1, ge=1, description="Result page number")
    limit: int = Field(20, ge=1, le=100, description="Records per page (max 100)")
    sort_by: str = "pe_ratio"
    sort_order: str = "asc"
    time_filter: Optional[int] = Field(None, description="Time horizon in quarters")

    @validator('query')
    def validate_query_no_sql(cls, v):
        sql_keywords = r'\b(DROP|DELETE|INSERT|UPDATE|TRUNCATE|DATABASE|SCHEMA|TABLE)\b'
        if re.search(sql_keywords, v, re.IGNORECASE):
            raise ValueError("Invalid query. Please use natural language only.")
        return v

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
            # Task 1: SAFE: parameterized query - no injection risk
            cursor.execute("SELECT id FROM users WHERE username=%s OR email=%s", (user.username, user.email))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username or Email already exists")
            
            hashed_pw = get_password_hash(user.password)
            # Task 1: SAFE: parameterized query - no injection risk
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                           (user.username, user.email, hashed_pw))
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
            # Task 1: SAFE: parameterized query - no injection risk
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username=%s", (user.username,))
            db_user = cursor.fetchone()
            
            if not db_user or not verify_password(user.password, db_user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            token = create_access_token({"sub": db_user['username'], "user_id": db_user['id']})
            return {"access_token": token, "token_type": "bearer", "user_id": db_user['id']}
    finally:
        release_connection(conn)

@app.post("/ask_ai")
@app.post("/query")
@limiter.limit("30/minute")
def ask_ai(request: Request, data: QueryRequest, current_user: dict = Depends(verify_token)):
    username = current_user['username']
    
    # 1. OPTIONAL: Check Redis Cache First
    cache_key = f"query_cache:{data.query}:{data.page}:{data.limit}:{data.sort_by}:{data.sort_order}"
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                results = json.loads(cached_result)
                return {
                    "status": "success", "count": len(results), "results": results, "source": "Redis Cache"
                }
        except Exception:
            pass
    
    # 2. Parsing: Natural Language -> JSON DSL
    dsl_data = parse_nl_to_dsl(data.query)
    if "error" in dsl_data:
        return {"status": "error", "message": f"Processing error: {dsl_data['error']}"}
        
    dsl_data["limit"] = data.limit
    dsl_data["page"] = data.page
    dsl_data["order_by"] = [{"field": data.sort_by, "direction": data.sort_order}]
        
    if data.time_filter is not None and data.time_filter > 0:
        dsl_data["time_filter"] = {"type": "last_m_quarters", "value": data.time_filter}
        
    # 3. Validation: Validate DSL rigidly
    is_valid, err_msg = validate_dsl(dsl_data)
    if not is_valid:
        return {"status": "error", "message": f"Validation Failed: {err_msg}"}
        
    # 4. Compiler: DSL -> Safe Parameterized SQL
    sql_query, parameters = compile_sql_from_dsl(dsl_data)
    
    # 5. Database Execution (PostgreSQL Source of Truth)
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Connection Failed.")
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Task 1: SAFE: parameterized query - no injection risk
            results = fetch_cached_screener_results(cursor, sql_query, tuple(parameters))
            
            clean_results = [{k: float(v) if not isinstance(v, str) and v is not None else v for k, v in row.items()} for row in results]
            
            response_data = {
                "status": "success", "count": len(clean_results) if clean_results else 0,
                "results": clean_results if clean_results else [], "dsl": dsl_data, "source": "Database"
            }
            
            if redis_client:
                try:
                    redis_client.setex(cache_key, 300, json.dumps(clean_results, default=str))
                except Exception:
                    pass
                
            return response_data
    except Exception as e:
        logger.error(f"SQL Error: {str(e)}")
        return {"status": "error", "message": f"Execution error: {str(e)}"}
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
def get_cache_stats(current_user: dict = Depends(verify_token)):
    """Return size stats for all system caches."""
    price_stats = get_price_cache_stats()
    llm_stats = get_llm_cache_stats()
    
    return {
        "llm": get_llm_cache_size(),
        "sql": get_sql_cache_size(),
        "db": get_results_cache_size(),
        "prices": price_stats.get("entries", 0),
        "price_hits": price_stats.get("hits", 0),
        "price_misses": price_stats.get("misses", 0),
        "llm_hits": llm_stats.get("hits", 0),
        "llm_misses": llm_stats.get("misses", 0)
    }

@app.post("/cache/clear_all")
def clear_all_caches(current_user: dict = Depends(verify_token)):
    clear_llm_cache()
    clear_sql_cache()
    clear_results_cache()
    clear_price_cache()
    return {"message": "All caches cleared successfully"}

# ==========================================
# Bottleneck 4 / Dashboard: Performance Endpoint
# ==========================================
@app.get("/performance/dashboard")
def get_performance_dashboard(current_user: dict = Depends(verify_token)):
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
            # SAFE: literal SQL - no injection risk
            cur.execute(query)
            results = cur.fetchall()
            
            # Format results
            clean = [{k: float(v) if not isinstance(v, str) and v is not None else v for k, v in row.items()} for row in results]
            
            # SAFE: parameterized query - no injection risk
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

# Scheduler initialization moved to a single location after defining job functions
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_screener_summary, 'interval', minutes=60)
scheduler.add_job(check_triggered_alerts, 'interval', minutes=1)
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
