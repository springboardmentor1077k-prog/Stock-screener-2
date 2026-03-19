import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


def clean_number(val):
    try:
        if val is None:
            return 0.0

        val = str(val).lower().strip()

        if val in ["", "nan", "none"]:
            return 0.0

        # remove commas and non-numeric chars
        val = re.sub(r"[^\d.\-]", "", val)

        return float(val) if val else 0.0

    except:
        return 0.0


def migrate_table(conn, table_name, numeric_columns):
    cursor = conn.cursor()

    print(f"\n🚀 Migrating table: {table_name}")

    # get all columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()

    columns = [col[1] for col in columns_info]

    # create new table schema
    new_columns = []
    for col in columns_info:
        col_name = col[1]

        if col_name in numeric_columns:
            new_columns.append(f"{col_name} REAL")
        else:
            new_columns.append(f"{col_name} TEXT")

    new_table = f"{table_name}_new"

    cursor.execute(f"DROP TABLE IF EXISTS {new_table}")

    cursor.execute(f"""
        CREATE TABLE {new_table} (
            {", ".join(new_columns)}
        )
    """)

    # fetch old data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # clean + insert
    cleaned_rows = []

    for row in rows:
        new_row = []

        for col_name, value in zip(columns, row):
            if col_name in numeric_columns:
                new_row.append(clean_number(value))
            else:
                new_row.append(value)

        cleaned_rows.append(tuple(new_row))

    placeholders = ", ".join(["?"] * len(columns))

    cursor.executemany(
        f"INSERT INTO {new_table} VALUES ({placeholders})",
        cleaned_rows
    )

    # replace old table
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {new_table} RENAME TO {table_name}")

    conn.commit()

    print(f"✅ {table_name} migrated successfully!")


def main():
    if not os.path.exists(DB_PATH):
        print("❌ Database not found")
        return

    conn = sqlite3.connect(DB_PATH)

    # 🎯 UPDATE THESE BASED ON YOUR DB
    migrate_table(conn, "fundamentals", [
        "pe_ratio",
        "market_cap",
        "revenue",
        "ebitda",
        "profit_margin"
    ])

    # if you want growth table also
    # migrate_table(conn, "historical_metrics", ["close"])

    conn.close()

    print("\n🎉 DATABASE FIXED SUCCESSFULLY!")


if __name__ == "__main__":
    main()