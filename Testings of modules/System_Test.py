import pytest
import requests


AUTH_URL = "http://127.0.0.1:8000"
QUERY_URL = "http://127.0.0.1:9000"
APP_URL = "http://127.0.0.1:7000"


# TEST USER (must exist)

TEST_USER = {
    "email": "2005ghosh@gmail.com",
    "password": "123456789@"
}


# FIXTURE: LOGIN → GET TOKEN

@pytest.fixture(scope="session")
def auth_token():
    res = requests.post(
        f"{AUTH_URL}/login",
        json=TEST_USER
    )

    assert res.status_code == 200, "Login failed"

    data = res.json()
    token = data.get("access_token")

    assert token is not None, "Token not received"

    return token



# 1. QUERY API (9000)

def test_query_api():
    res = requests.post(
        f"{QUERY_URL}/query",
        json={"nl_query": "show companies with pe < 20"}
    )

    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "success"
    assert "data" in data



# 2. CACHE TEST (IMPORTANT)

def test_query_cache():
    payload = {"nl_query": "show companies with pe < 20"}

    res1 = requests.post(f"{QUERY_URL}/query", json=payload)
    res2 = requests.post(f"{QUERY_URL}/query", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200

    assert res2.json().get("source") == "cache"



# 3. GET PORTFOLIO (7000)

def test_get_portfolio(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    res = requests.get(
        f"{APP_URL}/get-portfolio",
        headers=headers
    )

    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "success"



# 4. BUY STOCK

def test_buy_stock(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    res = requests.post(
        f"{APP_URL}/buy-stock",
        json={
            "symbol": "INFY",
            "quantity": 1,
            "buy_price": 1500
        },
        headers=headers
    )

    assert res.status_code == 200



# 5. ADD ALERT

def test_add_alert(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    res = requests.post(
        f"{APP_URL}/add-alert",
        json={"query": "pe < 20"},
        headers=headers
    )

    assert res.status_code == 200



# 6. CHECK ALERTS

def test_check_alerts(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    res = requests.get(
        f"{APP_URL}/check-alerts",
        headers=headers
    )

    assert res.status_code == 200

    data = res.json()
    assert "alerts" in data



# 7. SECURITY TEST (NO TOKEN)

def test_unauthorized_access():
    res = requests.get(f"{APP_URL}/get-portfolio")
    assert res.status_code in [401, 403]



# 8. INVALID QUERY TEST

def test_invalid_query():
    res = requests.post(
        f"{QUERY_URL}/query",
        json={"nl_query": "asdasd nonsense"}
    )

    assert res.status_code in [400, 422]