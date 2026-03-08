import sqlite3

conn = sqlite3.connect("stock_screener.db")
cursor = conn.cursor()

# SYMBOLS
cursor.execute("""
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    exchange TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# FUNDAMENTALS
cursor.execute("""
CREATE TABLE fundamentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    pe_ratio REAL,
    peg_ratio REAL,
    debt_fcf REAL,
    ebitda REAL,
    revenue REAL,
    promoter_holding REAL,
    report_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# HISTORICAL METRICS
cursor.execute("""
CREATE TABLE historical_metrics (
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

# USERS
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# PORTFOLIO
cursor.execute("""
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    quantity INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# ALERTS
cursor.execute("""
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    condition_json TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# INSERT SYMBOLS
cursor.executemany("""
INSERT INTO symbols (symbol, company_name, sector, industry, exchange)
VALUES (?, ?, ?, ?, ?)
""", [
    ("INFY", "Infosys Ltd", "IT", "Software", "NSE"),
    ("TCS", "Tata Consultancy Services", "IT", "Software", "NSE"),
    ("HDFCBANK", "HDFC Bank", "Banking", "Financial Services", "NSE")
])

# INSERT FUNDAMENTALS (2 quarters for INFY)
cursor.executemany("""
INSERT INTO fundamentals (company_id, pe_ratio, peg_ratio, debt_fcf, ebitda, revenue, promoter_holding, report_date)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", [
    (1, 22.5, 1.2, 0.5, 15000, 45000, 13.1, "2024-03-31"),
    (1, 21.8, 1.1, 0.4, 15500, 47000, 13.1, "2024-06-30")
])

# INSERT HISTORICAL METRICS
cursor.executemany("""
INSERT INTO historical_metrics (company_id, quarter, revenue, ebitda, net_profit)
VALUES (?, ?, ?, ?, ?)
""", [
    (1, "2024-03-31", 45000, 15000, 6000),
    (1, "2024-06-30", 47000, 15500, 6200)
])

# INSERT USER
cursor.execute("""
INSERT INTO users (name, email, hashed_password)
VALUES (?, ?, ?)
""", ("Keertana", "keertana@email.com", "hashed_password"))

# INSERT PORTFOLIO (2 entries)
cursor.executemany("""
INSERT INTO portfolio (user_id, company_id, quantity)
VALUES (?, ?, ?)
""", [
    (1, 1, 10),
    (1, 2, 5)
])

# INSERT ALERT
cursor.execute("""
INSERT INTO alerts (user_id, condition_json, is_active)
VALUES (?, ?, ?)
""", (1, '{"pe_ratio": "<20", "peg_ratio": "<1"}', 1))

conn.commit()
conn.close()

print("Database created and sample data inserted successfully.")