import uuid
from app.infrastructure.database.sqlite_client import SQLiteClient

db = SQLiteClient()

# test create_trade
trade_id = str(uuid.uuid4())
db.create_trade({
    "id": trade_id,
    "pair": "GBP_USD",
    "action": "SELL",
    "lot_size": 0.02,
    "entry_price": 1.26500,
    "stop_loss": 1.27000,
    "take_profit": 1.25500
})
print("✓ create_trade")

# test update_trade
db.update_trade(trade_id, 1.25500)
print("✓ update_trade")

# test log_signal
db.log_signal({
    "id": str(uuid.uuid4()),
    "pair": "GBP_USD",
    "action": "SELL",
    "confidence": 0.82,
    "stop_loss": 1.27000,
    "take_profit": 1.25500,
    "lot_size": 0.02,
    "model_version": "v1.0.0"
})
print("✓ log_signal")

# test log_error
db.log_error("trade", "Test error message", "pair: GBP_USD")
print("✓ log_error")

# test get_performance
result = db.get_performance("2026-03-28")
print(f"✓ get_performance returned: {result}")