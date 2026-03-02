CREATE TABLE symbol (
    symbol_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    company_symbol VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);





DROP TABLE historical_metrics;



-- CREATE DATABASE stock_db;

-- SELECT current_database();


CREATE TABLE fundamentals (
    fundamental_id SERIAL PRIMARY KEY,
    symbol_id INT NOT NULL,
    pe DECIMAL(10,2),
    peg DECIMAL(10,2),
    promoter_holding DECIMAL(5,2) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (symbol_id)
        REFERENCES symbol(symbol_id)
        ON DELETE CASCADE
);

ALTER TABLE fundamentals
ADD CONSTRAINT pe_range_check
CHECK (pe >= 0 AND pe <= 1000),

ADD CONSTRAINT peg_range_check
CHECK (peg >= 0 AND peg <= 50),

ADD CONSTRAINT ebitda_not_null_check
CHECK (ebitda IS NOT NULL),

ADD CONSTRAINT debt_free_cash_not_null_check
CHECK (debt_free_cash IS NOT NULL),

ADD CONSTRAINT promoter_range_check
CHECK (promoter_holding BETWEEN 0 AND 100);


CREATE TABLE historical_metrics (
    series_id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbol(symbol_id),

    financial_year INTEGER NOT NULL,
    quarter SMALLINT NOT NULL CHECK (quarter BETWEEN 1 AND 4),

    revenue NUMERIC,
    ebitda NUMERIC,
    net_profit NUMERIC,
    debt_free_cash NUMERIC,
    pe NUMERIC,

    reported_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol_id, financial_year, quarter)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    
    email VARCHAR(150) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    hashed_password TEXT NOT NULL,
    
    date_of_join TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE portfolio (
    p_id SERIAL PRIMARY KEY,
    
    user_id INT NOT NULL,
    company_id INT NOT NULL,
    
    quantity INT NOT NULL CHECK (quantity > 0),
    
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
        
    FOREIGN KEY (company_id)
        REFERENCES symbol(symbol_id)
        ON DELETE CASCADE,
        
    CONSTRAINT unique_user_stock
        UNIQUE (user_id, company_id)
);


CREATE TABLE alerts (
    a_id SERIAL PRIMARY KEY,
    
    user_id INT NOT NULL,
    company_id INT NOT NULL,
    
    alert_condition VARCHAR(255) NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
        
    FOREIGN KEY (company_id)
        REFERENCES symbol(symbol_id)
        ON DELETE CASCADE
);




INSERT INTO symbol (company_name, company_symbol, sector)
VALUES
('Reliance Industries Ltd.', 'RELIANCE.NS', 'Energy'),
('Tata Consultancy Services Ltd.', 'TCS.NS', 'Technology');




INSERT INTO users
(email, name, hashed_password)
VALUES
('apurba@gmail.com', 'Apurba Mukherjee', 'fjeiof#4342'),
('gem@gmail.com', 'Raj', 'jsgjiojew454');


INSERT INTO portfolio
(user_id, company_id, quantity)
VALUES
(1, 1, 10),
(1, 2, 5);



INSERT INTO alerts
(user_id, company_id, alert_condition)
VALUES
(1, 1, 'PE > 30'),
(1, 2, 'PEG < 1');

INSERT INTO historical_metrics
(symbol_id, financial_year, quarter, revenue, ebitda, net_profit, debt_free_cash, pe, reported_date)
VALUES
(1, 2025, 1, 50000000000, 10000000000, 7000000000, 2000000000, 18.5, '2025-03-31'),

(1, 2025, 2, 52000000000, 11000000000, 7500000000, 2200000000, 19.0, '2025-06-30'),

(1, 2025, 3, 54000000000, 12500000000, 8200000000, 2400000000, 20.5, '2025-09-30'),

(1, 2025, 4, 56000000000, 14000000000, 9000000000, 2600000000, 22.0, '2025-12-31');



INSERT INTO fundamentals
(symbol_id, pe, peg, promoter_holding, ebitda, debt_free_cash)
VALUES
(1, 19.80, 1.25, 45.60, 18000000000.00, 4200000000.00),
(2, 27.10, 1.40, 72.30, 22000000000.00, 6000000000.00);



SELECT * FROM symbol;
SELECT * FROM fundamentals;
SELECT * FROM historical_metrics;
SELECT * FROM users;
SELECT * FROM portfolio;
SELECT * FROM alerts;

TRUNCATE Table historical_metrics;