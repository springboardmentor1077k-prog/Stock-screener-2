from app.db import get_connection

def add_alert(symbol, condition, threshold):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO alerts (symbol, condition, threshold) VALUES (%s, %s, %s)",
        (symbol, condition, threshold)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_alerts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts")
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data