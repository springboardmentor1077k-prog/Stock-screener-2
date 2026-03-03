import yfinance as yf
import json
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, text

# ======================================================
# DATABASE CONNECTION
# ======================================================

engine = create_engine(
    "postgresql://postgres:newpassword123@localhost:5432/stock_screener"
)

# ======================================================
# STOCK LIST
# ======================================================

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "INFY"]

DATA_FOLDER = "yf_data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ======================================================
# PROCESS EACH STOCK
# ======================================================

for ticker_symbol in symbols:

    print(f"\nFetching {ticker_symbol}...")

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        history = ticker.history(period="1y")

        if not info or history.empty:
            print(f"❌ Skipping {ticker_symbol} (No valid data)")
            continue

        # ======================================================
        # COMPANY PROFILE
        # ======================================================

        company_profile = {
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "website": info.get("website"),
            "market_cap": info.get("marketCap") or 0
        }

        # ======================================================
        # CALCULATED METRICS (Aligned With main.py)
        # ======================================================

        pe_ratio = info.get("trailingPE") or 0
        eps = info.get("trailingEps") or 0
        revenue = info.get("totalRevenue") or 0
        debt = info.get("totalDebt") or 0
        market_cap = info.get("marketCap") or 0

        revenue_growth = info.get("revenueGrowth")
        revenue_growth = (revenue_growth * 100) if revenue_growth else 0

        first_close = history.iloc[0]["Close"]
        last_close = history.iloc[-1]["Close"]
        price_change_1y = ((last_close - first_close) / first_close) * 100

        # ======================================================
        # HISTORICAL PRICES
        # ======================================================

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

        # ======================================================
        # SAVE JSON SNAPSHOT
        # ======================================================

        stock_json = {
            "ticker": ticker_symbol,
            "snapshot_date": datetime.now().isoformat(),
            "company_profile": company_profile,
            "fundamentals": {
                "pe_ratio": pe_ratio,
                "eps": eps,
                "revenue": revenue,
                "debt": debt,
                "market_cap": market_cap,
                "revenue_growth": revenue_growth,
                "price_change_1y": price_change_1y
            },
            "historical_prices": historical_prices
        }

        file_path = os.path.join(DATA_FOLDER, f"{ticker_symbol}_structured.json")

        with open(file_path, "w") as f:
            json.dump(stock_json, f, indent=4)

        print(f"✅ JSON saved for {ticker_symbol}")

        # ======================================================
        # DATABASE INSERTION
        # ======================================================

        # 1️⃣ Insert into symbols
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

        # 2️⃣ Get symbol_id
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id FROM symbols WHERE symbol = :symbol
            """), {"symbol": ticker_symbol})
            symbol_id = result.fetchone()[0]

        # 3️⃣ Insert fundamentals (ONLY ONCE)
        # 3️⃣ Insert fundamentals (SAFE + UPDATE IF EXISTS)

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO fundamentals
                (symbol_id, pe_ratio, eps, revenue,
                debt, market_cap, revenue_growth,
                price_change_1y, reported_date)
                VALUES
                (:symbol_id, :pe_ratio, :eps, :revenue,
                :debt, :market_cap, :revenue_growth,
                :price_change_1y, :reported_date)
                ON CONFLICT (symbol_id, reported_date)
                DO UPDATE SET
                    pe_ratio = EXCLUDED.pe_ratio,
                    eps = EXCLUDED.eps,
                    revenue = EXCLUDED.revenue,
                    debt = EXCLUDED.debt,
                    market_cap = EXCLUDED.market_cap,
                    revenue_growth = EXCLUDED.revenue_growth,
                    price_change_1y = EXCLUDED.price_change_1y
            """), {
                "symbol_id": symbol_id,
                "pe_ratio": float(pe_ratio),
                "eps": float(eps),
                "revenue": float(revenue),
                "debt": float(debt),
                "market_cap": float(market_cap),
                "revenue_growth": float(revenue_growth),
                "price_change_1y": float(price_change_1y),
                "reported_date": datetime.now().date()
            })

        # 4️⃣ Insert historical prices properly
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
