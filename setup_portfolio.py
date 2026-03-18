import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

# Create Portfolio Table
cursor.execute('DROP TABLE IF EXISTS portfolio')
cursor.execute('''
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    symbol TEXT,
    quantity INTEGER,
    buy_price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Adding Sample Data 
sample_data = [
    ('user1', 'INFY', 10, 1400.0),
    ('user1', 'TCS', 5, 3000.0)
]
cursor.executemany('INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (?, ?, ?, ?)', sample_data)

conn.commit()
conn.close()
print("✅ Portfolio table created and sample data added successfully!")