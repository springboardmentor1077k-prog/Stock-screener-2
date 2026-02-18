import yfinance as yf
import json

def fetch_stock_data(ticker_symbol):
    print(f"Fetching data for: {ticker_symbol}...")
    
    # 1. Connect to the Stock (Create Ticker Object)
    stock = yf.Ticker(ticker_symbol)
    try:
        info = stock.info
        company_profile = {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "summary": info.get("longBusinessSummary", "N/A")
        }
        print("✅ Step 1: Company Info Fetched")
    except Exception as e:
        print(f"❌ Error fetching info: {e}")
        company_profile = {}

    try:
        pe_ratio = info.get("trailingPE", "N/A")
        market_cap = info.get("marketCap", "N/A")
        fundamentals = {
            "pe_ratio": pe_ratio,
            "market_cap": market_cap
        }
        print(f"✅ Step 2: Fundamental Metric Fetched (PE: {pe_ratio})")
    except Exception as e:
        print(f"❌ Error fetching fundamentals: {e}")
        fundamentals = {}

    try:
        # history() function calls the API to get price data
        hist = stock.history(period="1mo")
        
        # Convert Dataframe to JSON readable format
        history_data = json.loads(hist.to_json(orient="index", date_format="iso"))
        print("✅ Step 3: Historical Data Fetched")
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        history_data = {}

    final_data = {
        "ticker": ticker_symbol,
        "company_profile": company_profile,
        "fundamentals": fundamentals,
        "historical_prices": history_data
    }

    return final_data

# --- Main Execution ---
if __name__ == "__main__":
    # Infosys (NSE) Stock Symbol
    stock_symbol = "INFY.NS" 
    data = fetch_stock_data(stock_symbol)

    print("\n--- JSON RESPONSE ---")
    json_output = json.dumps(data, indent=4)
    print(json_output)

    filename = "stock_data.json"
    with open(filename, "w") as f:
        f.write(json_output)
    
    print(f"\n🎉 Success! Data saved to '{filename}' locally.")