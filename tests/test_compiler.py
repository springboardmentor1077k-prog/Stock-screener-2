import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.compiler import validate_dsl, compile_sql_from_dsl

def test_compiler_select_defaults():
    dsl = {
        "where": {
            "logic": "AND",
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": 20}
            ]
        }
    }
    
    is_valid, _ = validate_dsl(dsl)
    assert is_valid

    sql, params = compile_sql_from_dsl(dsl)
    assert "SELECT s.symbol, s.company_name, s.sector, f.pe_ratio, f.revenue, f.ebitda, f.debt_to_equity" in sql
    assert "WHERE f.pe_ratio < %s" in sql
    assert params[0] == 20
    assert "LIMIT %s OFFSET %s" in sql

def test_compiler_nested_conditions():
    dsl = {
        "select": ["symbol", "pe_ratio"],
        "where": {
            "logic": "OR",
            "conditions": [
                {"field": "pe_ratio", "operator": "<", "value": 15},
                {
                    "logic": "AND",
                    "conditions": [
                        {"field": "sector", "operator": "IN", "value": ["Technology", "Healthcare"]},
                        {"field": "revenue", "operator": ">", "value": 100000}
                    ]
                }
            ]
        },
        "order_by": [
            {"field": "pe_ratio", "direction": "DESC"}
        ]
    }
    
    is_valid, _ = validate_dsl(dsl)
    assert is_valid
    
    sql, params = compile_sql_from_dsl(dsl, default_limit=50)
    
    assert "SELECT s.symbol, f.pe_ratio" in sql
    assert "FROM symbols s JOIN fundamentals f ON s.id = f.company_id" in sql
    assert "(s.sector IN %s AND f.revenue > %s)" in sql
    
    assert params[0] == 15
    assert params[1] == ("Technology", "Healthcare")
    assert params[2] == 100000
    assert params[3] == 50 # limit
    assert params[4] == 0  # offset
    
    assert "ORDER BY f.pe_ratio DESC" in sql

def test_compiler_validation_fails_on_bad_fields():
    dsl = {
        "where": {
            "logic": "AND",
            "conditions": [
                {"field": "hacker_column", "operator": "=", "value": 1}
            ]
        }
    }
    is_valid, err = validate_dsl(dsl)
    assert not is_valid
    assert "Unknown field" in err

if __name__ == "__main__":
    pytest.main(["-v", __file__])
