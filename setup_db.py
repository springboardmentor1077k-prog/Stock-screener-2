import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_stock_screener")

def setup_database():
    try:
        # 1. Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # 2. Check if DB exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
        else:
            print(f"Database '{DB_NAME}' found.")

        cursor.close()
        conn.close()

        # 3. Connect to the actual database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        print("Dropping old table structure to prevent conflicts...")
        cursor.execute("DROP TABLE IF EXISTS users, historical_data, fundamentals, symbols, stocks CASCADE")
        
        print("Executing schema.sql to create tables...")
        # Read our schema file structure
        with open("database/schema.sql", "r") as f:
            sql_file = f.read()
            
        # Execute each individual layout chunk separated by semicolons
        sql_commands = [cmd for cmd in sql_file.split(";") if cmd.strip() != ""]
        
        for command in sql_commands:
            cursor.execute(command)

        conn.commit()
        print("✅ SUCCESS! Tables created correctly from schema.sql.")

    except Exception as e:
        print(f"❌ Error during setup: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
