from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class TickProcessor:
    """Converts raw OANDA ticks to clean mid-price ticks"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.on_candle_tick = None  # Callback for candle aggregator
    
    def process(self, raw_tick):
        """Process raw tick, extract mid price, and forward to callback"""
        
        # Ignore heartbeat and other non-price messages
        if raw_tick.get("type") != "PRICE":
            return
        
        try:
            # Extract data from raw tick
            pair = raw_tick["instrument"]
            timestamp = raw_tick["time"]
            
            # Parse bid and ask from first price level
            bid = float(raw_tick["bids"][0]["price"])
            ask = float(raw_tick["asks"][0]["price"])
            
            # Calculate mid price (fair value)
            mid = (bid + ask) / 2
            
            # Build clean tick dictionary
            clean_tick = {
                "pair": pair,
                "timestamp": timestamp,
                "bid": bid,
                "ask": ask,
                "mid": mid
            }
            
            # Forward to candle aggregator if registered
            if self.on_candle_tick:
                self.on_candle_tick(clean_tick)
                
        except (KeyError, IndexError, ValueError) as e:
            # Log malformed ticks but don't crash
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Failed to process tick: {e} | Raw tick: {raw_tick}"
            )