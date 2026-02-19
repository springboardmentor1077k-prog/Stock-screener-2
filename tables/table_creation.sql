CREATE TABLE symbol (
    symbol_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    company_symbol VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100) NOT NULL,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO symbol (company_name, company_symbol, sector)
VALUES
('Reliance Industries Ltd.', 'RELIANCE.NS', 'Energy'),
('Tata Consultancy Services Ltd.', 'TCS.NS', 'Technology');


SELECT * FROM symbol;

DROP TABLE SYMBOL;

SELECT * FROM fundamentals;

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