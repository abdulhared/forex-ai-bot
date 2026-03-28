from pydantic import BaseModel
from typing import Optional


class TradeResponse(BaseModel):
    """
    Pydantic model for trade data returned by the API.
    
    Used for listing trades and returning trade details to clients.
    Close-related fields are optional because open trades haven't closed yet.
    """
    
    id: str
    pair: str
    action: str
    lot_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    status: str
    opened_at: str
    close_price: Optional[float] = None
    closed_at: Optional[str] = None