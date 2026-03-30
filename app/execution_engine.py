# app/execution_engine.py

from app.db import get_connection

def execute_query(query, values):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query, values)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows