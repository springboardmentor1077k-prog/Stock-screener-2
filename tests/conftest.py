import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import os
import sys

# Add project root to path so we can import backend/ modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock redis and psycopg2 before importing the app
import sys
from unittest.mock import MagicMock

# Create mock for redis
mock_redis = MagicMock()
mock_redis_client = MagicMock()
mock_redis.StrictRedis.return_value = mock_redis_client
mock_redis_client.get.return_value = None # Ensure cache miss by default
sys.modules["redis"] = mock_redis

# Create mock for psycopg2
mock_psycopg2 = MagicMock()
mock_conn = MagicMock()
mock_cursor = MagicMock()
mock_pool = MagicMock()
mock_psycopg2.pool.SimpleConnectionPool.return_value = mock_pool
mock_pool.getconn.return_value = mock_conn
mock_conn.cursor.return_value = mock_cursor
mock_cursor.__enter__.return_value = mock_cursor
sys.modules["psycopg2"] = mock_psycopg2
sys.modules["psycopg2.pool"] = mock_psycopg2.pool
sys.modules["psycopg2.extras"] = MagicMock()

# Mock yfinance to prevent internet calls during tests
import yfinance as yf
sys.modules["yfinance"] = MagicMock()

from backend.portfolio_logic import clear_price_cache
from backend.db import clear_results_cache
from backend.main import app

@pytest.fixture(autouse=True)
def setup_mocks():
    """Reset mocks and clear caches before each test to ensure independence."""
    # Reset method return values to prevent MagicMock pollution in caches
    mock_redis_client.get.return_value = None
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    
    # Task 1 Edge Case 2: Ensure internal caches do not bleed across tests
    clear_price_cache()
    clear_results_cache()
    
    return mock_cursor

@pytest.fixture
def client():
    """Returns a FastAPI TestClient for API endpoints testing."""
    return TestClient(app)
