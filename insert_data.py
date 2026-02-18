import yfinance as yf
import json
import os
import time
from datetime import datetime

# 🔹 Stocks list
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "INFY"]

# 🔹 JSON folder
DATA_FOLDER = "yf_data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

for ticker_symbol in symbols:
    print(f"\nFetching {ticker_symbol}...")

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        history = ticker.history(period="1y")

        if not info or history.empty:
            print(f"❌ Skipping {ticker_symbol} (No valid data)")
            continue

        # -------------------------------
        # 1️⃣ Company Profile
        # -------------------------------
        company_profile = {
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "website": info.get("website"),
            "market_cap": info.get("marketCap")
        }

        # -------------------------------
        # 2️⃣ Fundamentals
        # -------------------------------
        fundamentals = {
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "revenue": info.get("totalRevenue"),
            "ebitda": info.get("ebitda"),
            "debt": info.get("totalDebt"),
            "free_cash_flow": info.get("freeCashflow"),
            "peg_ratio": info.get("pegRatio")
        }

        # -------------------------------
        # 3️⃣ Historical Prices
        # -------------------------------
        historical_prices = []

        for date, row in history.iterrows():
            historical_prices.append({
                "date": str(date.date()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })

        # -------------------------------
        # Final Snapshot JSON
        # -------------------------------
        stock_json = {
            "ticker": ticker_symbol,
            "snapshot_date": datetime.now().isoformat(),
            "company_profile": company_profile,
            "fundamentals": fundamentals,
            "historical_prices": historical_prices
        }

        file_path = os.path.join(DATA_FOLDER, f"{ticker_symbol}_structured.json")

        with open(file_path, "w") as f:
            json.dump(stock_json, f, indent=4)

        print(f"✅ JSON saved for {ticker_symbol}")

        time.sleep(2)

    except Exception as e:
        print(f"⚠ Error fetching {ticker_symbol}: {e}")

print("\n🎯 Structured stock snapshot data generated successfully.")
