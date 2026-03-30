import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

# We use connection pooling to make our secure DB scalable
try:
    db_pool = psycopg2.pool.ThreadedConnectionPool(
        1, 10,
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "ai_stock_screener")
    )
except Exception as e:
    print("WARNING: Could not connect to PostgreSQL Database. It may not be set up yet.", e)
    db_pool = None

def get_connection():
    if db_pool:
        return db_pool.getconn()
    return None

def release_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)
