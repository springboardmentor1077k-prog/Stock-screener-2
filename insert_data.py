from sqlalchemy import create_engine, text
import yfinance as yf
import pandas as pd

# 🔹 Replace with your actual password
engine = create_engine(
    "postgresql://postgres:newpassword123@localhost:5432/stock_screener"
)

# 🔹 List of stocks to insert
symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

for symbol in symbols:
    print(f"Inserting {symbol}...")

    ticker = yf.Ticker(symbol)
    info = ticker.info

    # -------------------------------
    # 1️⃣ Insert into stocks table
    # -------------------------------
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO stocks (symbol, company_name, sector)
            VALUES (:symbol, :company_name, :sector)
            ON CONFLICT (symbol) DO NOTHING
        """), {
            "symbol": symbol,
            "company_name": info.get("longName"),
            "sector": info.get("sector")
        })

    # -------------------------------
    # 2️⃣ Get stock_id
    # -------------------------------
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id FROM stocks WHERE symbol = :symbol
        """), {"symbol": symbol})
        stock_id = result.fetchone()[0]

    # -------------------------------
    # 3️⃣ Insert fundamentals
    # -------------------------------
    fundamental_data = {
        "stock_id": stock_id,
        "pe_ratio": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
        "revenue": info.get("totalRevenue"),
        "ebitda": info.get("ebitda"),
        "debt": info.get("totalDebt"),
        "free_cash_flow": info.get("freeCashflow"),
        "revenue_growth": None
    }

    df = pd.DataFrame([fundamental_data])
    df.to_sql("fundamentals", engine, if_exists="append", index=False)

print("✅ All data inserted successfully.")
