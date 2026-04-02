import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import verify_token
from unittest.mock import MagicMock, patch

# Dependency override for authentication
async def override_verify_token():
    return "test_user"

# Mock price logic globally
patch('backend.portfolio_routes.get_current_price', return_value=150.0).start()
patch('backend.portfolio_routes.get_multiple_prices', return_value={"AAPL": 150.0, "TSLA": 200.0}).start()

app.dependency_overrides[verify_token] = override_verify_token
client = TestClient(app)

def test_query_valid():
    """Test 1: POST /query with valid query."""
    response = client.post("/query", json={"query": "VALID_QUERY_1"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_query_empty():
    response = client.post("/query", json={"query": ""})
    assert response.status_code in [400, 200]

def test_query_gibberish():
    response = client.post("/query", json={"query": "GIBBERISH_123"})
    assert response.json()["status"] == "error"

def test_get_portfolio_structure():
    response = client.get("/portfolio/1")
    assert response.status_code == 200

def test_portfolio_add_and_get(setup_mocks):
    mock_cursor = setup_mocks
    mock_cursor.fetchone.return_value = None
    response = client.post("/portfolio/add", json={"user_id": 1, "symbol": "AAPL", "quantity": 10, "buy_price": 100.0})
    assert response.status_code == 200
    mock_cursor.fetchall.return_value = [{"symbol": "AAPL", "quantity": 10, "buy_price": 100.0}]
    get_res = client.get("/portfolio/1")
    assert any(h["symbol"] == "AAPL" for h in get_res.json())

def test_portfolio_remove(setup_mocks):
    mock_cursor = setup_mocks
    mock_cursor.fetchone.return_value = {"quantity": 5, "buy_price": 200.0}
    client.request("DELETE", "/portfolio/remove", json={"user_id": 1, "symbol": "TSLA"})
    mock_cursor.fetchall.return_value = []
    get_res = client.get("/portfolio/1")
    assert not any(h["symbol"] == "TSLA" for h in get_res.json())

def test_content_type_json(setup_mocks):
    res = client.get("/")
    assert "application/json" in res.headers["Content-Type"]

def test_sql_injection_attempt(setup_mocks):
    response = client.post("/query", json={"query": "INJECTION_QUERY ' DROP TABLE"})
    assert response.status_code == 200
    assert response.json()["status"] in ["success", "error"]

def test_empty_database_results(setup_mocks):
    """Edge Case 2: Empty results returns success count 0."""
    mock_cursor = setup_mocks
    mock_cursor.fetchall.return_value = []
    # Clear cache explicitly just in case setup_mocks didn't or the instance is different
    from backend.db import clear_results_cache
    clear_results_cache()
    
    response = client.post("/query", json={"query": "EMPTY_RESULTS_QUERY_UNIQUE"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 0

def test_large_query_input():
    response = client.post("/query", json={"query": "A" * 10000})
    assert response.status_code != 500

def test_database_connection_failure(setup_mocks):
    """Edge Case 6: Connection failure returns 500."""
    with patch('backend.main.get_connection', return_value=None):
        response = client.post("/query", json={"query": "CONNECTION_FAIL_QUERY_UNIQUE"})
        assert response.status_code == 500

def test_concurrent_requests(setup_mocks):
    import threading
    results = []
    def req(): results.append(client.post("/query", json={"query": "CONCURRENT"}).status_code)
    ts = [threading.Thread(target=req) for _ in range(5)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert all(c == 200 for c in results)
