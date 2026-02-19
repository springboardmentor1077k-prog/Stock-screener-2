-- Create database
CREATE DATABASE IF NOT EXISTS stock_screener;
USE stock_screener;

-- =========================
-- 1. Symbols Table
-- =========================
CREATE TABLE IF NOT EXISTS symbols (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2. Fundamentals Table
-- =========================
CREATE TABLE IF NOT EXISTS fundamentals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    pe_ratio DECIMAL(10,2),
    peg_ratio DECIMAL(10,2),
    debt_fcf DECIMAL(15,2),
    ebitda DECIMAL(15,2),
    revenue DECIMAL(15,2),
    promoter_holding DECIMAL(5,2),
    report_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES symbols(id)
        ON DELETE CASCADE
);

-- =========================
-- 3. Historical Metrics Table
-- =========================
CREATE TABLE IF NOT EXISTS historical_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    quarter DATE NOT NULL,
    revenue DECIMAL(15,2),
    ebitda DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES symbols(id)
        ON DELETE CASCADE
);

-- =========================
-- 4. Users Table
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 5. Portfolio Table
-- =========================
CREATE TABLE IF NOT EXISTS portfolio (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    company_id INT NOT NULL,
    quantity INT DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (company_id) REFERENCES symbols(id)
        ON DELETE CASCADE
);

-- =========================
-- 6. Alerts Table
-- =========================
CREATE TABLE IF NOT EXISTS alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    condition_json JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);
