# app/core/execution_engine/order_placer.py

import oandapyV20
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error

from app.shared.config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class OrderPlacer:
    """
    Sends market orders to OANDA.
    Converts lot size to units, attaches SL/TP, calls the API.
    """

    def __init__(self):
        self.client = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.logger = setup_logger()

    def place_order(self, signal: dict, lot_size: float) -> dict:
        """
        Place a market order based on a signal.

        Args:
            signal: dict with keys — pair, action, stop_loss, take_profit
            lot_size: float (e.g. 0.02)

        Returns:
            dict with success status and either response or error details
        """
        # 1. Convert lot size to units (negative for SELL)
        units = lot_size * 100000
        if signal["action"] == "SELL":
            units = -units

        # 2. Build the order body
        order_body = {
            "order": {
                "type": "MARKET",
                "instrument": signal["pair"],
                "units": str(int(units)),
                "stopLossOnFill": {"price": str(signal["stop_loss"])},
                "takeProfitOnFill": {"price": str(signal["take_profit"])},
            }
        }

        # 3. Create the request object
        request = orders.OrderCreate(OANDA_ACCOUNT_ID, data=order_body)

        # 4. Send to OANDA with error handling
        self.logger.info(f"Placing {signal['action']} order: {int(units)} units on {signal['pair']}")
        
        try:
            response = self.client.request(request)
            self.logger.info(f"Order placed successfully: {response}")
            return {"success": True, "response": response}
        
        except V20Error as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Order failed for {signal['action']} {signal['pair']}: code={e.code}, message={e.msg}"
            )
            return {
                "success": False,
                "error_code": e.code,
                "error_message": e.msg
            }