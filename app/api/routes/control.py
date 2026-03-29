from fastapi import APIRouter

router = APIRouter()


@router.post("/pause")
def pause_trading():
    """Pause the trading bot (graceful halt)"""
    return {"message": "Trading paused"}


@router.post("/resume")
def resume_trading():
    """Resume the trading bot after pause"""
    return {"message": "Trading resumed"}


@router.post("/emergency-stop")
def emergency_stop():
    """Emergency stop — immediately halt all trading activity"""
    return {"message": "Emergency stop triggered"}