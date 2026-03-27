from database import get_connection

def add_alert(alert):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (user_id, stock_symbol, condition_type, target_price)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (alert.user_id, alert.stock_symbol, alert.condition_type, alert.target_price))

    alert_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()

    return alert_id


def get_alerts(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts WHERE user_id = %s;", (user_id,))
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def delete_alert(alert_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alerts WHERE id = %s;", (alert_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return True


def check_alerts(current_prices):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts;")
    alerts = cursor.fetchall()

    triggered = []

    for alert in alerts:
        _, user_id, symbol, condition, target, _ = alert

        if symbol in current_prices:
            price = current_prices[symbol]

            if condition == "ABOVE" and price > target:
                triggered.append(alert)

            elif condition == "BELOW" and price < target:
                triggered.append(alert)

    cursor.close()
    conn.close()

    return triggered