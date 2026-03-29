# app/core/execution_engine/fill_handler.py

from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.database.sqlite_client import SQLiteClient
from app.infrastructure.database.redis_client import RedisClient
from app.shared.constants import LogCategory


class FillHandler:
    """
    Processes OANDA order fill responses.
    Extracts trade data, persists to SQLite, updates Redis.
    """

    def __init__(self):
        self.logger = setup_logger()
        self.sqlite = SQLiteClient()
        self.redis = RedisClient()

    def handle(self, response: dict, signal: dict) -> dict:
        """
        Process a successful OANDA fill response.

        Args:
            response: Raw OANDA response from order_placer
            signal:   Original signal dict

        Returns:
            Clean trade dict with actual fill details
        """
        # 1. Extract fill data from response
        fill = response["orderFillTransaction"]["tradeOpened"]
        trade_id    = fill["tradeID"]
        fill_price  = float(fill["price"])
        timestamp   = response["orderFillTransaction"]["time"]

        # 2. Build clean trade dict
        trade = {
            "trade_id":   trade_id,
            "pair":       signal["pair"],
            "action":     signal["action"],
            "lot_size":   signal["lot_size"],
            "entry_price": fill_price,          # actual fill price, not signal price
            "stop_loss":  signal["stop_loss"],
            "take_profit": signal["take_profit"],
            "status":     "open",               # this trade is now open
            "timestamp":  timestamp,
        }

        # 3. Save to SQLite
        self.sqlite.save_trade(trade)

        # 4. Update Redis — mark pair as having an open position
        self.redis.set(f"position:{signal['pair']}", trade_id)

        # 5. Log the fill
        self.logger.bind(category=LogCategory.TRADE.value).info(
            f"Fill confirmed: {signal['action']} {signal['pair']} @ {fill_price} (trade_id={trade_id})"
        )

        return trade