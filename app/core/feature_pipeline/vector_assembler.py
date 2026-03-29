import numpy as np
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class VectorAssembler:
    """Combines all features into a single NumPy array for the AI model"""
    
    # Define the exact order of features (must match model's training order)
    FEATURE_ORDER = [
        "rsi", "macd", "macd_signal",
        "ema9", "ema21", "ema50", "ema200",
        "atr", "bb_upper", "bb_mid", "bb_lower",
        "body_ratio", "upper_wick_ratio", "lower_wick_ratio",
        "support", "resistance",
        "sydney", "tokyo", "london", "new_york"
    ]
    
    def __init__(self):
        self.logger = setup_logger()
    
    def assemble(self, normalised_features):
        """
        Convert normalised features dictionary to NumPy array.
        
        Args:
            normalised_features: Dictionary of normalised feature values
            
        Returns:
            NumPy array of features in fixed order
        """
        feature_vector = []
        
        for key in self.FEATURE_ORDER:
            value = normalised_features.get(key, 0.0)
            feature_vector.append(value)
        
        return np.array(feature_vector, dtype=np.float32)