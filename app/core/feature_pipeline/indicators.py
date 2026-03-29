import pandas as pd
import pandas_ta as ta
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class Indicators:
    """Calculates technical indicators from candle data"""
    
    def __init__(self):
        self.logger = setup_logger()
    
    def calculate(self, candles):
        """
        Calculate all technical indicators from candle list.
        
        Args:
            candles: List of candle dicts with open/high/low/close/volume
            
        Returns:
            Dictionary of latest indicator values
        """
        if len(candles) < 200:  # Need enough data for EMA200
            self.logger.bind(category=LogCategory.SYSTEM.value).warning(
                f"Only {len(candles)} candles available. Need at least 200 for accurate indicators."
            )
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Calculate indicators
        df["rsi"] = ta.rsi(df["close"], length=14)
        
        # MACD returns DataFrame with MACD, MACD_signal, MACD_hist
        macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd_df is not None:
            df["macd"] = macd_df.iloc[:, 0]  # MACD line
            df["macd_signal"] = macd_df.iloc[:, 1]  # Signal line
        
        # Moving averages
        df["ema9"] = ta.ema(df["close"], length=9)
        df["ema21"] = ta.ema(df["close"], length=21)
        df["ema50"] = ta.ema(df["close"], length=50)
        df["ema200"] = ta.ema(df["close"], length=200)
        
        # ATR
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
        
        # Bollinger Bands (iloc[:, 0] = Lower, iloc[:, 1] = Mid, iloc[:, 2] = Upper)
        bb_df = ta.bbands(df["close"], length=20, std=2)
        if bb_df is not None:
            df["bb_lower"] = bb_df.iloc[:, 0]  # Lower band
            df["bb_mid"] = bb_df.iloc[:, 1]    # Middle band (SMA)
            df["bb_upper"] = bb_df.iloc[:, 2]  # Upper band
        
        # Get latest values
        latest = df.iloc[-1]
        
        return {
            "rsi": float(latest["rsi"]) if pd.notna(latest["rsi"]) else 50.0,
            "macd": float(latest["macd"]) if "macd" in latest and pd.notna(latest["macd"]) else 0.0,
            "macd_signal": float(latest["macd_signal"]) if "macd_signal" in latest and pd.notna(latest["macd_signal"]) else 0.0,
            "ema9": float(latest["ema9"]) if pd.notna(latest["ema9"]) else 0.0,
            "ema21": float(latest["ema21"]) if pd.notna(latest["ema21"]) else 0.0,
            "ema50": float(latest["ema50"]) if pd.notna(latest["ema50"]) else 0.0,
            "ema200": float(latest["ema200"]) if pd.notna(latest["ema200"]) else 0.0,
            "atr": float(latest["atr"]) if pd.notna(latest["atr"]) else 0.0,
            "bb_lower": float(latest["bb_lower"]) if "bb_lower" in latest and pd.notna(latest["bb_lower"]) else 0.0,
            "bb_mid": float(latest["bb_mid"]) if "bb_mid" in latest and pd.notna(latest["bb_mid"]) else 0.0,
            "bb_upper": float(latest["bb_upper"]) if "bb_upper" in latest and pd.notna(latest["bb_upper"]) else 0.0
        }