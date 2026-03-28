CREATE TABLE symbol (
    symbol_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    company_symbol VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE symbol
ALTER COLUMN symbol_id
SET DEFAULT nextval('symbol_symbol_id_seq');



-- DROP TABLE historical_metrics;
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


UPDATE fundamentals f
SET
    ebitda = h.ebitda,
    debt_free_cash = h.debt_free_cash
FROM historical_metrics h
WHERE
    f.symbol_id = h.symbol_id
AND h.reported_date = (
    SELECT MAX(reported_date)
    FROM historical_metrics
    WHERE symbol_id = f.symbol_id
);


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


ALTER TABLE portfolio
ADD COLUMN buy_price NUMERIC NOT NULL;


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






SELECT * FROM symbol;
SELECT * FROM fundamentals;
SELECT * FROM historical_metrics;
SELECT * FROM users;
SELECT * FROM portfolio;
SELECT * FROM alerts;

TRUNCATE Table portfolio;



CREATE TABLE company_details (
    symbol_id INT PRIMARY KEY,
    description TEXT,
    founded_year INT,
    company_type VARCHAR(50),  
    market_cap BIGINT,

    FOREIGN KEY (symbol_id)
    REFERENCES symbol(symbol_id)
    ON DELETE CASCADE
);




TRUNCATE company_details;

-- fundamentals unique


CREATE TABLE alert_master (
    alert_id SERIAL PRIMARY KEY,

    company_id INT,            
    metric VARCHAR(50),
    operator VARCHAR(5),
    target_value FLOAT,

    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (company_id, metric, operator, target_value)
);


CREATE TABLE user_alerts (
    id SERIAL PRIMARY KEY,

    user_id INT,
    alert_id INT,

    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (alert_id) REFERENCES alert_master(alert_id) ON DELETE CASCADE,

    UNIQUE (user_id, alert_id)
);
ALTER TABLE alerts
ADD COLUMN metric VARCHAR(50),
ADD COLUMN operator VARCHAR(5),
ADD COLUMN target_value FLOAT;

ALTER TABLE alerts
ALTER COLUMN company_id DROP NOT NULL;



UPDATE fundamentals
SET pe = 5
WHERE symbol_id = (
    SELECT symbol_id 
    FROM symbol 
    WHERE company_symbol = 'TCS.NS'
);


ALTER TABLE user_alerts
ADD CONSTRAINT unique_user_alert UNIQUE (user_id, alert_id);