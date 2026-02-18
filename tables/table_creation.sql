CREATE TABLE symbol (
    s_id SERIAL,
    symbol_id INT PRIMARY KEY,
    company_name VARCHAR(100),
    company_symbol VARCHAR(100),
    sector VARCHAR(100),
    created_on DATE
);


SELECT * FROM symbol;

-- DROP TABLE SYMBOL;

-- CREATE DATABASE stock_db;

-- SELECT current_database();


