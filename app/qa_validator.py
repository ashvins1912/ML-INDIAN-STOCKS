from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
class Candle(BaseModel):
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    @model_validator(mode="after")
    def check_ranges(self):
        if self.high < max(self.open,self.close): raise ValueError("High must be >= max(Open, Close)")
        if self.low > min(self.open,self.close): raise ValueError("Low must be <= min(Open, Close)")
        if self.volume < 0: raise ValueError("Volume must be non-negative")
        return self

def gap_requires_review(previous_close: float, current_open: float, threshold: float=0.22) -> bool:
    if not previous_close: return False
    return abs(current_open/previous_close-1) > threshold
