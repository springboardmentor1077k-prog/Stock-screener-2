CREATE TABLE stocks (
 id SERIAL PRIMARY KEY,
 symbol VARCHAR(10),
 name TEXT,
 sector TEXT,
 pe_ratio FLOAT,
 market_cap BIGINT,
 price FLOAT,
 volume BIGINT
);