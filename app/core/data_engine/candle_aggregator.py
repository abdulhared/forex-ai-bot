from datetime import datetime, timezone
import math
from app.shared.config import TIMEFRAMES
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class CandleAggregator:
    """Builds OHLCV candles from clean ticks for multiple pairs and timeframes"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.timeframes = TIMEFRAMES  # e.g., ["M1", "M15", "H1", "H4"]
        
        # Nested dict: open_candles[pair][timeframe] = candle
        self.open_candles = {}
        
        # Callback for completed candles
        self.on_candle_close = None
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"CandleAggregator initialized for timeframes: {self.timeframes}"
        )
    
    def _parse_timestamp(self, timestamp_str):
        """Convert ISO timestamp to Unix seconds"""
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.timestamp()
    
    def _get_timeframe_seconds(self, timeframe):
        """Convert timeframe string to seconds"""
        return {
            "M1": 60,
            "M15": 900,
            "H1": 3600,
            "H4": 14400
        }[timeframe]
    
    def _emit_candle(self, candle):
        """Forward completed candle to callback"""
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"Candle closed: {candle['pair']} {candle['timeframe']} "
            f"O:{candle['open']} H:{candle['high']} L:{candle['low']} "
            f"C:{candle['close']} V:{candle['volume']}"
        )
        
        if self.on_candle_close:
            self.on_candle_close(candle)
    
    def process_tick(self, clean_tick):
        """Process a clean tick and update open candles"""
        pair = clean_tick["pair"]
        price = clean_tick["mid"]
        timestamp_str = clean_tick["timestamp"]
        
        # Convert timestamp to Unix seconds for boundary math
        tick_ts = self._parse_timestamp(timestamp_str)
        
        # Initialize nested dict for this pair if needed
        if pair not in self.open_candles:
            self.open_candles[pair] = {}
        
        # Process each timeframe
        for tf in self.timeframes:
            tf_seconds = self._get_timeframe_seconds(tf)
            
            # Calculate candle start boundary
            candle_start = math.floor(tick_ts / tf_seconds) * tf_seconds
            
            # Check if we have an open candle for this pair/timeframe
            if tf not in self.open_candles[pair]:
                # No candle yet — create first one
                self.open_candles[pair][tf] = {
                    "pair": pair,
                    "timeframe": tf,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 1,
                    "candle_start": candle_start
                }
            else:
                candle = self.open_candles[pair][tf]
                
                # Check if tick belongs to current candle
                if candle_start == candle["candle_start"]:
                    # Same candle — update
                    candle["high"] = max(candle["high"], price)
                    candle["low"] = min(candle["low"], price)
                    candle["close"] = price
                    candle["volume"] += 1
                else:
                    # New candle — emit old one, start new
                    self._emit_candle(candle)
                    
                    # Start new candle
                    self.open_candles[pair][tf] = {
                        "pair": pair,
                        "timeframe": tf,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": 1,
                        "candle_start": candle_start
                    }