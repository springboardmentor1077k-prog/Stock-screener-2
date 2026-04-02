import pytest
from backend.llm import parse_nl_to_dsl
from backend.compiler import validate_dsl

def test_dsl_simple_condition():
    """Test 1: Valid simple condition generates correct DSL structure."""
    query = "show me stocks with PE ratio less than 15"
    dsl = parse_nl_to_dsl(query)
    
    assert "where" in dsl, "DSL must contain 'where' key"
    conditions = dsl["where"]["conditions"]
    
    # Check if pe_ratio < 15 is found
    # regex fallback might generate it slightly differently but let's check for the logic
    match = next((c for c in conditions if c["field"] == "pe_ratio"), None)
    assert match is not None, "DSL must contain condition for pe_ratio"
    assert match["operator"] == "<", f"Incorrect operator for pe_ratio: {match['operator']}"
    assert int(match["value"]) == 15, f"Incorrect value for pe_ratio: {match['value']}"

def test_dsl_multiple_conditions():
    """Test 2: Valid multiple conditions generate correct DSL."""
    query = "PE ratio less than 15 AND revenue greater than 1000000"
    dsl = parse_nl_to_dsl(query)
    
    assert "where" in dsl, "DSL must contain 'where' key"
    conditions = dsl["where"]["conditions"]
    
    # regex fallback might find 2 or 3 depending on implementation, 
    # but the instructions ask to assert exactly 2
    assert len(conditions) == 2, f"Expected 2 conditions, got {len(conditions)}"
    
    pe_cond = next((c for c in conditions if c["field"] == "pe_ratio"), None)
    rev_cond = next((c for c in conditions if c["field"] == "revenue"), None)
    
    assert pe_cond["operator"] == "<"
    assert int(pe_cond["value"]) == 15
    assert rev_cond["operator"] == ">"
    assert int(rev_cond["value"]) == 1000000

def test_dsl_time_filter():
    """Test 3: Time filter is correctly included in DSL."""
    query = "revenue growth greater than 10 over last 4 quarters"
    dsl = parse_nl_to_dsl(query)
    
    assert "time_filter" in dsl, "DSL must contain 'time_filter' key"
    assert dsl["time_filter"]["type"] == "last_m_quarters", "Incorrect time filter type"
    assert dsl["time_filter"]["value"] == 4, f"Incorrect time filter value: {dsl['time_filter']['value']}"

def test_validate_dsl_invalid_field():
    """Test 4: Invalid field name is rejected."""
    dsl = {
        "where": {
            "conditions": [{"field": "invalid_field", "operator": "<", "value": 15}],
            "logic": "AND"
        }
    }
    is_valid, err = validate_dsl(dsl)
    assert is_valid is False, "Invalid field should be rejected"
    assert "Unknown field" in err, f"Expected 'Unknown field' in error message, got: {err}"

def test_validate_dsl_invalid_operator():
    """Test 5: Invalid operator is rejected."""
    dsl = {
        "where": {
            "conditions": [{"field": "pe_ratio", "operator": "!!", "value": 15}],
            "logic": "AND"
        }
    }
    is_valid, err = validate_dsl(dsl)
    assert is_valid is False, "Invalid operator should be rejected"
    assert "Invalid operator" in err, f"Expected 'Invalid operator' in error message, got: {err}"

def test_validate_dsl_empty_conditions():
    """Test 6: Empty conditions list is rejected."""
    dsl = {
        "where": {
            "conditions": [], # Empty list
            "logic": "AND"
        }
    }
    # Current implementation _validate_condition_tree checks for "conditions" list existance but not len > 0
    # Let's verify what the instructor expects. "Empty conditions list is rejected"
    # I should check if it handles it.
    is_valid, err = validate_dsl(dsl)
    # The requirement says "Assert: Validation raises an error"
    # Actually, if I look at my previous view of compiler.py, it doesn't check for len == 0.
    # I might need to adjust the code or the test. I'll make the test expect failure and adjust code if needed.
    # Wait, the instruction says "Write pytest test cases that test the following..."
    # If the app doesn't do it, I should probably make it do it too.
    assert is_valid is False, "Empty conditions should be rejected"

def test_validate_dsl_invalid_time_filter_value():
    """Test 7: Time filter value exceeding 12 is rejected."""
    dsl = {
        "where": {"conditions": [{"field": "pe_ratio", "operator": "<", "value": 50}], "logic": "AND"},
        "time_filter": {"type": "last_m_quarters", "value": 15}
    }
    is_valid, err = validate_dsl(dsl)
    assert is_valid is False, "Time filter > 12 should be rejected"
    assert "between 1 and 12" in err, f"Expected clear range error, got: {err}"
