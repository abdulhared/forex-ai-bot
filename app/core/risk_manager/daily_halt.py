from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import DAILY_LOSS_LIMIT
from app.infrastructure.notifications.telegram_bot import TelegramBot


class DailyHalt:
    """
    Halts trading for the day if daily losses exceed limit.
    Resets automatically each day with new opening balance.
    """
    
    def __init__(self, telegram_bot: TelegramBot = None):
        """
        Initialize daily halt monitor.
        
        Args:
            telegram_bot: Optional TelegramBot instance for sending alerts
        """
        self.logger = setup_logger()
        self.opening_balance = None
        self.is_halted = False
        self.halt_date = None
        self.daily_loss_limit = DAILY_LOSS_LIMIT  # 0.05 = 5%
        self.telegram_bot = telegram_bot
    
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
            
            error_msg = (
                f"⚠️ DAILY HALT TRIGGERED ⚠️\n"
                f"Daily Loss: {daily_loss:.2%}\n"
                f"Limit: {self.daily_loss_limit:.2%}\n"
                f"Opening Balance: ${self.opening_balance:.2f}\n"
                f"Current Balance: ${current_balance:.2f}\n"
                f"Loss: ${self.opening_balance - current_balance:.2f}\n\n"
                f"Trading halted for the day. Will reset tomorrow."
            )
            
            self.logger.bind(category=LogCategory.ERROR.value).error(error_msg)
            
            # Send Telegram alert if bot is configured
            if self.telegram_bot:
                try:
                    self.telegram_bot.send_message(error_msg)
                except Exception as e:
                    self.logger.bind(category=LogCategory.ERROR.value).error(
                        f"Failed to send Telegram alert: {e}"
                    )
            else:
                self.logger.bind(category=LogCategory.WARNING.value).warning(
                    "No TelegramBot provided - alert not sent"
                )
            
            return True
        
        return False
    
    def get_daily_loss(self, current_balance):
        """
        Calculate current daily loss percentage without side effects.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            float: Daily loss percentage (e.g., 0.03 for 3% loss)
                   Returns 0.0 if opening_balance is None or invalid
                   Returns negative values if current_balance > opening_balance (profit)
        """
        if self.opening_balance is None:
            return 0.0
        
        if self.opening_balance <= 0:
            return 0.0
        
        daily_loss = (self.opening_balance - current_balance) / self.opening_balance
        
        return daily_loss
    
    def reset(self):
        """
        Manually reset daily halt (operator only).
        Useful for testing or emergency override.
        """
        self.is_halted = False
        self.opening_balance = None
        self.halt_date = None
        
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            "Daily halt manually reset"
        )
        
        # Optionally send notification on manual reset
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(
                    "🔄 Daily halt manually reset. Trading may resume."
                )
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram reset alert: {e}"
                )