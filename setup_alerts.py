import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

# Create Alerts Table 
cursor.execute('DROP TABLE IF EXISTS alerts')
cursor.execute('''
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    symbol TEXT,
    field TEXT,
    operator TEXT,
    value REAL,
    alert_type TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Adding Sample Data for testing
sample_data = [
    ('user1', 'INFY', 'pe_ratio', '<', 15.0, 'metric'),
    ('user1', 'WIPRO', 'revenue', '>', 15000.0, 'metric')
]
cursor.executemany('''
INSERT INTO alerts (user_id, symbol, field, operator, value, alert_type) 
VALUES (?, ?, ?, ?, ?, ?)''', sample_data)

conn.commit()
conn.close()
print("✅ Alerts table created and sample data added successfully!")