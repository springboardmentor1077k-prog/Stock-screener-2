import os
import json
from sqlalchemy import text
from database import engine
from datetime import date

STRUCTURED_FOLDER = "data/structured"


def ingest_data():

    files = [
        f for f in os.listdir(STRUCTURED_FOLDER)
        if f.endswith("_normalized_structured.json")
    ]

    if not files:
        print("No normalized files found.")
        return

    with engine.begin() as conn:

        for file in files:
            path = os.path.join(STRUCTURED_FOLDER, file)

            with open(path, "r") as f:
                stock = json.load(f)

            print(f"Inserting {stock['ticker']} into symbols...")

            # ----------------------------
            # Insert into symbols
            # ----------------------------
            conn.execute(text("""
                INSERT INTO symbols (symbol, company_name, sector, industry, exchange)
                VALUES (:symbol, :company_name, :sector, :industry, :exchange)
                ON CONFLICT (symbol) DO NOTHING
            """), {
                "symbol": stock["ticker"],
                "company_name": stock["company_profile"]["name"],
                "sector": stock["company_profile"]["sector"],
                "industry": stock["company_profile"]["industry"],
                "exchange": "NASDAQ"
            })

            # ----------------------------
            # Fetch symbol_id
            # ----------------------------
            result = conn.execute(text("""
                SELECT id FROM symbols WHERE symbol = :symbol
            """), {"symbol": stock["ticker"]})

            symbol_id = result.scalar()

            # ----------------------------
            # Insert into fundamentals
            # ----------------------------
            fundamentals = stock["fundamentals"]

            conn.execute(text("""
                INSERT INTO fundamentals
                (company_id, pe_ratio, revenue, report_date)
                VALUES (:company_id, :pe_ratio, :revenue, :report_date)
                ON CONFLICT (company_id, report_date) DO NOTHING
            """), {
                "company_id": symbol_id,
                "pe_ratio": fundamentals.get("pe_ratio"),
                "revenue": fundamentals.get("revenue_ttm"),
                "report_date": date.today()
            })

    print("\nSymbols + Fundamentals ingestion complete.")


if __name__ == "__main__":
    ingest_data()