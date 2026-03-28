from fastapi import APIRouter
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/trades")
def get_trades():
    """
    Retrieve all trades from the database.
    
    Returns:
        List of trades ordered by opened_at descending (newest first)
    """
    db = SQLiteClient()
    trades = db.get_all_trades()
    
    # Convert list of tuples to list of dictionaries for JSON response
    trades_list = []
    for trade in trades:
        trades_list.append({
            "id": trade[0],
            "pair": trade[1],
            "action": trade[2],
            "lot_size": trade[3],
            "entry_price": trade[4],
            "stop_loss": trade[5],
            "take_profit": trade[6],
            "status": trade[7],
            "opened_at": trade[8],
            "close_price": trade[9],
            "closed_at": trade[10]
        })
    
    return trades_list