import psycopg2
from psycopg2.extras import RealDictCursor

def execute_query(sql_query):

    conn = psycopg2.connect(
        host="localhost",
        database="stocks_db",
        user="postgres",
        password="Taekookilu"
    )

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(sql_query)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows
