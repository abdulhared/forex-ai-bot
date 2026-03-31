from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import MAX_DRAWDOWN_LIMIT


class CircuitBreaker:
    """
    Monitors drawdown and halts trading if losses exceed limit.
    Drawdown is measured from peak balance, not starting balance.
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.peak_balance = None
        self.is_triggered = False
        self.max_drawdown = MAX_DRAWDOWN_LIMIT  # 0.10 = 10%
    
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
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"CIRCUIT BREAKER TRIGGERED - Drawdown {drawdown:.2%} exceeded {self.max_drawdown:.2%}. "
                f"Peak: {self.peak_balance:.2f}, Current: {current_balance:.2f}"
            )
            return True
        
        return False
    
    def reset(self):
        """Manually reset circuit breaker (operator only)"""
        self.is_triggered = False
        self.peak_balance = None
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            "Circuit breaker manually reset"
        )