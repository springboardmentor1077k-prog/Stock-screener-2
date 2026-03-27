from pydantic import BaseModel

class AlertCreate(BaseModel):
    user_id: int
    stock_symbol: str
    condition_type: str   # ABOVE / BELOW
    target_price: float


class AlertResponse(BaseModel):
    id: int
    user_id: int
    stock_symbol: str
    condition_type: str
    target_price: float