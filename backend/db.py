import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

# We use connection pooling to make our secure DB scalable
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="aiscreener_pool",
        pool_size=5,
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ai_stock_screener")
    )
except Exception as e:
    print("WARNING: Could not connect to Database. It may not be set up yet.")
    db_pool = None

def get_connection():
    if db_pool:
        return db_pool.get_connection()
    return None
