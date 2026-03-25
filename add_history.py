import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS historical_metrics')
cursor.execute('''
CREATE TABLE historical_metrics (
    company_id TEXT,
    quarter TEXT,
    revenue REAL
)
''')

history_data = [
    # INFY Growth trend
    ('INFY', '2025-Q1', 37500), ('INFY', '2025-Q2', 38000), ('INFY', '2025-Q3', 38500), ('INFY', '2025-Q4', 39000),
    # TCS Consistent growth
    ('TCS', '2025-Q1', 59000), ('TCS', '2025-Q2', 59500), ('TCS', '2025-Q3', 60000), ('TCS', '2025-Q4', 61500),
    # WIPRO slight ups and downs
    ('WIPRO', '2025-Q1', 22000), ('WIPRO', '2025-Q2', 22500), ('WIPRO', '2025-Q3', 22200), ('WIPRO', '2025-Q4', 22300),
    # RELIANCE massive numbers
    ('RELIANCE', '2025-Q1', 215000), ('RELIANCE', '2025-Q2', 220000), ('RELIANCE', '2025-Q3', 228000), ('RELIANCE', '2025-Q4', 237000),
    # HDFC
    ('HDFC', '2025-Q1', 48000), ('HDFC', '2025-Q2', 50000), ('HDFC', '2025-Q3', 54000), ('HDFC', '2025-Q4', 58000),
    # TATAMOTORS
    ('TATAMOTORS', '2025-Q1', 105000), ('TATAMOTORS', '2025-Q2', 104000), ('TATAMOTORS', '2025-Q3', 108000), ('TATAMOTORS', '2025-Q4', 113000),
    # AIRTEL
    ('AIRTEL', '2025-Q1', 35000), ('AIRTEL', '2025-Q2', 36000), ('AIRTEL', '2025-Q3', 36500), ('AIRTEL', '2025-Q4', 37500)
]

cursor.executemany('''
INSERT INTO historical_metrics (company_id, quarter, revenue)
VALUES (?, ?, ?)
''', history_data)

conn.commit()
conn.close()
print("✅Historical Revenue Data successfully added!")