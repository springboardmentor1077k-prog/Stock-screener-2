# app/services/validator.py
from typing import Union
from app.schema.dsl_schema import DSL, Condition, GrowthCondition, TrendCondition

ALLOWED_FIELDS = {
    "sector", "pe_ratio", "peg_ratio", "debt_fcf", 
    "promoter_holding", "revenue", "ebitda"
}

ALLOWED_OPERATORS = {"=", "<", ">", "<=", ">=", "!="}
ALLOWED_GROWTH_METRICS = {"revenue_growth", "profit_growth", "avg_revenue_growth", "avg_profit_growth"}
ALLOWED_TREND_DIRECTIONS = {"increasing", "decreasing", "volatile"}
ALLOWED_TIME_RANGES = {"last_quarter", "last_4_quarters", "last_8_quarters", "last_12_quarters"}
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

def validate_dsl(dsl: DSL) -> bool:
    """Comprehensive DSL validation including growth conditions"""
    
    total_conditions = len(dsl.conditions)
    if total_conditions > MAX_CONDITIONS:
        raise ValueError(f"Query too complex. Maximum {MAX_CONDITIONS} conditions allowed")
    
    if dsl.limit > MAX_LIMIT:
        raise ValueError(f"Limit cannot exceed {MAX_LIMIT}")
    
    # Validate regular conditions
    for cond in dsl.get_regular_conditions():
        _validate_regular_condition(cond)
    
    # Validate growth conditions
    for cond in dsl.get_growth_conditions():
        _validate_growth_condition(cond)
    
    # Validate trend conditions
    for cond in dsl.get_trend_conditions():
        _validate_trend_condition(cond)
    
    # Validate time filter if present
    if dsl.time_filter:
        if dsl.time_filter.range not in ALLOWED_TIME_RANGES:
            raise ValueError(f"Invalid time range: {dsl.time_filter.range}")
    
    return True

def _validate_regular_condition(cond: Condition):
    """Validate regular field conditions"""
    if cond.field not in ALLOWED_FIELDS:
        raise ValueError(f"Unsupported field: {cond.field}")
    
    if cond.operator not in ALLOWED_OPERATORS:
        raise ValueError(f"Unsupported operator: {cond.operator}")
    
    expected_type = FIELD_TYPES.get(cond.field)
    if expected_type == str and not isinstance(cond.value, str):
        raise ValueError(f"Field {cond.field} requires string value")
    elif expected_type == float:
        try:
            float(cond.value)
        except (TypeError, ValueError):
            raise ValueError(f"Field {cond.field} requires numeric value")

def _validate_growth_condition(cond: GrowthCondition):
    """Validate growth-based conditions"""
    if cond.metric not in ALLOWED_GROWTH_METRICS:
        raise ValueError(f"Unsupported growth metric: {cond.metric}")
    
    if cond.operator not in ALLOWED_OPERATORS:
        raise ValueError(f"Unsupported operator: {cond.operator}")
    
    if not isinstance(cond.value, (int, float)):
        raise ValueError(f"Growth condition value must be numeric")
    
    if cond.time_range not in ALLOWED_TIME_RANGES:
        raise ValueError(f"Invalid time range: {cond.time_range}")
    
    if cond.min_quarters < 2:
        raise ValueError(f"min_quarters must be at least 2")

def _validate_trend_condition(cond: TrendCondition):
    """Validate trend analysis conditions"""
    if cond.direction not in ALLOWED_TREND_DIRECTIONS:
        raise ValueError(f"Unsupported trend direction: {cond.direction}")
    
    if cond.confidence < 0.5 or cond.confidence > 1.0:
        raise ValueError(f"Confidence must be between 0.5 and 1.0")
    
    if cond.time_range not in ALLOWED_TIME_RANGES:
        raise ValueError(f"Invalid time range: {cond.time_range}")