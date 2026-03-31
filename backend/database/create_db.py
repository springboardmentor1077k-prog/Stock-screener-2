import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "stock_screener.db")

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

    current_price REAL,
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
# PRICE GROWTH TABLE (PRECOMPUTED)
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS price_growth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    date DATE NOT NULL,
    price_growth REAL,
    FOREIGN KEY (company_id) REFERENCES symbols(id)
);
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_price_growth_company_date
ON price_growth(company_id, date);
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
    buy_price REAL,
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
    UNIQUE(user_id, company_id),
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
    triggered_message TEXT,
    triggered_at TIMESTAMP,
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
# BASIC INDEXES
# -----------------------------
cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_sector ON symbols(sector)")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_company ON fundamentals(company_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_pe ON fundamentals(pe_ratio)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_marketcap ON fundamentals(market_cap)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_revenue ON fundamentals(revenue)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_profitmargin ON fundamentals(profit_margin)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_ebitda ON fundamentals(ebitda)")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_company ON historical_metrics(company_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_metrics(date)")

# -----------------------------
# COMPOSITE INDEXES (VERY IMPORTANT)
# -----------------------------
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_hist_company_date_close
ON historical_metrics(company_id, date, close)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_symbols_sector_id
ON symbols(sector, id)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_fundamentals_sort
ON fundamentals(market_cap DESC, pe_ratio ASC)
""")
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_fundamentals_company_pe
ON fundamentals(company_id, pe_ratio);
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_fundamentals_company_marketcap
ON fundamentals(company_id, market_cap);
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_price_growth_latest
ON price_growth(company_id, date DESC);
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_price_growth_company_date
ON price_growth(company_id, date);
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_price_growth_company_date_desc
ON price_growth(company_id, date DESC);
""")

conn.commit()
conn.close()

print("Database schema created successfully with optimization indexes.")