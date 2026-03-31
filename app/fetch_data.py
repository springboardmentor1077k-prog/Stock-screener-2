# app/fetch_data.py

import yfinance as yf
import json

# 🔥 You can increase this list later
stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

data_list = []

for s in stocks:
    try:
        info = yf.Ticker(s).info

        stock = {
            "symbol": s,
            "name": info.get("shortName", ""),
            "sector": info.get("sector", ""),
            "pe_ratio": info.get("trailingPE", 0),
            "market_cap": info.get("marketCap", 0),
            "price": info.get("currentPrice", 0),
            "volume": info.get("volume", 0)
        }

        print(f"Fetched: {s}")  # ✅ debug

        data_list.append(stock)

    except Exception as e:
        print(f"Error fetching {s}:", e)

# 🔥 SAVE JSON
with open("data/stocks_data.json", "w") as f:
    json.dump(data_list, f, indent=4)

print("✅ Data fetched and saved to JSON")