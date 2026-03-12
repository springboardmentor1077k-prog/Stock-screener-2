import sqlite3

# connect to database (creates file if it does not exist)
conn = sqlite3.connect("stock_screener.db")
cursor = conn.cursor()

# -----------------------------
# SYMBOLS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    exchange TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# -----------------------------
# FUNDAMENTALS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS fundamentals (
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

# -----------------------------
# HISTORICAL METRICS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS historical_metrics (
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

# -----------------------------
# USERS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# -----------------------------
# PORTFOLIO TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    quantity INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# -----------------------------
# ALERTS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    condition_json TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# -----------------------------
# INDEXES (performance improvement)
# -----------------------------
cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_company ON fundamentals(company_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_company ON historical_metrics(company_id)")

# -----------------------------
# Insert demo user
# -----------------------------
cursor.execute("""
INSERT OR IGNORE INTO users (name, email, hashed_password)
VALUES (?, ?, ?)
""", ("Keertana", "keertana@email.com", "hashed_password"))

conn.commit()
conn.close()

print("Database schema created successfully.")