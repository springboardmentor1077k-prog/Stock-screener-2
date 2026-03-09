from pydantic import BaseModel
from typing import List, Any


class Filter(BaseModel):
    field: str
    operator: str
    value: Any


class DSLQuery(BaseModel):
    filters: List[Filter]
    logic: str