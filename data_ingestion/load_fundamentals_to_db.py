import sqlite3
import json
import os

DB_PATH = "../Database/stock_database.db"
DATA_FOLDER = "raw"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def get_company_id(symbol):

    cursor.execute(
        "SELECT id FROM symbols WHERE symbol=?",
        (symbol,)
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None


def insert_fundamentals(data):

    symbol = data.get("Symbol")
    company_id = get_company_id(symbol)

    if not company_id:
        print("Company not found:", symbol)
        return

    pe = data.get("PERatio")
    peg = data.get("PEGRatio")
    ebitda = data.get("EBITDA")
    revenue = data.get("RevenueTTM")
    report_date = data.get("LatestQuarter")

    cursor.execute("""
        INSERT INTO fundamentals
        (company_id, pe_ratio, peg_ratio, ebitda, revenue, report_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (company_id, pe, peg, ebitda, revenue, report_date))

    conn.commit()


def load_data():

    for file in os.listdir(DATA_FOLDER):

        if file.endswith("_overview.json"):

            path = os.path.join(DATA_FOLDER, file)

            with open(path) as f:
                data = json.load(f)

            insert_fundamentals(data)

            print("Inserted fundamentals:", data.get("Symbol"))


if __name__ == "__main__":

    load_data()

    conn.close()