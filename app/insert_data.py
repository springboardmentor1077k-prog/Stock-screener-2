import json
from db import get_connection

conn = get_connection()
cursor = conn.cursor()

# Load JSON file
with open("data/stocks_data.json", "r") as file:
    data = json.load(file)

for stock in data:
    cursor.execute(
        """
        INSERT INTO stocks (symbol, name, sector, pe_ratio, market_cap, price, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            stock["symbol"],
            stock["name"],
            stock["sector"],
            stock["pe_ratio"],
            stock["market_cap"],
            stock["price"],
            stock["volume"]
        )
    )

conn.commit()
cursor.close()
conn.close()

print("✅ JSON data inserted successfully")