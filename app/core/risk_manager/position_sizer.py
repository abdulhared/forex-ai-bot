from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class PositionSizer:
    """Calculates position size based on account balance and stop loss distance"""
    
    def __init__(self, max_risk_per_trade=0.01):  # 1% default
        self.logger = setup_logger()
        self.max_risk_per_trade = max_risk_per_trade
    
    def calculate(self, balance, entry_price, stop_loss):
        """
        Calculate position size using fixed fractional position sizing.
        
        Args:
            balance: Account balance in base currency
            entry_price: Entry price of the trade
            stop_loss: Stop loss price level
            
        Returns:
            Lot size (clamped between 0.01 and 1.0)
        """
        if balance <= 0:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Invalid balance: {balance}"
            )
            return 0.01  # Minimum lot size as fallback
        
        # Calculate risk amount (1% of balance)
        risk_amount = balance * self.max_risk_per_trade
        
        # Calculate price risk (distance to stop loss)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                "Stop loss cannot equal entry price"
            )
            return 0.01
        
        # Fixed fractional position sizing formula
        # 100,000 = standard lot size in Forex
        lot_size = risk_amount / (price_risk * 100000)
        
        # Round to 2 decimal places (standard lot size precision)
        lot_size = round(lot_size, 2)
        
        # Clamp between min and max allowed lot sizes
        lot_size = max(0.01, min(lot_size, 1.0))
        
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"Position sizing: balance={balance}, risk_amount={risk_amount:.2f}, "
            f"price_risk={price_risk:.5f}, lot_size={lot_size}"
        )
        
        return lot_size