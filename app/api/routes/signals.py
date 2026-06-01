from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/signals")
def get_signals(limit: int = 50):
    """
    Retrieve signals ordered by timestamp descending (newest first)
    
    Args:
        limit: Maximum number of signals to return (default: 50)
        
    Returns:
        List of signal dicts or error response
    """
    db = SQLiteClient()
    
    try:
        # row_factory returns list of dicts directly — no manual mapping needed
        signals = db.get_all_signals(limit=limit)
        return signals
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to retrieve signals from database",
                "detail": str(e),
                "limit_requested": limit
            }
        )