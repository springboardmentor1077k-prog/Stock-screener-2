import os
import time
import logging
import psycopg2
from psycopg2 import pool
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

# Task 4 & 5: Ensure logs directory exists and setup centralized logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging with rotation (5MB, 3 files)
logger = logging.getLogger("ai_stock_screener")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(LOG_DIR, "app.log"), maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Task 5: Sanitization function
def sanitize_log_data(data):
    """Redact sensitive fields from logging data."""
    if not isinstance(data, dict):
        return data
    sensitive_keys = {"password", "token", "access_token", "jwt", "api_key", "secret"}
    sanitized = data.copy()
    for key in sanitized:
        if any(sk in key.lower() for sk in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(sanitized[key], dict):
            sanitized[key] = sanitize_log_data(sanitized[key])
    return sanitized

# We use connection pooling to make our secure DB scalable
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        2, 10,
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "ai_stock_screener")
    )
except Exception as e:
    logger.error(f"FATAL: Could not connect to PostgreSQL Database: {str(e)}")
    db_pool = None

# Bottleneck 4 / Dashboard: Track slow queries
SLOW_QUERIES = []

def get_active_db_connections():
    if db_pool and hasattr(db_pool, '_used'):
        return len(db_pool._used)
    return 0

def get_recent_slow_queries():
    return SLOW_QUERIES

# Task 3: Wrap every database call with a timer
class TimerCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor
        
    def execute(self, query, vars=None):
        start = time.time()
        try:
            return self._cursor.execute(query, vars)
        finally:
            duration_ms = (time.time() - start) * 1000
            # Task 4: Structured logging
            logger.info(f"SQL Query Executed - Duration: {duration_ms:.2f}ms")
            if duration_ms > 1000:
                logger.warning(f"SLOW QUERY DETECTED: {duration_ms:.2f}ms")
                q_str = "Unknown Query"
                try: 
                    if hasattr(self._cursor, 'query') and self._cursor.query:
                         q_str = self._cursor.query.decode('utf-8')[:150]
                except:
                    pass
                SLOW_QUERIES.insert(0, {"query": q_str, "duration_ms": round(duration_ms, 2)})
                if len(SLOW_QUERIES) > 5:
                    SLOW_QUERIES.pop()
                
    def __getattr__(self, name):
        return getattr(self._cursor, name)
        
    def __enter__(self):
        self._cursor.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._cursor.__exit__(exc_type, exc_val, exc_tb)

class TimerConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn
        
    def cursor(self, *args, **kwargs):
        return TimerCursorWrapper(self._conn.cursor(*args, **kwargs))
        
    def __getattr__(self, name):
        return getattr(self._conn, name)
        
    def __enter__(self):
        self._conn.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

def get_connection():
    if db_pool:
        return TimerConnectionWrapper(db_pool.getconn())
    return None

def release_connection(wrapper):
    if db_pool and wrapper:
        raw_conn = getattr(wrapper, "_conn", wrapper)
        db_pool.putconn(raw_conn)

RESULTS_CACHE = {}
RESULTS_CACHE_TIMEOUT = 60
DB_QUERY_TIMEOUT_MS = 5000

def clear_results_cache():
    RESULTS_CACHE.clear()

def get_results_cache_size():
    return len(RESULTS_CACHE)

def fetch_cached_screener_results(cursor, query, params=None):
    cache_key = f"{query}_{str(params)}"
    now = time.time()
    
    if cache_key in RESULTS_CACHE:
        timestamp, cached_results = RESULTS_CACHE[cache_key]
        if now - timestamp < RESULTS_CACHE_TIMEOUT:
            logger.info("Database Results cache hit")
            return cached_results
        else:
            del RESULTS_CACHE[cache_key]
            
    # Task 1: SAFE: parameterized query - no injection risk (No f-strings used for SQL)
    cursor.execute("SELECT set_config('statement_timeout', %s, false)", (str(DB_QUERY_TIMEOUT_MS),))
    
    # Task 1: SAFE: parameterized query - no injection risk
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    
    # Task 1: SAFE: literal SQL - no injection risk
    cursor.execute("SET statement_timeout = 0;")
    
    RESULTS_CACHE[cache_key] = (time.time(), results)
    return results
