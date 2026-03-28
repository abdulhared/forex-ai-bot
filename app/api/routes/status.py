from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def get_status():
    """
    Get the current status of the trading bot.
    
    Returns:
        - status: running/stopped
        - model_version: AI model version
        - active_pairs: list of currency pairs being traded
    """
    return {
        "status": "running",
        "model_version": "v1.0.0",
        "active_pairs": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
    }