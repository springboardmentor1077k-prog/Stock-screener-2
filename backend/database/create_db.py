import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "stock_screener.db")

# connect to database (creates file if it does not exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# -----------------------------
# SYMBOLS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    exchange TEXT,
    country TEXT,
    website TEXT,
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
    market_cap REAL,

    revenue REAL,
    revenue_growth REAL,
    ebitda REAL,
    profit_margin REAL,

    total_debt REAL,
    debt_to_equity REAL,

    roe REAL,
    roa REAL,

    eps REAL,
    book_value REAL,
    dividend_yield REAL,

    current_price REAL,      -- ADDED
    price_growth REAL,

    report_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# -----------------------------
# HISTORICAL PRICE DATA
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS historical_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,

    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# -----------------------------
# USERS TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
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
    buy_price REAL,          -- ADDED
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

# -----------------------------
# WATCHLIST TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

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
# SEARCH HISTORY TABLE
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    parsed_dsl TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON search_history(user_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_time ON search_history(created_at)")

# -----------------------------
# COMMUNITY POSTS
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# -----------------------------
# INDEXES (performance improvement)
# -----------------------------
cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_company ON fundamentals(company_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_company ON historical_metrics(company_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_metrics(date)")

conn.commit()
conn.close()

print("Database schema created successfully.")