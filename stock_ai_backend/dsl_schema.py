from pydantic import BaseModel
from typing import List, Union


class Condition(BaseModel):
    field: str
    operator: str
    value: Union[int, float, str]


class QueryDSL(BaseModel):
    conditions: List[Condition]
    logic: str = "AND"
