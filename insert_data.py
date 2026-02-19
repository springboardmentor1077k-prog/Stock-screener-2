import yfinance as yf
import json
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, text

# 🔹 Database connection
engine = create_engine(
    "postgresql://postgres:newpassword123@localhost:5432/stock_screener"
)

# 🔹 Stocks list
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "INFY"]

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
            "market_cap": info.get("marketCap") or 0
        }

        # -------------------------------
        # 2️⃣ Fundamentals Snapshot
        # -------------------------------
        fundamentals = {
            "pe_ratio": info.get("trailingPE") or 0,
            "peg_ratio": info.get("pegRatio") or 0,
            "eps": info.get("trailingEps") or 0,
            "revenue": info.get("totalRevenue") or 0,
            "ebitda": info.get("ebitda") or 0,
            "debt": info.get("totalDebt") or 0,
            "free_cash_flow": info.get("freeCashflow") or 0,
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
        # Save JSON Snapshot
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

        # ======================================================
        # 🔥 DATABASE INSERTION (UPDATED CLEAN LOGIC)
        # ======================================================

        # 4️⃣ Insert into symbols
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO symbols (symbol, company_name, sector)
                VALUES (:symbol, :company_name, :sector)
                ON CONFLICT (symbol) DO NOTHING
            """), {
                "symbol": ticker_symbol,
                "company_name": company_profile["name"],
                "sector": company_profile["sector"]
            })

        # 5️⃣ Get symbol_id
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id FROM symbols WHERE symbol = :symbol
            """), {"symbol": ticker_symbol})
            symbol_id = result.fetchone()[0]

        # 6️⃣ Insert fundamentals snapshot
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO fundamentals
                (symbol_id, pe_ratio, peg_ratio, ebitda, revenue,
                 eps, debt, free_cash_flow, reported_date)
                VALUES
                (:symbol_id, :pe_ratio, :peg_ratio, :ebitda, :revenue,
                 :eps, :debt, :free_cash_flow, :reported_date)
            """), {
                "symbol_id": symbol_id,
                "reported_date": datetime.today().date(),
                **fundamentals
            })

        # 7️⃣ Insert historical prices (avoid duplicates)
        with engine.begin() as conn:
            for price in historical_prices:
                conn.execute(text("""
                    INSERT INTO historical_prices
                    (symbol_id, price_date, open, high, low, close, volume)
                    VALUES
                    (:symbol_id, :price_date, :open, :high, :low, :close, :volume)
                    ON CONFLICT (symbol_id, price_date) DO NOTHING
                """), {
                    "symbol_id": symbol_id,
                    "price_date": price["date"],
                    "open": price["open"],
                    "high": price["high"],
                    "low": price["low"],
                    "close": price["close"],
                    "volume": price["volume"]
                })

        print(f"✅ Database updated for {ticker_symbol}")

        time.sleep(2)

    except Exception as e:
        print(f"⚠ Error processing {ticker_symbol}: {e}")

print("\n🎯 Snapshot + database ingestion completed successfully.")
