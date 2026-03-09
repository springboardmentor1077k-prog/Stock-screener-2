from pydantic import BaseModel, Field
from typing import List, Literal, Union

AllowedOperator = Literal["=", "<", ">", "<=", ">=", "!="]
AllowedLogic = Literal["AND", "OR"]

class Condition(BaseModel):
    field: str
    operator: AllowedOperator
    value: Union[int, float, str]

class DSL(BaseModel):
    logic: AllowedLogic
    conditions: List[Condition]
    limit: int = Field(default=10, ge=1, le=100)