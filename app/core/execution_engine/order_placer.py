# app/core/execution_engine/order_placer.py

import time
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
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def place_order(self, signal: dict, lot_size: float) -> dict:
        """
        Place a market order based on a signal.

        Args:
            signal: dict with keys — pair, action, stop_loss, take_profit
            lot_size: float (e.g. 0.02)

        Returns:
            dict with success status and either response or error details
        """
        # Guard: HOLD action should not place an order
        if signal["action"] == "HOLD":
            self.logger.info(
                f"Skipping order placement: Action is HOLD for {signal['pair']}"
            )
            return {
                "success": True,
                "skipped": True,
                "message": "Action was HOLD, no order placed"
            }

        # 1. Convert lot size to units (negative for SELL)
        units = lot_size * 100000
        if signal["action"] == "SELL":
            units = -units

        # Round units properly (not truncate)
        rounded_units = int(round(units))
        
        # 2. Round stop loss and take profit to 5 decimal places
        rounded_stop_loss = round(signal["stop_loss"], 5)
        rounded_take_profit = round(signal["take_profit"], 5)

        # 3. Build the order body
        order_body = {
            "order": {
                "type": "MARKET",
                "instrument": signal["pair"],
                "units": str(rounded_units),
                "stopLossOnFill": {"price": str(rounded_stop_loss)},
                "takeProfitOnFill": {"price": str(rounded_take_profit)},
            }
        }

        # 4. Create the request object
        request = orders.OrderCreate(OANDA_ACCOUNT_ID, data=order_body)

        # 5. Send to OANDA with retry logic and error handling
        self.logger.info(
            f"Placing {signal['action']} order: {rounded_units} units "
            f"on {signal['pair']} (SL={rounded_stop_loss}, TP={rounded_take_profit})"
        )
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.request(request)
                
                # Check for order fill confirmation
                if response.get("orderFillTransaction") is None:
                    self.logger.bind(category=LogCategory.WARNING.value).warning(
                        f"Order accepted but fill not confirmed for {signal['action']} "
                        f"{signal['pair']}. Response: {response}"
                    )
                    return {
                        "success": True,
                        "warning": "Order accepted but fill not confirmed",
                        "response": response
                    }
                
                # Success with fill confirmation
                self.logger.info(
                    f"Order placed and filled successfully: {rounded_units} units "
                    f"on {signal['pair']} (attempt {attempt}/{self.max_retries})"
                )
                return {"success": True, "response": response}
            
            except V20Error as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Order attempt {attempt}/{self.max_retries} failed for "
                    f"{signal['action']} {signal['pair']}: code={e.code}, message={e.msg}"
                )
                
                if attempt < self.max_retries:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.bind(category=LogCategory.ERROR.value).error(
                        f"All {self.max_retries} attempts failed for order on {signal['pair']}"
                    )
                    return {
                        "success": False,
                        "error_code": e.code,
                        "error_message": e.msg,
                        "attempts": self.max_retries
                    }
        
        # Fallback (should never reach here)
        return {
            "success": False,
            "error_message": "Unexpected error in retry loop"
        }