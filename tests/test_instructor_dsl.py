import pytest
import sys
import os

# Add parent to path for relative importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.instructor_dsl_parser import generate_sql

def test_generate_sql_simple_condition():
    sql, params = generate_sql('PE ratio < 15')
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE f.pe_ratio < %s"
    assert sql == expected_sql
    assert params == [15]

def test_generate_sql_multiple_conditions_and():
    sql, params = generate_sql('PE ratio < 15 AND revenue > 1000000')
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE f.pe_ratio < %s AND f.revenue > %s"
    assert sql == expected_sql
    assert params == [15, 1000000]

def test_generate_sql_multiple_conditions_or():
    sql, params = generate_sql('sector == "Tech" OR price <= 50.5')
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE s.sector = %s OR s.price <= %s"
    assert sql == expected_sql
    assert params == ["Tech", 50.5]

def test_generate_sql_sqlite_placeholder():
    sql, params = generate_sql('PE ratio < 15 AND revenue > 1000000', placeholder="?")
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE f.pe_ratio < ? AND f.revenue > ?"
    assert sql == expected_sql
    assert params == [15, 1000000]

def test_generate_sql_no_values_in_sql():
    sql, params = generate_sql('company == "Hacker Drop Table"')
    # Verify the potentially dangerous value is strictly parametrized and NOT in the SQL
    assert 'Hacker Drop Table' not in sql
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE s.company_name = %s"
    assert sql == expected_sql
    assert params == ["Hacker Drop Table"]

def test_generate_sql_different_case():
    sql, params = generate_sql('REVENUE > 50 and SEntiment < 1')
    expected_sql = "SELECT s.symbol, s.company_name FROM symbols s JOIN fundamentals f ON s.id = f.company_id WHERE f.revenue > %s AND f.sentiment < %s"
    assert sql == expected_sql
    assert params == [50, 1]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
