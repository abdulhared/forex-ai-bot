from pydantic import BaseModel


class EmergencyStopRequest(BaseModel):
    """
    Pydantic model for emergency stop request payload.
    
    Used when triggering an emergency halt of the trading bot.
    """
    
    reason: str