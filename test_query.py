import sqlite3

conn = sqlite3.connect("stock_analysis.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM symbols")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
