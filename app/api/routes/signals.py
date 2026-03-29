from fastapi import APIRouter
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/signals")
def get_signals():
    """
    Retrieve all signals from the database.
    
    Returns:
        List of signals ordered by timestamp descending (newest first)
    """
    db = SQLiteClient()
    signals = db.get_all_signals()
    
    signals_list = []
    for signal in signals:
        signals_list.append({
            "id": signal[0],
            "pair": signal[1],
            "action": signal[2],
            "confidence": signal[3],
            "take_profit": signal[4],
            "stop_loss": signal[5],
            "lot_size": signal[6],
            "model_version": signal[7],
            "timestamp": signal[8]
        })
    
    return signals_list