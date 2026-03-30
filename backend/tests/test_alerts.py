import sqlite3
from backend.api.alerts.alerts_routes import evaluate_condition

def test_alert_trigger():
    conn = sqlite3.connect("backend/database/stock_screener.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    condition = {
        "symbol": "INFY",
        "metric": "current_price",
        "operator": ">",
        "value": 1
    }

    result = evaluate_condition(condition, cursor)
    assert result in [True, False]

    conn.close()