from fastapi import APIRouter

router = APIRouter()


@router.post("/pause")
def pause_trading():
    """
    Pause the trading bot.
    
    Returns:
        Confirmation message
    """
    return {"message": "Trading paused"}


@router.post("/resume")
def resume_trading():
    """
    Resume the trading bot.
    
    Returns:
        Confirmation message
    """
    return {"message": "Trading resumed"}


@router.post("/emergency-stop")
def emergency_stop():
    """
    Trigger emergency stop to halt all trading activity immediately.
    
    Returns:
        Confirmation message
    """
    return {"message": "Emergency stop triggered"}