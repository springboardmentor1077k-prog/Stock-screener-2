from app.db import get_connection

def add_to_portfolio(symbol, shares):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO portfolio (symbol, shares) VALUES (%s, %s)",
        (symbol, shares)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_portfolio():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM portfolio")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data