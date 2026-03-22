import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_stock_screener")

COMPANIES = [
    ("AAPL", "Apple Inc.", "Technology", 28.5, 383000, 125000, 1.2),
    ("MSFT", "Microsoft Corp.", "Technology", 35.2, 211000, 95000, 0.8),
    ("TSLA", "Tesla Inc.", "Automotive", 45.0, 96000, 14000, 0.4),
    ("AMZN", "Amazon.com", "Retail", 50.1, 513000, 60000, 1.1),
    ("GOOGL", "Alphabet Inc.", "Technology", 25.4, 282000, 91000, 0.3),
    ("NVDA", "NVIDIA Corp.", "Technology", 65.3, 26000, 11000, 0.5),
    ("JPM", "JPMorgan Chase", "Finance", 10.5, 128000, 48000, 2.5),
    ("V", "Visa Inc.", "Finance", 30.2, 29000, 20000, 1.5),
    ("WMT", "Walmart Inc.", "Retail", 22.1, 611000, 35000, 0.9),
    ("JNJ", "Johnson & Johnson", "Healthcare", 15.6, 94000, 31000, 0.6),
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
    # Let's add one with PE < 6 specifically to test
    ("F", "Ford Motor", "Automotive", 5.2, 158000, 14000, 4.5)
]

def seed_database():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Clear existing data so we don't accidentally double-insert
        cursor.execute("DELETE FROM fundamentals")
        cursor.execute("DELETE FROM symbols")
        
        print("Injecting companies into 'symbols' and 'fundamentals' tables...")
        
        for comp in COMPANIES:
            symbol, name, sector, pe, rev, ebitda, dte = comp
            
            # 1. Insert into symbols
            cursor.execute(
                "INSERT INTO symbols (symbol, company_name, sector) VALUES (%s, %s, %s)",
                (symbol, name, sector)
            )
            
            # We need the new record's assigned ID for the foreign key
            company_id = cursor.lastrowid
            
            # 2. Insert into fundamentals
            cursor.execute(
                """INSERT INTO fundamentals 
                   (company_id, pe_ratio, revenue, ebitda, debt_to_equity) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (company_id, pe, rev, ebitda, dte)
            )
            
        conn.commit()
        print(f"✅ Successfully injected {len(COMPANIES)} fake companies into your MySQL database!")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    seed_database()
