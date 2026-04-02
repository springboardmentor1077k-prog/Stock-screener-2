# Database/create_alerts_table.py
import sqlite3
import os

# Database path (adjust if needed)
DB_PATH = "stock_database.db"

def create_alerts_table():
    """Create enhanced alerts table with all features"""
    
    print("=" * 60)
    print("CREATING ENHANCED ALERTS TABLE")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if old alerts table exists and backup if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alert'")
        old_table_exists = cursor.fetchone()
        
        if old_table_exists:
            cursor.execute("SELECT COUNT(*) FROM alert")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"\n⚠️  Found {count} existing alerts. Creating backup...")
                cursor.execute("CREATE TABLE IF NOT EXISTS alert_backup AS SELECT * FROM alert")
                print(f"✅ Backed up {count} alerts to 'alert_backup' table")
            
            print("\n📌 Dropping old alerts table...")
            cursor.execute("DROP TABLE IF EXISTS alert")
        
        # Create enhanced alerts table
        print("\n📌 Creating enhanced alerts table...")
        
        cursor.execute("""
            CREATE TABLE alert (
                -- Primary key
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- User association
                user_id INTEGER NOT NULL,
                
                -- Alert identification
                alert_name TEXT NOT NULL,
                alert_type TEXT NOT NULL CHECK (alert_type IN ('price', 'growth', 'screener', 'portfolio')),
                
                -- Stock identification
                symbol TEXT,
                company_id INTEGER,
                
                -- Alert conditions (for price and growth alerts)
                condition_field TEXT,
                condition_operator TEXT CHECK (condition_operator IN ('>', '<', '>=', '<=', '==', '!=')),
                condition_value REAL,
                
                -- For screener-based alerts (store entire DSL query)
                screener_dsl TEXT,  -- JSON stored as TEXT
                
                -- Alert behavior settings
                is_active BOOLEAN DEFAULT 1,
                frequency TEXT DEFAULT 'once' CHECK (frequency IN ('once', 'daily', 'hourly')),
                
                -- Tracking fields
                last_triggered TIMESTAMP,
                trigger_count INTEGER DEFAULT 0,
                
                -- Notification settings
                notification_method TEXT DEFAULT 'email' CHECK (notification_method IN ('email', 'webhook', 'push')),
                notification_sent BOOLEAN DEFAULT 0,
                
                -- Additional info
                notes TEXT,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Foreign keys
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (company_id) REFERENCES symbols(id)
            )
        """)
        
        # Create indexes for better performance
        print("\n📌 Creating indexes...")
        
        cursor.execute("CREATE INDEX idx_alert_user_id ON alert(user_id)")
        cursor.execute("CREATE INDEX idx_alert_symbol ON alert(symbol)")
        cursor.execute("CREATE INDEX idx_alert_is_active ON alert(is_active)")
        cursor.execute("CREATE INDEX idx_alert_type ON alert(alert_type)")
        cursor.execute("CREATE INDEX idx_alert_created_at ON alert(created_at)")
        
        # Create trigger to automatically update 'updated_at' timestamp
        print("\n📌 Creating update trigger...")
        
        cursor.execute("""
            CREATE TRIGGER update_alert_timestamp 
            AFTER UPDATE ON alert
            BEGIN
                UPDATE alert SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        # Insert sample alerts for testing
        print("\n📌 Inserting sample alerts for testing...")
        
        # Get demo user_id
        cursor.execute("SELECT user_id FROM users LIMIT 1")
        demo_user = cursor.fetchone()
        
        if demo_user:
            user_id = demo_user[0]
            
            # Sample price alert
            cursor.execute("""
                INSERT INTO alert (
                    user_id, alert_name, alert_type, symbol, 
                    condition_field, condition_operator, condition_value,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "AAPL Price Alert",
                "price",
                "AAPL",
                "current_price",
                ">",
                200.00,
                "Alert when Apple stock goes above $200"
            ))
            
            # Sample growth alert
            cursor.execute("""
                INSERT INTO alert (
                    user_id, alert_name, alert_type, symbol,
                    condition_field, condition_operator, condition_value,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "NVDA Growth Alert",
                "growth",
                "NVDA",
                "revenue_growth",
                ">",
                50.00,
                "Alert when NVIDIA growth exceeds 50%"
            ))
            
            # Sample low price alert
            cursor.execute("""
                INSERT INTO alert (
                    user_id, alert_name, alert_type, symbol,
                    condition_field, condition_operator, condition_value,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                "TSLA Dip Alert",
                "price",
                "TSLA",
                "current_price",
                "<",
                200.00,
                "Alert when Tesla drops below $200"
            ))
            
            print("✅ Added 3 sample alerts for testing")
        
        conn.commit()
        
        # Verify table creation
        print("\n📌 Verifying table creation...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alert'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Alerts table created successfully!")
            
            # Show table schema
            cursor.execute("PRAGMA table_info(alert)")
            columns = cursor.fetchall()
            print(f"\n📊 Table structure: {len(columns)} columns")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM alert")
            count = cursor.fetchone()[0]
            print(f"📊 Records in table: {count}")
            
        else:
            print("❌ Failed to create alerts table")
        
        print("\n" + "=" * 60)
        print("✅ ALERTS TABLE SETUP COMPLETE!")
        print("=" * 60)
        
        # Show sample data if available
        cursor.execute("SELECT id, alert_name, alert_type, symbol, is_active FROM alert LIMIT 3")
        sample_alerts = cursor.fetchall()
        
        if sample_alerts:
            print("\n📋 Sample alerts:")
            for alert in sample_alerts:
                print(f"   ID: {alert[0]}, Name: {alert[1]}, Type: {alert[2]}, Symbol: {alert[3]}, Active: {alert[4]}")
        
    except Exception as e:
        print(f"\n❌ Error creating alerts table: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n🔒 Database connection closed")

def verify_alerts_table():
    """Verify the alerts table structure"""
    
    print("\n" + "=" * 60)
    print("VERIFYING ALERTS TABLE")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alert'")
        if not cursor.fetchone():
            print("❌ Alerts table does not exist!")
            return
        
        # Get table info
        cursor.execute("PRAGMA table_info(alert)")
        columns = cursor.fetchall()
        
        print("\n✅ Table Structure:")
        for col in columns:
            print(f"   • {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='alert'")
        indexes = cursor.fetchall()
        
        print("\n✅ Indexes:")
        for idx in indexes:
            print(f"   • {idx[0]}")
        
        # Count alerts by type
        cursor.execute("""
            SELECT alert_type, COUNT(*) 
            FROM alert 
            GROUP BY alert_type
        """)
        counts = cursor.fetchall()
        
        if counts:
            print("\n✅ Alert counts by type:")
            for count in counts:
                print(f"   • {count[0]}: {count[1]} alerts")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Create the alerts table
    create_alerts_table()
    
    # Verify the table structure
    verify_alerts_table()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("=" * 60)
    print("1. Run: uvicorn app.main:app --reload")
    print("2. Test alerts API endpoints")
    print("3. Create alerts via POST /api/v1/alerts/price")
    print("4. Check alerts via GET /api/v1/alerts/?user_id=1")
    print("=" * 60)