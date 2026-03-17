import sqlite3

conn = sqlite3.connect("stock_database.db")
cursor = conn.cursor()

# cursor.executescript("""

# CREATE TABLE symbols (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     symbol TEXT NOT NULL UNIQUE,
#     company_name TEXT NOT NULL,
#     sector TEXT,
#     industry TEXT,
#     exchange TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );

# CREATE TABLE users (
#     user_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_name TEXT NOT NULL,
#     user_email TEXT UNIQUE NOT NULL,
#     hashed_password TEXT NOT NULL,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );

# CREATE TABLE fundamentals (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     company_id INTEGER NOT NULL,
#     pe_ratio REAL,
#     peg_ratio REAL,
#     debt_fcf REAL,
#     ebitda REAL,
#     revenue REAL,
#     promoter_holding REAL,
#     report_date DATE NOT NULL,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (company_id) REFERENCES symbols(id)
# );


# CREATE TABLE historic_metrics (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     company_id INTEGER NOT NULL,
#     quarter DATE NOT NULL,
#     revenue REAL,
#     ebitda REAL,
#     net_profit REAL,
#     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (company_id) REFERENCES symbols(company_id)
# );

# CREATE TABLE portfolio (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     company_id INTEGER NOT NULL,
#     quantity INTEGER NOT NULL,
#     added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (user_id) REFERENCES users(user_id),
#     FOREIGN KEY (company_id) REFERENCES symbols(company_id)
# );

# CREATE TABLE alert (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     condition_json JSON,
#     is_active BOOLEAN DEFAULT 1,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (user_id) REFERENCES users(user_id)
# );

# """)
cursor.executescript("""
DROP TABLE historic_metrics;
    CREATE TABLE historic_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    quarter DATE NOT NULL,
    revenue REAL,
    ebitda REAL,
    net_profit REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

conn.commit()
conn.close()

print("Tables created successfully!")
