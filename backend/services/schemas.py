from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union


ALLOWED_FIELDS = {
    "pe_ratio",
    "peg_ratio",
    "market_cap",
    "revenue",
    "revenue_growth",
    "ebitda",
    "profit_margin",
    "roe",
    "roa",
    "debt_to_equity",
    "eps",
    "book_value",
    "dividend_yield",
    "sector",
    "price_growth"
}

ALLOWED_OPERATORS = {"<", ">", "<=", ">=", "="}

ALLOWED_TIME_FILTERS = {
    "last_year",
    "last_4_quarters",
    "recent_quarters",
    "last_6_months"  
}


class Condition(BaseModel):

    field: str
    operator: str
    value: Union[int, float, str]

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

    @field_validator("value")
    def validate_value(cls, v):
        if not isinstance(v, (int, float, str)):
            raise ValueError("Value must be numeric or text")
        return v


class DSLQuery(BaseModel):

    conditions: List[Condition] = Field(default_factory=list, max_length=5)

    logic: str = "AND"

    time_filter: Optional[str] = None

    limit: int | None = None

    @field_validator("logic")
    def validate_logic(cls, v):
        v = v.upper()
        if v not in {"AND", "OR"}:
            raise ValueError("Logic must be AND or OR only")
        return v

    @field_validator("time_filter")
    def validate_time_filter(cls, v):
        if v and v not in ALLOWED_TIME_FILTERS:
            raise ValueError("Unsupported time filter")
        return v