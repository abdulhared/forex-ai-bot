# app/core/execution_engine/trailing_stop.py

import oandapyV20
import oandapyV20.endpoints.trades as trades
from oandapyV20.exceptions import V20Error

from app.shared.config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.database.redis_client import RedisClient
from app.shared.constants import LogCategory


class TrailingStop:
    """
    Calculates and updates trailing stop-loss on open trades.
    Tracks peak price in Redis. Only moves stop in profit direction.
    """

    def __init__(self):
        self.client = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.logger = setup_logger()
        self.redis = RedisClient()

    def update(self, trade_id: str, pair: str, action: str,
               current_price: float, trail_pips: int) -> float:
        """
        Update trailing stop if price has moved in our favour.

        Args:
            trade_id:      OANDA trade ID
            pair:          Instrument e.g. "EUR_USD"
            action:        "BUY" or "SELL"
            current_price: Latest market price
            trail_pips:    Trail distance in pips

        Returns:
            New stop-loss price (float)
        """
        # 1. Calculate pip size
        pip_size = 0.01 if "JPY" in pair else 0.0001
        trail_distance = trail_pips * pip_size

        # 2. Get or initialise peak price from Redis
        redis_key = f"trailing:{trade_id}"
        peak = self.redis.get(redis_key)
        if peak is None:
            peak = current_price
            self.redis.set(redis_key, str(peak))
        else:
            peak = float(peak)

        # 3. Update peak if price moved in our favour
        if action == "BUY" and current_price > peak:
            peak = current_price
            self.redis.set(redis_key, str(peak))
        elif action == "SELL" and current_price < peak:
            peak = current_price
            self.redis.set(redis_key, str(peak))

        # 4. Calculate new stop-loss
        if action == "BUY":
            new_stop = peak - trail_distance
        else:
            new_stop = peak + trail_distance

        # 5. Send updated stop to OANDA
        try:
            request = trades.TradeCRCDO(
                OANDA_ACCOUNT_ID,
                tradeID=trade_id,
                data={"stopLoss": {"price": str(round(new_stop, 5))}}
            )
            self.client.request(request)
            self.logger.bind(category=LogCategory.TRADE.value).info(
                f"Trailing stop updated: {action} {pair} | peak={peak:.5f} | new_stop={new_stop:.5f}"
            )
        except V20Error as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Failed to update trailing stop for {trade_id}: code={e.code}, message={e.msg}"
            )

        return round(new_stop, 5)