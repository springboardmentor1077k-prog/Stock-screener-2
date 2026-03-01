import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )