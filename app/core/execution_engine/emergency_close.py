# app/core/execution_engine/emergency_close.py

import oandapyV20
import oandapyV20.endpoints.trades as trades
from oandapyV20.exceptions import V20Error

from app.shared.config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.database.sqlite_client import SQLiteClient
from app.infrastructure.database.redis_client import RedisClient
from app.shared.constants import LogCategory


class EmergencyClose:
    """
    Closes all open positions immediately.
    Used during circuit breaker, system failure, or manual operator command.
    Never stops on individual trade failure — close as many as possible.
    """

    def __init__(self):
        self.client = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.logger = setup_logger()
        self.sqlite = SQLiteClient()
        self.redis = RedisClient()

    def close_all(self, reason: str) -> dict:
        """
        Fetch and close all open trades from OANDA.

        Args:
            reason: Why emergency close was triggered (for logging)

        Returns:
            Summary dict with total, closed, failed counts
        """
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"EMERGENCY CLOSE triggered: {reason}"
        )

        # 1. Fetch all open trades from OANDA
        request = trades.TradesList(OANDA_ACCOUNT_ID, params={"state": "OPEN"})
        response = self.client.request(request)
        open_trades = response["trades"]

        # 2. Initialise counters
        total = len(open_trades)
        closed = 0
        failed = 0
        trade_ids = []

        # 3. Loop — never stop on failure
        for trade in open_trades:
            trade_id = trade["id"]
            pair = trade["instrument"]
            trade_ids.append(trade_id)

            try:
                # Close this trade
                close_request = trades.TradeClose(OANDA_ACCOUNT_ID, tradeID=trade_id)
                self.client.request(close_request)

                # Update local state
                self.sqlite.update_trade_status(trade_id, "closed")
                self.redis.delete(f"position:{pair}")

                closed += 1
                self.logger.bind(category=LogCategory.TRADE.value).info(
                    f"Emergency closed: {pair} (trade_id={trade_id})"
                )

            except V20Error as e:
                failed += 1
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to emergency close {pair}: code={e.code}, message={e.msg}"
                )
                # Continue to next trade — explicit continue not needed

        # 4. Return summary
        return {
            "reason": reason,
            "total": total,
            "closed": closed,
            "failed": failed,
            "trade_ids": trade_ids
        }