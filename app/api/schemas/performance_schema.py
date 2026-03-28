from pydantic import BaseModel


class PerformanceResponse(BaseModel):
    """
    Pydantic model for daily performance metrics returned by the API.
    
    Matches the performance_daily table columns exactly.
    """
    
    date: str
    total_trades: int
    wins: int
    losses: int
    gross_pnl: float
    win_rate: float
    opening_balance: float