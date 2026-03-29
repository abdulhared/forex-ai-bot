from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class PriceAction:
    """Extracts candle shape features and support/resistance levels"""
    
    def __init__(self):
        self.logger = setup_logger()
    
    def calculate(self, candles):
        """
        Calculate price action features from candle list.
        
        Args:
            candles: List of candle dicts with open/high/low/close
            
        Returns:
            Dictionary of price action features
        """
        if not candles:
            return None
        
        # Get latest candle for shape analysis
        latest = candles[-1]
        
        # Calculate body and wick ratios
        body = abs(latest["close"] - latest["open"])
        total_range = latest["high"] - latest["low"]
        
        if total_range == 0:
            body_ratio = 0.0
            upper_wick_ratio = 0.0
            lower_wick_ratio = 0.0
        else:
            body_ratio = body / total_range
            upper_wick = latest["high"] - max(latest["open"], latest["close"])
            lower_wick = min(latest["open"], latest["close"]) - latest["low"]
            upper_wick_ratio = upper_wick / total_range
            lower_wick_ratio = lower_wick / total_range
        
        # Calculate support and resistance (last 50 candles)
        lookback = min(50, len(candles))
        recent_candles = candles[-lookback:]
        
        resistance = max(c["high"] for c in recent_candles)
        support = min(c["low"] for c in recent_candles)
        
        return {
            "body_ratio": round(body_ratio, 4),
            "upper_wick_ratio": round(upper_wick_ratio, 4),
            "lower_wick_ratio": round(lower_wick_ratio, 4),
            "support": round(support, 5),
            "resistance": round(resistance, 5)
        }