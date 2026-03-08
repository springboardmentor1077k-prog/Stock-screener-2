from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union

ALLOWED_FIELDS = {"pe_ratio", "debt", "market_cap", "revenue", "ebitda", "promoter_holding"}
ALLOWED_OPERATORS = {"<", ">", "<=", ">=", "="}

class Condition(BaseModel):
    field: str
    operator: str
    value: Union[int, float]

    @field_validator("field")
    def validate_field(cls, v):
        if v not in ALLOWED_FIELDS:
            raise ValueError(f"Unsupported metric: {v}")
        return v

    @field_validator("operator")
    def validate_operator(cls, v):
        if v not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {v}")
        return v


class DSLQuery(BaseModel):
    conditions: List[Condition] = Field(..., min_length=1, max_length=5)
    logic: str
    time_filter: Optional[str] = None

    @field_validator("logic")
    def validate_logic(cls, v):
        if v not in {"AND", "OR"}:
            raise ValueError("Logic must be AND or OR only")
        return v