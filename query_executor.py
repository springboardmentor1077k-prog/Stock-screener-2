from database import get_connection


def execute_query(sql, params):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(sql, params)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows