import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_stock_screener")

# Fake Company Sample Data (Includes various metrics for testing filters)
# Tuple format: (symbol, name, sector, PE_ratio, revenue_millions, EBITDA_millions, debt_to_equity)
COMPANIES = [
    ("AAPL", "Apple Inc.", "Technology", 28.5, 383000, 125000, 1.4),
    ("MSFT", "Microsoft Corp.", "Technology", 35.2, 211000, 102000, 0.4),
    ("AMZN", "Amazon.com Inc.", "Retail", 60.1, 514000, 54000, 0.9),
    ("GOOGL", "Alphabet Inc.", "Technology", 22.8, 282000, 90000, 0.1),
    ("TSLA", "Tesla Inc.", "Automotive", 45.4, 81000, 13000, 0.05),
    ("JNJ", "Johnson & Johnson", "Healthcare", 25.4, 94000, 32000, 0.5),
    ("V", "Visa Inc.", "Finance", 30.2, 29000, 20000, 0.6),
    ("WMT", "Walmart Inc.", "Retail", 27.1, 611000, 36000, 0.7),
    ("JPM", "JPMorgan Chase", "Finance", 11.5, 128000, 48000, 1.2),
    ("PG", "Procter & Gamble", "Consumer", 24.5, 80000, 21000, 1.0),
    ("XOM", "Exxon Mobil", "Energy", 8.4, 413000, 85000, 0.2),
    ("UNH", "UnitedHealth Group", "Healthcare", 18.2, 324000, 28000, 0.7),
    ("HD", "Home Depot", "Retail", 19.5, 157000, 25000, 3.1),
    ("MA", "Mastercard", "Finance", 35.6, 22000, 13000, 4.2),
    ("CVX", "Chevron Corp.", "Energy", 9.1, 246000, 52000, 0.1),
    ("ABBV", "AbbVie Inc.", "Healthcare", 14.8, 58000, 26000, 3.8),
    ("MRK", "Merck & Co.", "Healthcare", 12.3, 59000, 22000, 0.8),
    ("PEP", "PepsiCo Inc.", "Consumer", 26.7, 86000, 15000, 2.2),
    ("KO", "Coca-Cola Co.", "Consumer", 23.4, 43000, 13000, 1.8),
    ("F", "Ford Motor", "Automotive", 5.2, 158000, 14000, 4.5)
]

def seed_database():
    try:
        # Connect to PostgreSQL
        print(f"Connecting to database '{DB_NAME}' as '{DB_USER}'...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        print("Injecting companies into 'symbols' and 'fundamentals' tables...")
        # Clear existing data so we don't accidentally double-insert
        cursor.execute("TRUNCATE TABLE fundamentals CASCADE")
        cursor.execute("TRUNCATE TABLE symbols CASCADE")
        
        for comp in COMPANIES:
            symbol, name, sector, pe, rev, ebitda, dte = comp
            
            # 1. Insert into symbols
            cursor.execute(
                "INSERT INTO symbols (symbol, company_name, sector) VALUES (%s, %s, %s) RETURNING id",
                (symbol, name, sector)
            )
            
            # We need the new record's assigned ID for the foreign key
            company_id = cursor.fetchone()[0]
            
            # 2. Insert into fundamentals
            cursor.execute(
                """INSERT INTO fundamentals 
                   (company_id, pe_ratio, revenue, ebitda, debt_to_equity) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (company_id, pe, rev, ebitda, dte)
            )

        # Add a default admin user
        from backend.auth import get_password_hash
        password_hash = get_password_hash("admin123")
        
        print("Creating default user 'admin'...")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ('admin', 'admin@stock.com', password_hash))
            
        conn.commit()
        print(f"✅ Successfully injected {len(COMPANIES)} fake companies and 1 admin user into your PostgreSQL database!")
        
    except Exception as err:
        print(f"❌ Database error: {err}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    seed_database()
