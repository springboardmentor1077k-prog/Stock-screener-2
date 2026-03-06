import sqlite3
import json
import os

def create_database():
    # Get the absolute path of the current directory to locate files correctly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'stock_data.json')
    db_path = os.path.join(current_dir, 'stocks.db')
    
    # 1. Read the stock data from the JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # 2. Connect to the SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 3. Create the fundamentals table as per the schema design
    cursor.execute('DROP TABLE IF EXISTS fundamentals')
    cursor.execute('''
        CREATE TABLE fundamentals (
            symbol TEXT PRIMARY KEY,
            pe_ratio REAL,
            market_cap REAL
        )
    ''')
    
    # 4. Extract data from the JSON structure
    symbol = data['ticker']
    pe_ratio = data['fundamentals']['pe_ratio']
    market_cap = data['fundamentals']['market_cap']
    
    # 5. Insert the data into the fundamentals table using parameterized query
    cursor.execute('INSERT INTO fundamentals (symbol, pe_ratio, market_cap) VALUES (?, ?, ?)', 
                   (symbol, pe_ratio, market_cap))
    
    conn.commit()
    conn.close()
    
    # Professional success message
    print("Database 'stocks.db' initialized and populated successfully.")

if __name__ == '__main__':
    create_database()