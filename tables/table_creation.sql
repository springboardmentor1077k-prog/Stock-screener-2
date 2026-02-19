CREATE TABLE symbol (
    symbol_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    company_symbol VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);





DROP TABLE SYMBOL;



-- CREATE DATABASE stock_db;

-- SELECT current_database();


CREATE TABLE fundamentals (
    fundamental_id SERIAL PRIMARY KEY,
    symbol_id INT NOT NULL,
    pe FLOAT NOT NULL,
    peg FLOAT NOT NULL,
    promoter_holding DECIMAL(5,2) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (symbol_id)
        REFERENCES symbol(symbol_id)
        ON DELETE CASCADE
);



CREATE TABLE historical_metrics (
    metric_id SERIAL PRIMARY KEY,
    
    company_id INT NOT NULL,
    
    revenue_quarter DECIMAL(15,2) NOT NULL,
    pe DECIMAL(10,2),
    peg DECIMAL(10,2),
    promoter_holding DECIMAL(5,2),
    
    quarter_label VARCHAR(20) NOT NULL,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id)
        REFERENCES symbol(symbol_id)
        ON DELETE CASCADE
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


INSERT INTO historical_metrics
(company_id, revenue_quarter, pe, peg, promoter_holding, quarter_label)
VALUES
(1, 56000.00, 28.50, 1.40, 54.30, 'Q1-2025'),
(2, 92000.00, 24.10, 1.10, 50.20, 'Q1-2025');



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



SELECT * FROM symbol;
SELECT * FROM fundamentals;
SELECT * FROM historical_metrics;
SELECT * FROM users;
SELECT * FROM portfolio;
SELECT * FROM alerts;