import os
import json
import sqlite3
from glob import glob

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def safe_load_json(file_path):
    try:
        with open(file_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load {file_path}: {e}")
        return None


# -----------------------------
# INSERT SYMBOL
# -----------------------------
def insert_symbol(cursor, symbol, overview_data):

    if "Name" not in overview_data:
        print(f"Skipping {symbol} (invalid API response)")
        return None

    cursor.execute("""
        INSERT OR IGNORE INTO symbols (
            symbol,
            company_name,
            sector,
            industry,
            exchange,
            country,
            website
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        overview_data.get("Name"),
        overview_data.get("Sector"),
        overview_data.get("Industry"),
        overview_data.get("Exchange"),
        overview_data.get("Country"),
        overview_data.get("Website")
    ))

    cursor.execute("SELECT id FROM symbols WHERE symbol=?", (symbol,))
    result = cursor.fetchone()

    return result[0] if result else None


# -----------------------------
# INSERT FUNDAMENTALS
# -----------------------------
def insert_fundamentals(cursor, company_id, fundamentals_data):

    cursor.execute("""
        SELECT id FROM fundamentals
        WHERE company_id=? AND report_date = DATE('now')
    """, (company_id,))

    if cursor.fetchone():
        return

    cursor.execute("""
        INSERT INTO fundamentals (
            company_id,
            pe_ratio,
            peg_ratio,
            market_cap,
            revenue,
            revenue_growth,
            ebitda,
            profit_margin,
            total_debt,
            debt_to_equity,
            roe,
            roa,
            eps,
            book_value,
            dividend_yield,
            current_price,
            report_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'))
    """, (
        company_id,
        fundamentals_data.get("PERatio"),
        fundamentals_data.get("PEGRatio"),
        fundamentals_data.get("MarketCap"),
        fundamentals_data.get("RevenueTTM"),
        fundamentals_data.get("RevenueGrowth") or 0,
        fundamentals_data.get("EBITDA"),
        fundamentals_data.get("ProfitMargins"),
        fundamentals_data.get("TotalDebt"),
        fundamentals_data.get("DebtToEquity"),
        fundamentals_data.get("ReturnOnEquity"),
        fundamentals_data.get("ReturnOnAssets"),
        fundamentals_data.get("EPS"),
        fundamentals_data.get("BookValue"),
        fundamentals_data.get("DividendYield"),
        fundamentals_data.get("CurrentPrice")   # IMPORTANT
    ))


# -----------------------------
# INSERT HISTORICAL PRICES
# -----------------------------
def insert_historical(cursor, company_id, price_data):

    prices = price_data.get("HistoricalPrices", [])

    for row in prices:

        date = row.get("date")

        cursor.execute("""
            SELECT id FROM historical_metrics
            WHERE company_id=? AND date=?
        """, (company_id, date))

        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO historical_metrics (
                company_id,
                date,
                open,
                high,
                low,
                close,
                volume
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            date,
            row.get("open"),
            row.get("high"),
            row.get("low"),
            row.get("close"),
            row.get("volume")
        ))


# -----------------------------
# CALCULATE PRICE GROWTH
# -----------------------------
def calculate_price_growth(prices):

    if len(prices) < 2:
        return 0

    first_price = prices[0]["close"]
    last_price = prices[-1]["close"]

    if first_price == 0:
        return 0

    return (last_price - first_price) / first_price


# -----------------------------
# MAIN INGESTION FUNCTION
# -----------------------------
def run_ingestion():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    overview_files = glob(os.path.join(DATA_DIR, "*_company_overview.json"))

    print(f"Found {len(overview_files)} company overview files")

    for file_path in overview_files:

        symbol = os.path.basename(file_path).split("_")[0]

        overview_data = safe_load_json(file_path)

        if not overview_data:
            continue

        company_id = insert_symbol(cursor, symbol, overview_data)

        if not company_id:
            continue

        fundamentals_file = os.path.join(DATA_DIR, f"{symbol}_fundamentals_income.json")

        if os.path.exists(fundamentals_file):

            fundamentals_data = safe_load_json(fundamentals_file)

            if fundamentals_data:
                insert_fundamentals(cursor, company_id, fundamentals_data)

        prices_file = os.path.join(DATA_DIR, f"{symbol}_historical_prices.json")

        if os.path.exists(prices_file):

            price_data = safe_load_json(prices_file)

            if price_data:

                insert_historical(cursor, company_id, price_data)

                prices = price_data.get("HistoricalPrices", [])

                growth = calculate_price_growth(prices)

                cursor.execute("""
                UPDATE fundamentals
                SET price_growth = ?
                WHERE company_id = ?
                """, (growth, company_id))

    conn.commit()
    conn.close()

    print("JSON data successfully inserted into database.")


if __name__ == "__main__":
    run_ingestion()