import sqlite3

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

print("Adding indexes to the database...")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON fundamentals(symbol);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_pe_ratio ON fundamentals(pe_ratio);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_revenue ON fundamentals(revenue);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_quarter ON historical_metrics(quarter);")

conn.commit()
conn.close()
print("✅ Indexes added successfully! Database is now ultra-fast.")