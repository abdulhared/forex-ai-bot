# app/core/execution_engine/trade_monitor.py

import oandapyV20
import oandapyV20.endpoints.trades as trades
from oandapyV20.exceptions import V20Error

from app.shared.config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.database.sqlite_client import SQLiteClient
from app.infrastructure.database.redis_client import RedisClient
from app.shared.constants import LogCategory


class TradeMonitor:
    """
    Polls OANDA for live trade status.
    Updates SQLite and Redis when a trade closes.
    """

    def __init__(self):
        self.client = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.logger = setup_logger()
        self.sqlite = SQLiteClient()
        self.redis = RedisClient()

    def check_trade(self, trade_id: str, pair: str) -> dict:
        """
        Fetch trade status from OANDA.
        If closed: update SQLite, delete Redis key.

        Args:
            trade_id: OANDA trade ID string
            pair:     Instrument string e.g. "EUR_USD"

        Returns:
            dict with state, realized_pl, and close_time
        """
        try:
            # 1. Build and send request
            request = trades.TradeDetails(OANDA_ACCOUNT_ID, tradeID=trade_id)
            response = self.client.request(request)

            # 2. Extract trade state
            trade_data = response["trade"]
            state = trade_data["state"]
            realized_pl = trade_data.get("realizedPL", None)
            close_time = trade_data.get("closeTime", None)

            # 3. If closed — update local state
            if state == "CLOSED":
                self.sqlite.update_trade_status(trade_id, "closed")
                self.redis.delete(f"position:{pair}")
                self.logger.bind(category=LogCategory.TRADE.value).info(
                    f"Trade closed: {pair} | PL={realized_pl} | closed_at={close_time}"
                )

            return {
                "trade_id": trade_id,
                "state": state,
                "realized_pl": realized_pl,
                "close_time": close_time
            }

        except V20Error as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Failed to check trade {trade_id}: code={e.code}, message={e.msg}"
            )
            return {
                "trade_id": trade_id,
                "state": "unknown",
                "realized_pl": None,
                "close_time": None
            }