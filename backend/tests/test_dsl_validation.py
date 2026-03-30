import pytest
from backend.services.schemas import DSLQuery

def test_valid_dsl():
    dsl = {
        "conditions": [
            {"field": "pe_ratio", "operator": "<", "value": 20}
        ],
        "logic": "AND"
    }

    obj = DSLQuery(**dsl)
    assert obj.logic == "AND"


def test_invalid_field():
    dsl = {
        "conditions": [
            {"field": "invalid_field", "operator": "<", "value": 20}
        ]
    }

    with pytest.raises(Exception):
        DSLQuery(**dsl)


def test_invalid_operator():
    dsl = {
        "conditions": [
            {"field": "pe_ratio", "operator": "!!", "value": 20}
        ]
    }

    with pytest.raises(Exception):
        DSLQuery(**dsl)