# app/services/validator.py
from typing import Union
from app.schema.dsl_schema import DSL, Condition

ALLOWED_FIELDS = {
    "sector", "pe_ratio", "peg_ratio", "debt_fcf", 
    "promoter_holding", "revenue", "ebitda"
}

ALLOWED_OPERATORS = {"=", "<", ">", "<=", ">=", "!="}
MAX_CONDITIONS = 10
MAX_LIMIT = 100

FIELD_TYPES = {
    "sector": str,
    "pe_ratio": float,
    "peg_ratio": float,
    "debt_fcf": float,
    "promoter_holding": float,
    "revenue": float,
    "ebitda": float
}

def validate_fields(dsl):
    """Simple field validation for screener service"""
    # Check number of conditions
    if len(dsl.conditions) > MAX_CONDITIONS:
        raise ValueError(f"Query too complex. Maximum {MAX_CONDITIONS} conditions allowed")
    
    # Check limit
    if dsl.limit > MAX_LIMIT:
        raise ValueError(f"Limit cannot exceed {MAX_LIMIT}")
    
    # Validate each condition
    for cond in dsl.conditions:
        if cond.field not in ALLOWED_FIELDS:
            raise ValueError(f"Unsupported field: {cond.field}. Allowed fields: {', '.join(ALLOWED_FIELDS)}")
        
        if cond.operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {cond.operator}. Allowed operators: {', '.join(ALLOWED_OPERATORS)}")
        
        expected_type = FIELD_TYPES.get(cond.field)
        if expected_type == str:
            if not isinstance(cond.value, str):
                raise ValueError(f"Field {cond.field} requires string value")
            if not cond.value.strip():
                raise ValueError(f"Field {cond.field} cannot be empty")
        elif expected_type == float:
            try:
                float(cond.value)
            except (TypeError, ValueError):
                raise ValueError(f"Field {cond.field} requires numeric value")
    
    # Validate logic
    if dsl.logic not in ["AND", "OR"]:
        raise ValueError("Logic must be either AND or OR")
    
    return True

def validate_dsl(dsl: DSL) -> bool:
    """Comprehensive DSL validation (alias)"""
    return validate_fields(dsl)