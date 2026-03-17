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
    ('INFY', '2025-Q1', 1000), ('INFY', '2025-Q2', 1100), ('INFY', '2025-Q3', 1210), ('INFY', '2025-Q4', 1331),
    ('TCS', '2025-Q1', 2000), ('TCS', '2025-Q2', 2050), ('TCS', '2025-Q3', 2100), ('TCS', '2025-Q4', 2150),
    ('WIPRO', '2025-Q1', 800), ('WIPRO', '2025-Q2', 900), ('WIPRO', '2025-Q3', 1035), ('WIPRO', '2025-Q4', 1190)
]

cursor.executemany('''
INSERT INTO historical_metrics (company_id, quarter, revenue)
VALUES (?, ?, ?)
''', history_data)

conn.commit()
conn.close()
print("✅ Raw Revenue Data successfully added to Database!")