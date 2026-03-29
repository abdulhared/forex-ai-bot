from fastapi import APIRouter
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/trades")
def get_trades():
    """Retrieve all trades ordered by opened_at descending (newest first)"""
    db = SQLiteClient()
    # row_factory returns list of dicts directly — no manual mapping needed
    return db.get_all_trades()