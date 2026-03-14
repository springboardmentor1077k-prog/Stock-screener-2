from app.db import get_connection


def execute_query(sql, values):
    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(sql, values)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results