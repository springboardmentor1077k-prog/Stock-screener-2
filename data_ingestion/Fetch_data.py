# data_ingestion/find_and_fetch_companies.py
import os
import requests
import json
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"
DB_PATH = "../Database/stock_database.db"

if not API_KEY:
    raise ValueError("API key missing")

# ============================================
# EXPANDED COMPANY LIST (200+ companies)
# ============================================

# US Large Cap Stocks (S&P 500 companies)
LARGE_CAP_SYMBOLS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "GOOG", "META", "NVDA", "AMD", "INTC", "QCOM", "TXN",
    "AVGO", "CRM", "NOW", "ADBE", "ORCL", "SAP", "IBM", "CSCO", "HPQ", "DELL",
    "HPE", "AMZN", "NFLX", "SHOP", "UBER", "LYFT", "SNAP", "PINS", "RBLX", "ZM",
    "DOCU", "TEAM", "NET", "DDOG", "SNOW", "PLTR", "U", "TWLO", "OKTA", "ZS",
    
    # Financial
    "JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "COF",
    "BLK", "SCHW", "PYPL", "SQ", "FIS", "FISV", "ICE", "CME", "SPGI", "MCO",
    "ALL", "AIG", "MET", "PRU", "TRV", "PGR", "CB", "MMC", "AON", "AJG",
    
    # Healthcare
    "JNJ", "PFE", "MRK", "ABBV", "AMGN", "GILD", "BMY", "LLY", "MDT", "ABT",
    "UNH", "CVS", "CI", "ANTM", "HUM", "ISRG", "SYK", "ZBH", "BDX", "EW",
    "DHR", "TMO", "IQV", "LH", "DGX", "BIIB", "REGN", "VRTX", "ALXN", "ILMN",
    
    # Consumer
    "WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "MCD", "DIS", "CMG",
    "BKNG", "EXPE", "MAR", "HLT", "RCL", "CCL", "NCLH", "DAL", "UAL", "LUV",
    "PG", "KO", "PEP", "MO", "PM", "CL", "KMB", "GIS", "K", "MDLZ",
    
    # Industrial
    "BA", "CAT", "GE", "HON", "MMM", "UPS", "FDX", "LMT", "NOC", "RTX",
    "DE", "CAT", "CMI", "PCAR", "ETN", "EMR", "ROK", "ABB", "SIEGY", "HON",
    
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PSX", "VLO", "MPC", "KMI",
    "WMB", "OKE", "LNG", "HAL", "BKR", "NOV", "APA", "DVN", "HES", "MRO",
    
    # Telecom & Utilities
    "T", "VZ", "TMUS", "CHTR", "CMCSA", "DUK", "SO", "NEE", "D", "AEP",
    "EXC", "XEL", "WEC", "PEG", "ED", "EIX", "AEE", "DTE", "ETR", "FE"
]

# Mid Cap Stocks
MID_CAP_SYMBOLS = [
    "ZM", "DOCU", "TEAM", "NET", "DDOG", "SNOW", "PLTR", "U", "TWLO", "OKTA",
    "ZS", "MDB", "CRWD", "PANW", "FTNT", "CHKP", "VRSN", "AKAM", "FFIV", "JNPR",
    "MRNA", "BNTX", "NVAX", "SRPT", "EXAS", "TWST", "NTLA", "BEAM", "CRSP", "EDIT"
]

# Combine all symbols
ALL_SYMBOLS = list(set(LARGE_CAP_SYMBOLS + MID_CAP_SYMBOLS))
print(f"📊 Total target companies: {len(ALL_SYMBOLS)}")

DATA_FOLDER = "raw"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_existing_companies():
    """Get list of companies already in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT symbol FROM symbols")
        existing = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return set(existing)
    except Exception as e:
        print(f"⚠️ Could not read database: {e}")
        return set()

def check_symbol_exists_in_files(symbol):
    """Check if symbol already has a JSON file"""
    file_path = f"{DATA_FOLDER}/{symbol}_overview.json"
    return os.path.exists(file_path)

def fetch_overview(symbol, retry_count=3):
    """Fetch company overview with retry logic"""
    
    for attempt in range(retry_count):
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": API_KEY
            }
            
            response = requests.get(BASE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if data is valid
                if data and data.get("Symbol"):
                    # Add fetch timestamp
                    data["_fetch_timestamp"] = datetime.now().isoformat()
                    
                    # Save to file
                    filename = f"{DATA_FOLDER}/{symbol}_overview.json"
                    with open(filename, "w") as f:
                        json.dump(data, f, indent=2)
                    
                    # Extract key metrics
                    name = data.get("Name", "N/A")
                    sector = data.get("Sector", "N/A")
                    pe = data.get("PERatio", "N/A")
                    
                    print(f"✅ {symbol} - {name[:35]:35} | Sector: {sector[:15]:15} | P/E: {pe}")
                    return True
                else:
                    # No data returned - symbol might not exist
                    print(f"❌ {symbol}: No data available (symbol may not exist)")
                    return False
                    
            elif response.status_code == 429:
                print(f"⚠️ Rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                continue
            else:
                print(f"❌ {symbol}: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏱️ {symbol}: Timeout (attempt {attempt+1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(10)
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
            if attempt < retry_count - 1:
                time.sleep(5)
    
    return False

def find_available_companies():
    """Test which symbols are available in Alpha Vantage"""
    
    print("\n" + "=" * 80)
    print("🔍 TESTING SYMBOL AVAILABILITY")
    print("=" * 80)
    
    # Get already fetched companies
    existing_in_db = get_existing_companies()
    existing_in_files = set()
    
    # Check files
    for f in os.listdir(DATA_FOLDER):
        if f.endswith("_overview.json"):
            symbol = f.replace("_overview.json", "")
            existing_in_files.add(symbol)
    
    existing = existing_in_db | existing_in_files
    print(f"\n📊 Already have data for: {len(existing)} companies")
    
    # Find symbols to fetch
    to_fetch = [s for s in ALL_SYMBOLS if s not in existing]
    print(f"📊 Need to fetch: {len(to_fetch)} companies")
    
    if not to_fetch:
        print("\n🎉 All companies already fetched!")
        return []
    
    # Test first 10 to see if they exist
    print("\n🔍 Testing first 10 symbols for availability...")
    available = []
    unavailable = []
    
    for symbol in to_fetch[:10]:
        print(f"   Testing {symbol}...", end=" ")
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": API_KEY
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if data and data.get("Symbol"):
                print("✅ Available")
                available.append(symbol)
            else:
                print("❌ Not available")
                unavailable.append(symbol)
            time.sleep(2)  # Quick test with less delay
        except:
            print("❌ Error")
            unavailable.append(symbol)
    
    print(f"\n📊 Test Results:")
    print(f"   Available: {len(available)}")
    print(f"   Unavailable: {len(unavailable)}")
    
    if unavailable:
        print(f"\n⚠️ Unavailable symbols in first 10:")
        for sym in unavailable:
            print(f"   • {sym}")
    
    return to_fetch

def fetch_missing_companies():
    """Fetch only missing companies"""
    
    print("\n" + "=" * 80)
    print("📊 FETCHING MISSING COMPANIES")
    print("=" * 80)
    
    # Get existing companies
    existing_in_db = get_existing_companies()
    existing_in_files = set()
    
    for f in os.listdir(DATA_FOLDER):
        if f.endswith("_overview.json"):
            symbol = f.replace("_overview.json", "")
            existing_in_files.add(symbol)
    
    existing = existing_in_db | existing_in_files
    print(f"\n✅ Already have: {len(existing)} companies")
    
    # Find missing
    to_fetch = [s for s in ALL_SYMBOLS if s not in existing]
    print(f"📊 Need to fetch: {len(to_fetch)} companies")
    
    if not to_fetch:
        print("\n🎉 All 100+ companies already fetched!")
        return True
    
    print(f"\n🚀 Starting fetch for {len(to_fetch)} companies...")
    print(f"⏱️ Estimated time: ~{(len(to_fetch) * 12) / 60:.1f} minutes")
    print("=" * 80)
    
    fetched = 0
    failed = 0
    failed_symbols = []
    
    for i, symbol in enumerate(to_fetch, 1):
        print(f"\n[{i}/{len(to_fetch)}] Fetching {symbol}...")
        
        success = fetch_overview(symbol)
        
        if success:
            fetched += 1
        else:
            failed += 1
            failed_symbols.append(symbol)
        
        # Progress
        progress = (i / len(to_fetch)) * 100
        print(f"Progress: {progress:.1f}% | Fetched: {fetched} | Failed: {failed}")
        
        # Rate limiting
        if i < len(to_fetch):
            time.sleep(12)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FETCH SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully fetched: {fetched} new companies")
    print(f"❌ Failed to fetch: {failed} companies")
    print(f"📊 Total companies now: {len(existing) + fetched}")
    
    if failed_symbols:
        print(f"\n⚠️ Failed symbols:")
        for sym in failed_symbols[:20]:
            print(f"   • {sym}")
        if len(failed_symbols) > 20:
            print(f"   ... and {len(failed_symbols) - 20} more")
    
    print("=" * 80)
    
    return fetched > 0

def list_all_fetched_companies():
    """List all companies that have been fetched"""
    
    print("\n" + "=" * 80)
    print("📋 ALL FETCHED COMPANIES")
    print("=" * 80)
    
    files = os.listdir(DATA_FOLDER)
    overview_files = [f for f in files if f.endswith("_overview.json")]
    
    companies = []
    for file in overview_files:
        try:
            with open(os.path.join(DATA_FOLDER, file), 'r') as f:
                data = json.load(f)
                if data.get("Symbol"):
                    companies.append({
                        "symbol": data.get("Symbol"),
                        "name": data.get("Name", "N/A"),
                        "sector": data.get("Sector", "N/A"),
                        "pe": data.get("PERatio", "N/A")
                    })
        except:
            pass
    
    # Sort by symbol
    companies.sort(key=lambda x: x["symbol"])
    
    print(f"\n📊 Total companies: {len(companies)}")
    print(f"\n📊 By Sector:")
    
    sector_counts = {}
    for c in companies:
        sector = c["sector"]
        if sector != "N/A":
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {sector}: {count} companies")
    
    print(f"\n📊 Sample companies:")
    for c in companies[:20]:
        print(f"   • {c['symbol']} - {c['name'][:40]} - {c['sector']}")
    
    return companies

def suggest_more_symbols():
    """Suggest additional symbols to fetch"""
    
    print("\n" + "=" * 80)
    print("💡 SUGGESTED ADDITIONAL SYMBOLS")
    print("=" * 80)
    
    # Alternative symbols that might work
    alternative_symbols = [
        # Different tickers for same companies
        "BRK.B", "BRK.A", "LMT", "GD", "LHX", "TXT",
        "ADP", "PAYX", "CTSH", "IT", "GPN", "FLT",
        "ECL", "SHW", "PPG", "APD", "LIN", "DOW", "DD",
        
        # More tech companies
        "SE", "GRAB", "BIDU", "JD", "PDD", "BABA",
        "SPOT", "EA", "TTWO",
        
        # More healthcare
        "CVS", "WBA", "CAH", "MCK", "ABC", "HCA", "UHS",
        "ZTS", "IDXX", "WAT", "MTD"
    ]
    
    existing = set()
    for f in os.listdir(DATA_FOLDER):
        if f.endswith("_overview.json"):
            existing.add(f.replace("_overview.json", ""))
    
    new_suggestions = [s for s in alternative_symbols if s not in existing]
    
    if new_suggestions:
        print(f"\n📊 Found {len(new_suggestions)} new symbol suggestions:")
        for sym in new_suggestions[:20]:
            print(f"   • {sym}")
        
        print(f"\n💡 To fetch these, add them to ALL_SYMBOLS list")
    else:
        print("\n🎉 No more suggestions available")
    
    return new_suggestions

if __name__ == "__main__":
    print(f"\n🚀 Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First, find available companies
    to_fetch = find_available_companies()
    
    # Fetch missing companies
    fetch_missing_companies()
    
    # List all fetched companies
    companies = list_all_fetched_companies()
    
    # Suggest more symbols
    suggestions = suggest_more_symbols()
    
    # Count total valid companies
    valid_count = len([c for c in companies if c["pe"] != "N/A"])
    print(f"\n📊 SUMMARY:")
    print(f"   Total companies: {len(companies)}")
    print(f"   Valid companies (with PE ratio): {valid_count}")
    print(f"   Percentage: {(valid_count/len(companies)*100) if companies else 0:.1f}%")
    
    print(f"\n✅ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")