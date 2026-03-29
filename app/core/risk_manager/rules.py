from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import MAX_CONCURRENT_POSITIONS, MIN_MODEL_CONFIDENCE
from app.core.risk_manager.position_sizer import PositionSizer
from app.core.risk_manager.circuit_breaker import CircuitBreaker
from app.core.risk_manager.daily_halt import DailyHalt
from app.core.risk_manager.news_filter import NewsFilter


class RiskManager:
    """
    Master risk check combining all risk components.
    No trade passes without clearing every rule.
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.position_sizer = PositionSizer()
        self.circuit_breaker = CircuitBreaker()
        self.daily_halt = DailyHalt()
        self.news_filter = NewsFilter()
    
    def check_signal(self, signal, account_state, current_time):
        """
        Check if a signal should be executed.
        
        Args:
            signal: Signal dict with action, confidence, entry_price, stop_loss
            account_state: Dict with balance, open_positions
            current_time: Current datetime
            
        Returns:
            Dict with approved (bool), reason (str), and lot_size (float)
        """
        # 1. Check HOLD signal
        if signal.get("action") == "HOLD":
            return {"approved": False, "reason": "Signal is HOLD", "lot_size": 0}
        
        # 2. Check minimum confidence
        if signal.get("confidence", 0) < MIN_MODEL_CONFIDENCE:
            return {"approved": False, "reason": f"Confidence too low: {signal.get('confidence')}", "lot_size": 0}
        
        # 3. Check news window
        self.news_filter.clear_past_events(current_time)
        if self.news_filter.is_news_window(current_time):
            return {"approved": False, "reason": "News window active - trading blocked", "lot_size": 0}
        
        # 4. Check max concurrent positions
        if account_state.get("open_positions", 0) >= MAX_CONCURRENT_POSITIONS:
            return {"approved": False, "reason": f"Max positions reached ({MAX_CONCURRENT_POSITIONS})", "lot_size": 0}
        
        # 5. Update and check circuit breaker
        balance = account_state.get("balance", 0)
        if self.circuit_breaker.update(balance):
            return {"approved": False, "reason": "Circuit breaker triggered", "lot_size": 0}
        
        # 6. Check daily halt
        date_str = current_time.strftime("%Y-%m-%d")
        if self.daily_halt.check(balance, date_str):
            return {"approved": False, "reason": f"Daily loss limit reached for {date_str}", "lot_size": 0}
        
        # 7. Calculate position size
        entry_price = signal.get("entry_price", 0)
        stop_loss = signal.get("stop_loss", 0)
        lot_size = self.position_sizer.calculate(balance, entry_price, stop_loss)
        
        if lot_size <= 0:
            return {"approved": False, "reason": "Invalid lot size calculated", "lot_size": 0}
        
        # All checks passed
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"Signal approved: {signal.get('action')} {signal.get('pair')} lot_size={lot_size}"
        )
        
        return {"approved": True, "reason": "All risk checks passed", "lot_size": lot_size}
    
    def set_daily_opening_balance(self, balance, date):
        """Set daily opening balance (call at start of each trading day)"""
        self.daily_halt.set_opening_balance(balance, date)
    
    def add_news_event(self, event_time):
        """Add news event to block"""
        self.news_filter.add_event(event_time)
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (operator only)"""
        self.circuit_breaker.reset()