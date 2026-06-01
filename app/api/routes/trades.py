from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/trades")
def get_trades(limit: int = 50):
    """
    Retrieve trades ordered by opened_at descending (newest first)
    
    Args:
        limit: Maximum number of trades to return (default: 50)
        
    Returns:
        List of trade dicts or error response
    """
    db = SQLiteClient()
    
    try:
        # row_factory returns list of dicts directly — no manual mapping needed
        trades = db.get_all_trades(limit=limit)
        return trades
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to retrieve trades from database",
                "detail": str(e),
                "limit_requested": limit
            }
        )