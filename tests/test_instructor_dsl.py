import pytest
import sys
import os

# Add parent to path for relative importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.instructor_dsl_parser import generate_sql

def test_generate_sql_simple_condition():
    sql, params = generate_sql('PE ratio < 15')
    assert sql == "SELECT * FROM fundamentals WHERE pe_ratio < %s"
    assert params == [15]

def test_generate_sql_multiple_conditions_and():
    sql, params = generate_sql('PE ratio < 15 AND revenue > 1000000')
    assert sql == "SELECT * FROM fundamentals WHERE pe_ratio < %s AND revenue > %s"
    assert params == [15, 1000000]

def test_generate_sql_multiple_conditions_or():
    sql, params = generate_sql('sector == "Tech" OR price <= 50.5')
    assert sql == "SELECT * FROM fundamentals WHERE sector = %s OR price <= %s"
    assert params == ["Tech", 50.5]

def test_generate_sql_sqlite_placeholder():
    sql, params = generate_sql('PE ratio < 15 AND revenue > 1000000', placeholder="?")
    assert sql == "SELECT * FROM fundamentals WHERE pe_ratio < ? AND revenue > ?"
    assert params == [15, 1000000]

def test_generate_sql_no_values_in_sql():
    sql, params = generate_sql('company == "Hacker Drop Table"')
    # Verify the potentially dangerous value is strictly parametrized and NOT in the SQL
    assert 'Hacker Drop Table' not in sql
    assert sql == "SELECT * FROM fundamentals WHERE company_name = %s"
    assert params == ["Hacker Drop Table"]

def test_generate_sql_different_case():
    sql, params = generate_sql('REVENUE > 50 and SEntiment < 1')
    assert sql == "SELECT * FROM fundamentals WHERE revenue > %s AND sentiment < %s"
    assert params == [50, 1]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
