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
