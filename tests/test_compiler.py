import pytest
from backend.compiler import compile_sql_from_dsl

def test_compile_sql_simple_condition():
    """Test 1: Simple single condition compiles to correct parameterized SQL."""
    dsl = {
        "where": {
            "conditions": [{"field": "pe_ratio", "operator": "<", "value": 15}],
            "logic": "AND"
        }
    }
    sql, params = compile_sql_from_dsl(dsl)
    
    assert "(f.pe_ratio < %s)" in sql, f"Incorrect SQL structure: {sql}"
    assert 15 in params, f"Value 15 should be in parameters, got: {params}"
    assert "15" not in sql, "Literal value 15 should NOT be directly in the SQL string"

def test_compile_sql_multiple_conditions():
    """Test 2: Multiple conditions compile with correct AND joining."""
    dsl = {
        "where": {
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": 15},
                {"field": "revenue", "operator": ">", "value": 1000000}
            ],
            "logic": "AND"
        }
    }
    sql, params = compile_sql_from_dsl(dsl)
    
    assert "f.pe_ratio < %s AND f.revenue > %s" in sql, "SQL should join conditions with AND"
    assert params == [15, 1000000, 100, 0], f"Parameters should match provided values (plus limit/offset): {params}"

def test_compile_sql_time_filter():
    """Test 3: Time filter compiles to correct SQL date condition."""
    dsl = {
        "where": {"conditions": [{"field": "pe_ratio", "operator": "<", "value": 50}], "logic": "AND"},
        "time_filter": {"type": "last_m_quarters", "value": 4}
    }
    sql, params = compile_sql_from_dsl(dsl)
    
    # Check for historical_metrics JOIN
    assert "JOIN historical_metrics h" in sql or "LEFT JOIN historical_metrics h" in sql, "Must join historical metrics"
    # Check for quarter interval condition with parameter
    assert "(h.quarter >= current_date - (interval '1 month' * %s) OR h.quarter IS NULL)" in sql, "Missing parameterized time filter"
    assert 12 in params, "Interval value 12 should be in parameters"

def test_compile_sql_no_literals():
    """Test 4: No value is ever concatenated directly into SQL string."""
    dsl = {
        "where": {
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": 15},
                {"field": "sector", "operator": "IN", "value": ["Healthcare"]}
            ],
            "logic": "AND"
        },
        "time_filter": {"type": "last_m_quarters", "value": 4}
    }
    sql, params = compile_sql_from_dsl(dsl)
    
    # Check that 15, Healthcare, and 12 are not in SQL as strings
    assert "15" not in sql, "Numeric literal 15 found in SQL"
    assert "Healthcare" not in sql, "String literal Healthcare found in SQL"
    assert "12" not in sql, "Interval literal 12 found in SQL"
    assert 15 in params, "15 missing from params"
    assert ("Healthcare",) in params, "Healthcare tuple missing from params"
    assert 12 in params, "12 missing from params"

def test_compile_sql_joins():
    """Test 5: Correct table joins are generated."""
    # pe_ratio is from Fundamentals, revenue_growth is from Historical
    dsl = {
        "where": {
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": 15},
                {"field": "revenue_growth", "operator": ">", "value": 5}
            ],
            "logic": "AND"
        }
    }
    sql, params = compile_sql_from_dsl(dsl)
    
    # Needs both fundamentals and historical joins
    assert "JOIN fundamentals f" in sql or "JOIN fundamentals f" in sql
    assert "JOIN historical_metrics h" in sql or "LEFT JOIN historical_metrics h" in sql
    assert "JOIN symbols s" in sql or "FROM symbols s" in sql
