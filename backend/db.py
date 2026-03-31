import os
import time
import logging
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# We use connection pooling to make our secure DB scalable
# Task 4: Use psycopg2.pool.SimpleConnectionPool with minimum 2 and maximum 10 connections
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
    print("WARNING: Could not connect to PostgreSQL Database. It may not be set up yet.", e)
    db_pool = None

# Bottleneck 4 / Dashboard: Track slow queries
SLOW_QUERIES = []

def get_active_db_connections():
    """Return an approximation of used connections from the pool."""
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
            logging.info(f"Query Executed in {duration_ms:.2f} ms")
            if duration_ms > 1000:
                print(f"SLOW QUERY DETECTED: {duration_ms:.2f} ms")
                logging.warning(f"SLOW QUERY DETECTED: {duration_ms:.2f} ms")
                q_str = ""
                try: 
                    q_str = self._cursor.query.decode('utf-8')[:150] + "..." if self._cursor.query else "Unknown Query"
                except:
                    q_str = "Unknown Query Format"
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
        # Return the transparent connection wrapper so timers run seamlessly
        return TimerConnectionWrapper(db_pool.getconn())
    return None

def release_connection(wrapper):
    if db_pool and wrapper:
        # Ensure we place the unwrapped raw connection back in the pool
        raw_conn = getattr(wrapper, "_conn", wrapper)
        db_pool.putconn(raw_conn)

# Task 3: Cache database query results
RESULTS_CACHE = {}
RESULTS_CACHE_TIMEOUT = 60

# Bottleneck 2: Database Query Speed
DB_QUERY_TIMEOUT_MS = 5000 # 5 seconds

def clear_results_cache():
    RESULTS_CACHE.clear()

def get_results_cache_size():
    return len(RESULTS_CACHE)

def fetch_cached_screener_results(cursor, query, params=None):
    # Only cache read-only SELECT queries explicitly for the screener
    cache_key = f"{query}_{str(params)}"
    now = time.time()
    
    if cache_key in RESULTS_CACHE:
        timestamp, cached_results = RESULTS_CACHE[cache_key]
        if now - timestamp < RESULTS_CACHE_TIMEOUT:
            logging.info("Database Results cache hit")
            return cached_results
        else:
            del RESULTS_CACHE[cache_key]
            
    # Bottleneck 2: Enforce 5s query timeout directly at the Postgres instance level
    cursor.execute(f"SET statement_timeout = {DB_QUERY_TIMEOUT_MS};")
    cursor.execute(query, params)
    
    # Reset immediately after completion to avoid bleeding timeout to pooled connections
    results = cursor.fetchall()
    cursor.execute("SET statement_timeout = 0;")
    
    RESULTS_CACHE[cache_key] = (time.time(), results)
    return results
