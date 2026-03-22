import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_stock_screener")

def setup_database():
    try:
        print(f"Connecting to MySQL server at {DB_HOST} with user '{DB_USER}'...")
        
        # Connect to MySQL Server (Without specifying a database first)
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create the Database if it doesn't exist yet
        print(f"Creating database '{DB_NAME}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        
        # Switch our connection specifically to the new database
        cursor.execute(f"USE {DB_NAME}")
        
        # Read our schema file structure
        with open("database/schema.sql", "r") as f:
            sql_file = f.read()
            
        # Execute each individual layout chunk separated by semicolons
        sql_commands = [cmd for cmd in sql_file.split(";") if cmd.strip() != ""]
        
        for command in sql_commands:
            cursor.execute(command)
        
        conn.commit()
        print("✅ Success! Database and all Tables were perfectly created!")
        
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to Database: {err}")
        print("Please check your .env file and make sure your MySQL is running and password is correct.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
