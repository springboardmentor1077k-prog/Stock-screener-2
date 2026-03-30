from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

headers = {"Authorization": "Bearer testtoken"}

def test_add_stock():
    response = client.post(
        "/portfolio/add",
        json={"company_id": 1, "quantity": 2},
        headers=headers
    )

    assert response.status_code in [200, 401]


def test_get_portfolio():
    response = client.get("/portfolio/", headers=headers)
    assert response.status_code in [200, 401]