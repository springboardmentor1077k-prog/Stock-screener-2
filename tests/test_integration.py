import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_full_query_pipeline_integration(setup_mocks):
    """Integration Test 1: Full query pipeline works end to end."""
    mock_cursor = setup_mocks
    
    # Mock return for query execution
    mock_cursor.fetchall.return_value = [{"symbol": "AAPL", "company_name": "Apple Inc.", "pe_ratio": 12.5}]
    
    # Send natural language query
    nl_query = "show me stocks with PE ratio less than 15"
    response = client.post("/query", json={"query": nl_query})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["results"][0]["symbol"] == "AAPL"
    assert data["results"][0]["pe_ratio"] == 12.5

def test_portfolio_add_and_fetch_integration(setup_mocks):
    """Integration Test 2: Portfolio add then fetch works end to end."""
    mock_cursor = setup_mocks
    
    # Mock initial empty check
    mock_cursor.fetchone.return_value = None
    
    # 1. Add entry
    payload = {"user_id": 1, "symbol": "MSFT", "quantity": 5, "buy_price": 300.0}
    add_response = client.post("/portfolio/add", json=payload)
    assert add_response.status_code == 200
    
    # 2. Fetch entry
    mock_cursor.fetchall.return_value = [{"symbol": "MSFT", "quantity": 5, "buy_price": 300.0}]
    # We also mock prices to ensure no internet calls
    with patch('backend.portfolio_routes.get_multiple_prices', return_value={"MSFT": 310.0}):
        fetch_response = client.get("/portfolio/1")
        assert fetch_response.status_code == 200
        data = fetch_response.json()
        assert any(h["symbol"] == "MSFT" for h in data)
        assert data[0]["current_price"] == 310.0

def test_quarter_filter_integration():
    """Integration Test 3: Quarter filter integration."""
    from backend.compiler import compile_sql_from_dsl
    
    dsl = {
        "where": { "conditions": [{"field": "pe_ratio", "operator": "<", "value": 15}], "logic": "AND" },
        "time_filter": { "type": "last_m_quarters", "value": 4 }
    }
    
    sql, params = compile_sql_from_dsl(dsl)
    
    # Check for historical_metrics JOIN (Left Join in our current implementation)
    assert "LEFT JOIN historical_metrics h" in sql
    # Check for quarter grouping or limit related components
    assert "h.quarter" in sql
    # Check params include the value 12 (4 * 3)
    assert 12 in params
