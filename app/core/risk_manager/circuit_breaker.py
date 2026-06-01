from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import MAX_DRAWDOWN_LIMIT
from app.infrastructure.notifications.telegram_bot import TelegramBot


class CircuitBreaker:
    """
    Monitors drawdown and halts trading if losses exceed limit.
    Drawdown is measured from peak balance, not starting balance.
    """
    
    def __init__(self, telegram_bot: TelegramBot = None):
        """
        Initialize circuit breaker.
        
        Args:
            telegram_bot: Optional TelegramBot instance for sending alerts
        """
        self.logger = setup_logger()
        self.peak_balance = None
        self.is_triggered = False
        self.max_drawdown = MAX_DRAWDOWN_LIMIT  # 0.10 = 10%
        self.telegram_bot = telegram_bot
    
    def update(self, current_balance):
        """
        Update peak balance and check if drawdown exceeds limit.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if circuit breaker triggered, False otherwise
        """
        if self.is_triggered:
            return True
        
        # Initialize peak on first update
        if self.peak_balance is None:
            self.peak_balance = current_balance
            return False
        
        # Update peak if current balance is higher
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            return False
        
        # Calculate drawdown from peak
        drawdown = (self.peak_balance - current_balance) / self.peak_balance
        
        # Check if drawdown exceeds limit
        if drawdown >= self.max_drawdown:
            self.is_triggered = True
            error_msg = (
                f"⚠️ CIRCUIT BREAKER TRIGGERED ⚠️\n"
                f"Drawdown: {drawdown:.2%}\n"
                f"Limit: {self.max_drawdown:.2%}\n"
                f"Peak Balance: ${self.peak_balance:.2f}\n"
                f"Current Balance: ${current_balance:.2f}\n"
                f"Loss: ${self.peak_balance - current_balance:.2f}\n\n"
                f"Trading has been halted. Manual reset required."
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
    
    def get_drawdown(self, current_balance):
        """
        Calculate current drawdown percentage from peak without side effects.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            float: Drawdown percentage (e.g., 0.05 for 5% drawdown)
                   Returns 0.0 if peak_balance is None or invalid
        """
        if self.peak_balance is None:
            return 0.0
        
        if self.peak_balance <= 0:
            return 0.0
        
        drawdown = (self.peak_balance - current_balance) / self.peak_balance
        
        # Ensure non-negative return (no negative drawdown when balance > peak)
        return max(0.0, drawdown)
    
    def reset(self):
        """Manually reset circuit breaker (operator only)"""
        self.is_triggered = False
        self.peak_balance = None
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            "Circuit breaker manually reset"
        )
        
        # Optionally send notification on manual reset
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(
                    "🔄 Circuit breaker manually reset. Trading may resume."
                )
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram reset alert: {e}"
                )