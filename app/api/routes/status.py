from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def get_status():
    """Get current bot status, model version, and active trading pairs"""
    return {
        "status": "running",
        "model_version": "v1.0.0",
        "active_pairs": ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
    }