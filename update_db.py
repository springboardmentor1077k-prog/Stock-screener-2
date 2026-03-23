import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_stock_screener")

def upgrade_database():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Add the brand new 'email' column securely!
        print("Upgrading database schema to officially store user emails...")
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE AFTER username;")
        
        conn.commit()
        print("✅ Success! Your database is officially upgraded and ready for Emails!")
        
    except mysql.connector.Error as err:
        print(f"Notes: {err} (If it says 'Duplicate column', it means it is completely ready!)")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    upgrade_database()
