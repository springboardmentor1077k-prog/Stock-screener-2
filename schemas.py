from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union

# Whitelists as per constraints
# 🔥 Added 'revenue_growth' here
ALLOWED_FIELDS = {"pe_ratio", "debt", "market_cap", "revenue", "ebitda", "promoter_holding", "revenue_growth"}
ALLOWED_OPERATORS = {"<", ">", "<=", ">=", "="}

class Condition(BaseModel):
    field: str
    operator: str
    value: Union[int, float]

    @field_validator("field")
    def validate_field(cls, v):
        if v not in ALLOWED_FIELDS:
            raise ValueError(f"Unsupported metric: {v}") # Fails gracefully if field is wrong
        return v

    @field_validator("operator")
    def validate_operator(cls, v):
        if v not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {v}")
        return v

class DSLQuery(BaseModel):
    # Guardrail: Maximum 5 conditions allowed, cannot be empty
    conditions: List[Condition] = Field(..., min_length=1, max_length=5)
    logic: str
    time_filter: Optional[str] = None

    @field_validator("logic")
    def validate_logic(cls, v):
        if v not in {"AND", "OR"}:
            raise ValueError("Logic must be AND or OR only")
        return v
    
# 🔥 Portfolio Input Validation
class PortfolioItem(BaseModel):
    user_id: str = "user1" # Ippatiki default user1 ani peduthunnam
    symbol: str
    quantity: int
    buy_price: float

    @field_validator("quantity")
    def validate_qty(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("buy_price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Buy price must be a valid amount")
        return v