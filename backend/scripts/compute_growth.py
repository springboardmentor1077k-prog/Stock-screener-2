import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go to backend/
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DELETE FROM price_growth")

cursor.execute("""
INSERT INTO price_growth (company_id, date, price_growth)
SELECT
    company_id,
    date,
    COALESCE(
        (close - LAG(close) OVER (
            PARTITION BY company_id ORDER BY date
        )) * 1.0 /
        LAG(close) OVER (
            PARTITION BY company_id ORDER BY date
        ),
        0
    ) AS price_growth
FROM historical_metrics
""")

conn.commit()
conn.close()

print("Price growth computed successfully")