from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import DAILY_LOSS_LIMIT


class DailyHalt:
    """
    Halts trading for the day if daily losses exceed limit.
    Resets automatically each day with new opening balance.
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.opening_balance = None
        self.is_halted = False
        self.halt_date = None
        self.daily_loss_limit = DAILY_LOSS_LIMIT  # 0.05 = 5%
    
    def set_opening_balance(self, balance, date):
        """
        Set the starting balance for the day. Resets halt for new day.
        
        Args:
            balance: Account balance at start of day
            date: Current date (YYYY-MM-DD string)
        """
        # Reset if this is a new day
        if self.halt_date != date:
            self.is_halted = False
            self.halt_date = date
        
        self.opening_balance = balance
        
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"Daily opening balance set: {balance:.2f} for {date}"
        )
    
    def check(self, current_balance, date):
        """
        Check if daily loss limit has been exceeded.
        
        Args:
            current_balance: Current account balance
            date: Current date (YYYY-MM-DD string)
            
        Returns:
            True if trading is halted, False if can continue
        """
        # If already halted today, return True
        if self.is_halted and self.halt_date == date:
            return True
        
        # Check if it's a new day (reset happened in set_opening_balance)
        if self.opening_balance is None or self.halt_date != date:
            # No opening balance set for today — allow trading
            return False
        
        # Calculate daily loss
        if self.opening_balance <= 0:
            return False
        
        daily_loss = (self.opening_balance - current_balance) / self.opening_balance
        
        # Check if loss exceeds limit
        if daily_loss >= self.daily_loss_limit:
            self.is_halted = True
            self.halt_date = date
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"DAILY HALT TRIGGERED - Loss {daily_loss:.2%} exceeded {self.daily_loss_limit:.2%}. "
                f"Opening: {self.opening_balance:.2f}, Current: {current_balance:.2f}"
            )
            return True
        
        return False