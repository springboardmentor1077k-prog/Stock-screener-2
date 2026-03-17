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


def insert_quarterly(symbol, reports):

    company_id = get_company_id(symbol)

    if not company_id:
        return

    for report in reports:

        quarter = report.get("fiscalDateEnding")
        revenue = report.get("totalRevenue")
        ebitda = report.get("ebitda")
        net_profit = report.get("netIncome")

        cursor.execute("""
            INSERT INTO historic_metrics
            (company_id, quarter, revenue, ebitda, net_profit)
            VALUES (?, ?, ?, ?, ?)
        """, (company_id, quarter, revenue, ebitda, net_profit))

    conn.commit()


def load_data():

    for file in os.listdir(DATA_FOLDER):

        if file.endswith("_income.json"):

            path = os.path.join(DATA_FOLDER, file)

            with open(path) as f:
                data = json.load(f)

            symbol = file.split("_")[0]

            reports = data.get("quarterlyReports", [])

            insert_quarterly(symbol, reports)

            print("Inserted historic data:", symbol)


if __name__ == "__main__":

    load_data()

    conn.close()