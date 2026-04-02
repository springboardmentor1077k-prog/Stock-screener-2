# Database/create_portfolio_tables.py
import sqlite3
import os

# Get the correct path (adjust if needed)
DB_PATH = os.path.join(os.path.dirname(__file__), "stock_database.db")

def create_portfolio_tables():
    """Create enhanced portfolio tables"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Drop old portfolio table if exists
        cursor.execute("DROP TABLE IF EXISTS portfolio")
        
        # Create enhanced portfolio table
        cursor.execute("""
            CREATE TABLE portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                average_price REAL NOT NULL CHECK (average_price >= 0),
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (company_id) REFERENCES symbols(id),
                UNIQUE(user_id, company_id)
            )
        """)
        
        # Create transaction history table
        cursor.execute("""
            CREATE TABLE portfolio_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolio(id) ON DELETE CASCADE
            )
        """)
        
        # Create performance snapshots table
        cursor.execute("""
            CREATE TABLE portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_investment REAL,
                total_current_value REAL,
                total_profit_loss REAL,
                profit_loss_percentage REAL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create watchlist table
        cursor.execute("""
            CREATE TABLE watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_price REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (company_id) REFERENCES symbols(id),
                UNIQUE(user_id, company_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_id ON portfolio_transactions(portfolio_id)")
        
        conn.commit()
        print("✅ Portfolio tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_portfolio_tables()