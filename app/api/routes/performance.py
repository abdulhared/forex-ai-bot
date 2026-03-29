from fastapi import APIRouter, Query
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/performance")
def get_performance(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    """
    Get daily performance metrics for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., "2026-03-28")
    
    Returns:
        Performance metrics including total trades, win rate, gross PnL, etc.
    """
    db = SQLiteClient()
    performance = db.get_performance(date)
    
    if not performance:
        return {
            "date": date,
            "message": "No performance data found for this date"
        }
    
    return {
        "date": performance[0],
        "total_trades": performance[1],
        "wins": performance[2],
        "losses": performance[3],
        "gross_pnl": performance[4],
        "win_rate": performance[5],
        "opening_balance": performance[6]
    }