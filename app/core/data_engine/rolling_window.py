from collections import deque
from app.shared.config import ROLLING_WINDOW_SIZE
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class RollingWindow:
    """Maintains last N candles per pair/timeframe in memory for fast access"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.window_size = ROLLING_WINDOW_SIZE  # Default: 200
        
        # Nested dict: windows[pair][timeframe] = deque of candles
        self.windows = {}
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"RollingWindow initialized with size: {self.window_size}"
        )
    
    def add_candle(self, candle):
        """Add a completed candle to the rolling window"""
        pair = candle["pair"]
        timeframe = candle["timeframe"]
        
        # Initialize nested dict for this pair if needed
        if pair not in self.windows:
            self.windows[pair] = {}
        
        # Create deque for this timeframe if needed
        if timeframe not in self.windows[pair]:
            self.windows[pair][timeframe] = deque(maxlen=self.window_size)
        
        # Add candle (deque auto-removes oldest if at maxlen)
        self.windows[pair][timeframe].append(candle)
    
    def get_candles(self, pair, timeframe):
        """Get all candles for a pair/timeframe as a list (newest last)"""
        try:
            # Return as list (deque remains unchanged)
            return list(self.windows[pair][timeframe])
        except KeyError:
            # No candles yet for this pair/timeframe
            return []
    
    def get_latest_candle(self, pair, timeframe):
        """Get the most recent candle for a pair/timeframe"""
        try:
            return self.windows[pair][timeframe][-1]
        except (KeyError, IndexError):
            return None