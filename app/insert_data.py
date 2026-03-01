import yfinance as yf
from datetime import date
from app.db import get_connection


def insert_companies():
    conn = get_connection()
    cursor = conn.cursor()

    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]

    for ticker in symbols:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Insert into symbols table
        cursor.execute("""
            INSERT IGNORE INTO symbols
            (symbol, company_name, sector, industry, exchange)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            ticker,
            info.get("longName"),
            info.get("sector"),
            info.get("industry"),
            info.get("exchange")
        ))

        conn.commit()

        # Get company_id
        cursor.execute("SELECT id FROM symbols WHERE symbol = %s", (ticker,))
        result = cursor.fetchone()

        if not result:
            continue

        company_id = result[0]

        # Insert fundamentals
        cursor.execute("""
            INSERT INTO fundamentals
            (company_id, pe_ratio, revenue, ebitda, report_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            company_id,
            info.get("trailingPE"),
            info.get("totalRevenue"),
            info.get("ebitda"),
            date.today()
        ))

        conn.commit()

    cursor.close()
    conn.close()

    print("Inserted companies + fundamentals successfully.")