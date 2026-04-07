import pytest
from fastapi.testclient import TestClient
from main import app
from schemas import DSLQuery
from compiler import compile_dsl_to_sql

client = TestClient(app)

# 1. DSL Validation Tests
def test_dsl_validation_valid():
    valid_data = {
        "conditions": [{"field": "pe_ratio", "operator": "<", "value": 15}],
        "logic": "AND"
    }
    dsl = DSLQuery(**valid_data)
    assert len(dsl.conditions) == 1
    assert dsl.conditions[0].field == "pe_ratio"

def test_dsl_validation_invalid_field():
    invalid_data = {
        "conditions": [{"field": "invalid_metric", "operator": "<", "value": 15}],
        "logic": "AND"
    }
    with pytest.raises(ValueError):
        DSLQuery(**invalid_data)

# 2. SQL Compiler Tests
def test_sql_compiler():
    dsl_dict = {
        "conditions": [{"field": "pe_ratio", "operator": "<", "value": 15}],
        "logic": "AND"
    }
    query, params = compile_dsl_to_sql(dsl_dict)
    assert "SELECT f.symbol" in query
    assert "pe_ratio < ?" in query
    assert params == [15]

# 3. API Endpoint Tests (Query)
def test_query_api():
    response = client.post("/query", json={"query": "Show companies with pe_ratio < 15"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

# 4. Portfolio API Tests
def test_portfolio_operations():
    # Add to portfolio
    add_res = client.post("/portfolio/add", json={
        "user_id": "user_test", "symbol": "INFY", "quantity": 10, "buy_price": 1500
    })
    assert add_res.status_code == 200
    
    # Get portfolio
    get_res = client.get("/portfolio/user_test")
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) > 0

# 5. Alerts Evaluation Test
def test_alerts_check():
    # Setup alert
    client.post("/alert/add", json={
        "user_id": "user_test", "symbol": "INFY", "field": "pe_ratio", "operator": "<", "value": 100, "alert_type": "metric"
    })
    # Check alert
    check_res = client.get("/alerts/check/user_test")
    assert check_res.status_code == 200
    assert "triggered" in check_res.json()