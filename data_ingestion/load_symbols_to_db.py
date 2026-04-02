# data_ingestion/load_symbols_to_db.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "../Database/stock_database.db"
DATA_FOLDER = "raw"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def insert_symbol(data):
    """Insert symbol data into database"""
    
    symbol = data.get("Symbol")
    name = data.get("Name")
    sector = data.get("Sector")
    industry = data.get("Industry")
    exchange = data.get("Exchange")
    
    if not symbol:
        return False
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO symbols
            (symbol, company_name, sector, industry, exchange, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (symbol, name, sector, industry, exchange, datetime.now()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting {symbol}: {e}")
        return False

def load_all_json():
    """Load all overview JSON files"""
    
    files = os.listdir(DATA_FOLDER)
    overview_files = [f for f in files if f.endswith("_overview.json")]
    
    print(f"Found {len(overview_files)} overview files")
    
    success_count = 0
    fail_count = 0
    
    for file in overview_files:
        path = os.path.join(DATA_FOLDER, file)
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
                if data.get("Symbol"):
                    if insert_symbol(data):
                        success_count += 1
                        print(f"✅ Inserted: {data['Symbol']} - {data.get('Name', 'N/A')[:40]}")
                    else:
                        fail_count += 1
                else:
                    print(f"⚠️ No symbol in {file}")
                    fail_count += 1
                    
        except Exception as e:
            print(f"❌ Error reading {file}: {e}")
            fail_count += 1
    
    print(f"\n📊 Summary: {success_count} inserted, {fail_count} failed")
    return success_count

if __name__ == "__main__":
    print("=" * 60)
    print("LOADING SYMBOLS TO DATABASE")
    print("=" * 60)
    
    count = load_all_json()
    
    conn.close()
    
    print(f"\n✅ Loaded {count} companies to database!")