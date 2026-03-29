from fastapi import APIRouter
from app.infrastructure.database.sqlite_client import SQLiteClient

router = APIRouter()


@router.get("/signals")
def get_signals():
    """Retrieve all signals ordered by timestamp descending (newest first)"""
    db = SQLiteClient()
    # row_factory returns list of dicts directly — no manual mapping needed
    return db.get_all_signals()