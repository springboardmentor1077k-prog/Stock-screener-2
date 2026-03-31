CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fundamentals (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    pe_ratio DECIMAL(10, 2),
    revenue DECIMAL(15, 2),
    ebitda DECIMAL(15, 2),
    debt_to_equity DECIMAL(10, 2),
    reported_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES symbols(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15, 2) NOT NULL,
    record_date DATE NOT NULL,
    FOREIGN KEY (company_id) REFERENCES symbols(id) ON DELETE CASCADE
);

-- We also need a simple 'users' table to support the Authentication (JWT) requirement
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The immutable ledger of all buys/sells
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(15, 2) NOT NULL,
    realized_pnl DECIMAL(15, 2), -- Null for buys, calculated for sells
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fast lookup indexes for transactions
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);

-- The current snapshot of holdings (Authoritative State)
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    buy_price DECIMAL(15, 2) NOT NULL, -- Average purchase price
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

-- Fast lookup indexes for portfolio
CREATE INDEX idx_portfolio_user ON portfolio(user_id);
CREATE INDEX idx_portfolio_symbol ON portfolio(symbol);

-- ==========================================
-- Task 1: PERFORMANCE INDEXES
-- ==========================================

-- Index on fundamentals.company_id for fast joins between symbols and fundamentals
CREATE INDEX IF NOT EXISTS idx_fundamentals_company ON fundamentals(company_id);

-- Index on fundamentals.pe_ratio since it is queried most often for filtering
CREATE INDEX IF NOT EXISTS idx_fundamentals_pe ON fundamentals(pe_ratio);

-- Index on historical_metrics.company_id for fast left join performance
CREATE INDEX IF NOT EXISTS idx_historical_company ON historical_metrics(company_id);

-- Index on historical_metrics.quarter since time filter queries use it heavily
CREATE INDEX IF NOT EXISTS idx_historical_quarter ON historical_metrics(quarter);

-- Index on portfolio.user_id so portfolio lookups are instant
-- (Note: idx_portfolio_user already handles portfolio user_id lookup above, ensuring instant lookup)
CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id);

-- Index on symbols.symbol since every query looks up by symbol or uses it for linking
CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol);

-- Composite index on historical_metrics(company_id, quarter) since they are always used together in joins
CREATE INDEX IF NOT EXISTS idx_historical_company_quarter ON historical_metrics(company_id, quarter);

-- ==========================================
-- Bottleneck 2: Hourly Pre-computed Query Cache
-- ==========================================
CREATE TABLE IF NOT EXISTS screener_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(100) UNIQUE NOT NULL,
    data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
