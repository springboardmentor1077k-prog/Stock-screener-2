import yfinance as yf
from app.db import get_connection

def insert_companies():
    conn = get_connection()
    cursor = conn.cursor()

    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]

    for ticker in symbols:
        stock = yf.Ticker(ticker)
        info = stock.info

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
    cursor.close()
    conn.close()

    print("Inserted companies successfully.")
