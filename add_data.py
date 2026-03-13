import sqlite3

# Connect to database
conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS fundamentals')

cursor.execute('''
CREATE TABLE fundamentals (
    symbol TEXT PRIMARY KEY,
    pe_ratio REAL,
    market_cap REAL,
    debt REAL,
    revenue REAL,
    ebitda REAL,
    promoter_holding REAL
)
''')

# Add real-looking Dummy Data
stocks = [
    ('INFY', 12.5, 75000, 0.1, 15000, 3000, 15.0),
    ('TCS', 25.0, 120000, 0.05, 25000, 6000, 72.0),
    ('WIPRO', 14.0, 40000, 0.2, 10000, 1500, 73.0),
    ('RELIANCE', 30.0, 200000, 1.5, 80000, 15000, 50.0),
    ('HDFC', 18.0, 150000, 2.0, 40000, 8000, 0.0)
]

cursor.executemany('''
INSERT INTO fundamentals (symbol, pe_ratio, market_cap, debt, revenue, ebitda, promoter_holding)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', stocks)

conn.commit()
conn.close()
print("Data successfully added! 🎉")