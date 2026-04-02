# data_ingestion/load_fundamentals_to_db.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "../Database/stock_database.db"
DATA_FOLDER = "raw"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_company_id(symbol):
    """Get company ID from symbols table"""
    cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol,))
    row = cursor.fetchone()
    return row[0] if row else None

def parse_numeric(value):
    """Safely parse numeric values"""
    if value in [None, "None", "", "N/A"]:
        return None
    try:
        if isinstance(value, str):
            value = value.replace(',', '').replace('$', '')
        return float(value) if value else None
    except (ValueError, TypeError):
        return None

def insert_fundamentals(data):
    """Insert fundamentals data"""
    
    symbol = data.get("Symbol")
    company_id = get_company_id(symbol)
    
    if not company_id:
        return False
    
    # Extract fundamentals
    pe_ratio = parse_numeric(data.get("PERatio"))
    peg_ratio = parse_numeric(data.get("PEGRatio"))
    ebitda = parse_numeric(data.get("EBITDA"))
    revenue = parse_numeric(data.get("RevenueTTM"))
    report_date = data.get("LatestQuarter")
    
    # Debt to Free Cash Flow (calculate if available)
    debt = parse_numeric(data.get("TotalDebt"))
    free_cash_flow = parse_numeric(data.get("FreeCashFlow"))
    debt_fcf = debt / free_cash_flow if debt and free_cash_flow and free_cash_flow != 0 else None
    
    # Promoter holding (not available in overview, set to None)
    promoter_holding = None
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO fundamentals
            (company_id, pe_ratio, peg_ratio, debt_fcf, ebitda, revenue, 
             promoter_holding, report_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id, pe_ratio, peg_ratio, debt_fcf, ebitda, revenue,
            promoter_holding, report_date, datetime.now()
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting {symbol}: {e}")
        return False

def load_all_fundamentals():
    """Load all fundamentals data"""
    
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
                    if insert_fundamentals(data):
                        success_count += 1
                        print(f"✅ Loaded fundamentals: {data['Symbol']}")
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                    
        except Exception as e:
            print(f"❌ Error reading {file}: {e}")
            fail_count += 1
    
    print(f"\n📊 Summary: {success_count} loaded, {fail_count} failed")
    return success_count

if __name__ == "__main__":
    print("=" * 60)
    print("LOADING FUNDAMENTALS TO DATABASE")
    print("=" * 60)
    
    count = load_all_fundamentals()
    
    conn.close()
    
    print(f"\n✅ Loaded fundamentals for {count} companies!")