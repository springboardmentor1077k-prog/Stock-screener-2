CREATE TABLE IF NOT EXISTS symbols (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fundamentals (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15, 2) NOT NULL,
    record_date DATE NOT NULL,
    FOREIGN KEY (company_id) REFERENCES symbols(id) ON DELETE CASCADE
);

-- We also need a simple 'users' table to support the Authentication (JWT) requirement
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
