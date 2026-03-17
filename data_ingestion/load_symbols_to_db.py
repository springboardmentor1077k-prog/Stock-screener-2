import sqlite3
import json
import os


DB_PATH = "../Database/stock_database.db"
DATA_FOLDER = "raw"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def insert_symbol(data):

    symbol = data.get("Symbol")
    name = data.get("Name")
    sector = data.get("Sector")
    industry = data.get("Industry")
    exchange = data.get("Exchange")

    if not symbol:
        return

    cursor.execute("""
        INSERT OR IGNORE INTO symbols
        (symbol, company_name, sector, industry, exchange)
        VALUES (?, ?, ?, ?, ?)
    """, (symbol, name, sector, industry, exchange))

    conn.commit()


def load_all_json():

    files = os.listdir(DATA_FOLDER)

    for file in files:

        if file.endswith("_overview.json"):

            path = os.path.join(DATA_FOLDER, file)

            with open(path, "r") as f:
                data = json.load(f)

                insert_symbol(data)

                print("Inserted:", data.get("Symbol"))


if __name__ == "__main__":

    load_all_json()

    conn.close()