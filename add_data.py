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

stocks = [
    ('INFY', 24.5, 700000, 0.0, 153000, 35000, 15.1),
    ('TCS', 30.2, 1450000, 0.0, 240000, 65000, 72.3),
    ('WIPRO', 21.0, 250000, 0.1, 89000, 18000, 72.9),
    ('RELIANCE', 28.5, 1950000, 0.4, 900000, 120000, 50.3),
    ('HDFC', 16.8, 1150000, 0.9, 210000, 140000, 0.0),
    ('TATAMOTORS', 17.5, 350000, 0.8, 430000, 45000, 46.4),
    ('AIRTEL', 55.0, 780000, 1.2, 145000, 75000, 54.7)
]

cursor.executemany('''
INSERT INTO fundamentals (symbol, pe_ratio, market_cap, debt, revenue, ebitda, promoter_holding)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', stocks)

conn.commit()
conn.close()
print("Market Data successfully added! 🎉")