# app/schema/dsl_schema.py
from pydantic import BaseModel, Field
from typing import List, Literal, Union, Optional

AllowedOperator = Literal["=", "<", ">", "<=", ">=", "!="]
AllowedLogic = Literal["AND", "OR"]
TimeRange = Literal["last_quarter", "last_4_quarters", "last_8_quarters", "last_12_quarters"]
GrowthMetric = Literal["revenue_growth", "profit_growth", "avg_revenue_growth", "avg_profit_growth"]
TrendDirection = Literal["increasing", "decreasing", "volatile"]

class TimeFilter(BaseModel):
    """Time-based filter for quarterly data"""
    range: TimeRange = "last_4_quarters"
    quarters: Optional[int] = Field(None, ge=1, le=12)  # Custom quarter count

class GrowthCondition(BaseModel):
    """Growth-based condition"""
    metric: GrowthMetric
    operator: AllowedOperator
    value: float
    time_range: TimeRange = "last_4_quarters"
    min_quarters: int = Field(3, ge=2, le=12)  # Minimum quarters for trend analysis

class TrendCondition(BaseModel):
    """Trend analysis condition"""
    metric: Literal["revenue", "profit"]
    direction: TrendDirection
    confidence: float = Field(0.7, ge=0.5, le=1.0)  # Trend confidence threshold
    time_range: TimeRange = "last_4_quarters"

class Condition(BaseModel):
    field: str
    operator: AllowedOperator
    value: Union[int, float, str]

class DSL(BaseModel):
    logic: AllowedLogic
    conditions: List[Union[Condition, GrowthCondition, TrendCondition]]
    time_filter: Optional[TimeFilter] = None
    limit: int = Field(default=10, ge=1, le=100)
    
    def get_regular_conditions(self):
        """Get non-growth, non-trend conditions"""
        return [c for c in self.conditions if isinstance(c, Condition)]
    
    def get_growth_conditions(self):
        """Get growth-based conditions"""
        return [c for c in self.conditions if isinstance(c, GrowthCondition)]
    
    def get_trend_conditions(self):
        """Get trend-based conditions"""
        return [c for c in self.conditions if isinstance(c, TrendCondition)]