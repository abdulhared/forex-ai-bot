from fastapi import APIRouter

router = APIRouter()


@router.get("/risk")
def get_risk():
    """
    Get current risk management status.
    
    Returns:
        Open positions count, current drawdown, and status message.
    """
    return {
        "open_positions": 0,
        "current_drawdown": 0.0,
        "message": "Risk data will be populated when trading engine is active"
    }