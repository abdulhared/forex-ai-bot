from fastapi import APIRouter, Query
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/performance")
def get_performance(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    """Get daily performance metrics for a specific date"""
    db = SQLiteClient()
    performance = db.get_performance(date)  # Returns dict or None
    
    if not performance:
        # Return zeros for consistent schema (better for clients)
        return {
            "date": date,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_pnl": 0.0,
            "win_rate": 0.0,
            "opening_balance": None
        }
    
    # performance is already a dict from row_factory
    return performance