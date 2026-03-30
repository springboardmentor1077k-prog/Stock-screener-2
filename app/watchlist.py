from app.db import get_connection

def add_to_watchlist(symbol):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO watchlist (symbol) VALUES (%s)",
        (symbol,)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_watchlist():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM watchlist")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data