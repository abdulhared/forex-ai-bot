from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class Normaliser:
    """Scales feature values to [0, 1] range for AI model input"""
    
    # Fixed ranges for bounded features
    FEATURE_RANGES = {
        "rsi": (0, 100),
        "macd": (-0.01, 0.01),
        "macd_signal": (-0.01, 0.01),
        "body_ratio": (0, 1),
        "upper_wick_ratio": (0, 1),
        "lower_wick_ratio": (0, 1),
        "sydney": (0, 1),
        "tokyo": (0, 1),
        "london": (0, 1),
        "new_york": (0, 1),
    }
    
    def __init__(self):
        self.logger = setup_logger()
    
    def _scale(self, value, min_val, max_val):
        """Min-max scale with clipping to [0, 1]"""
        if max_val == min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    
    def normalise(self, features, candles):
        """
        Normalise all features to [0, 1] range.
        
        Args:
            features: Dictionary of raw feature values
            candles: List of candles for dynamic price range calculation
            
        Returns:
            Dictionary of normalised features
        """
        if not candles:
            self.logger.bind(category=LogCategory.SYSTEM.value).warning(
                "No candles provided for normalisation"
            )
            return features
        
        # Calculate price range from recent candles (last 200 or all)
        lookback = min(200, len(candles))
        recent_closes = [c["close"] for c in candles[-lookback:]]
        price_min = min(recent_closes)
        price_max = max(recent_closes)
        
        # Use current ATR doubled as the range ceiling
        atr_max = features.get("atr", 0.001) * 2
        
        normalised = {}
        
        for key, value in features.items():
            # Use fixed range if defined
            if key in self.FEATURE_RANGES:
                min_val, max_val = self.FEATURE_RANGES[key]
                normalised[key] = self._scale(value, min_val, max_val)
            
            # Price-based features
            elif key in ["ema9", "ema21", "ema50", "ema200", "bb_upper", "bb_mid", "bb_lower", "support", "resistance"]:
                normalised[key] = self._scale(value, price_min, price_max)
            
            # ATR feature
            elif key == "atr":
                normalised[key] = self._scale(value, 0, atr_max)
            
            # Unknown feature — log warning and pass through
            else:
                self.logger.bind(category=LogCategory.SYSTEM.value).warning(
                    f"Unknown feature '{key}' - no normalisation range defined"
                )
                normalised[key] = value
        
        return normalised