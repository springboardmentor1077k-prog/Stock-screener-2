import os
import json
import sqlite3
from glob import glob

DATA_DIR = os.path.join("backend", "data")
DB_PATH = os.path.join("backend", "database", "stock_screener.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def insert_symbol(symbol, overview_data):

    # Skip invalid API responses
    if "Name" not in overview_data:
        print(f"Skipping {symbol} (invalid API response)")
        return None

    company_name = overview_data.get("Name")
    sector = overview_data.get("Sector")
    industry = overview_data.get("Industry")
    exchange = overview_data.get("Exchange")

    cursor.execute("""
        INSERT OR IGNORE INTO symbols (symbol, company_name, sector, industry, exchange)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol, company_name, sector, industry, exchange))

    cursor.execute("SELECT id FROM symbols WHERE symbol=?", (symbol,))
    result = cursor.fetchone()

    if result:
        return result[0]

    return None


def insert_fundamentals(company_id, overview_data):

    pe_ratio = overview_data.get("PERatio")
    peg_ratio = overview_data.get("PEGRatio")
    ebitda = overview_data.get("EBITDA")
    revenue = overview_data.get("RevenueTTM")

    cursor.execute("""
        SELECT id FROM fundamentals
        WHERE company_id=? AND report_date = DATE('now')
    """, (company_id,))

    if cursor.fetchone():
        return

    cursor.execute("""
        INSERT INTO fundamentals (
            company_id, pe_ratio, peg_ratio, debt_fcf,
            ebitda, revenue, promoter_holding, report_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'))
    """, (
        company_id,
        float(pe_ratio) if pe_ratio else None,
        float(peg_ratio) if peg_ratio else None,
        None,
        float(ebitda) if ebitda else None,
        float(revenue) if revenue else None,
        None
    ))


def insert_historical(company_id, price_data):

    series = price_data.get("Time Series (Daily)", {})

    for date, values in list(series.items())[:30]:

        close_price = values.get("4. close")

        cursor.execute("""
            SELECT id FROM historical_metrics
            WHERE company_id=? AND quarter=?
        """, (company_id, date))

        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO historical_metrics (
                company_id, quarter, revenue, ebitda, net_profit
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            company_id,
            date,
            None,
            None,
            float(close_price) if close_price else None
        ))


overview_files = glob(os.path.join(DATA_DIR, "*_company_overview.json"))

for file_path in overview_files:

    symbol = os.path.basename(file_path).split("_")[0]

    with open(file_path) as f:
        overview_data = json.load(f)

    company_id = insert_symbol(symbol, overview_data)

    if not company_id:
        continue

    insert_fundamentals(company_id, overview_data)

    prices_file = os.path.join(DATA_DIR, f"{symbol}_historical_prices.json")

    if os.path.exists(prices_file):

        with open(prices_file) as f:
            price_data = json.load(f)

        insert_historical(company_id, price_data)


conn.commit()
conn.close()

print("JSON data successfully inserted into database.")