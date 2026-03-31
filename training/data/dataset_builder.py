# training/data/dataset_builder.py

import numpy as np
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from app.core.feature_pipeline.session_context import SessionContext
from app.core.feature_pipeline.normaliser import Normaliser
from app.core.feature_pipeline.vector_assembler import VectorAssembler
from app.infrastructure.monitoring.logger import setup_logger


class DatasetBuilder:
    """
    Pre-computes feature matrix from cleaned candles.
    Output: numpy array of shape [n_candles, 20]
    """

    FEATURE_LOOKBACK = 200

    def __init__(self):
        self.logger = setup_logger()
        self.session_context = SessionContext()
        self.normaliser = Normaliser()
        self.assembler = VectorAssembler()

    def _flatten_candle(self, candle: dict) -> dict:
        """Convert nested OANDA-format candle to flat format."""
        return {
            "open":   float(candle["mid"]["o"]),
            "high":   float(candle["mid"]["h"]),
            "low":    float(candle["mid"]["l"]),
            "close":  float(candle["mid"]["c"]),
            "volume": int(candle["volume"]),
            "time":   candle["time"]
        }

    def _compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all technical indicators once on full DataFrame."""
        df["ema9"] = ta.ema(df["close"], length=9)
        df["ema21"] = ta.ema(df["close"], length=21)
        df["ema50"] = ta.ema(df["close"], length=50)
        df["ema200"] = ta.ema(df["close"], length=200)
        
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df["macd"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]
        
        df["rsi"] = ta.rsi(df["close"], length=14)
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
        
        bbands = ta.bbands(df["close"], length=20, std=2)
        df["bb_upper"] = bbands.iloc[:, 2]
        df["bb_mid"] = bbands.iloc[:, 1]
        df["bb_lower"] = bbands.iloc[:, 0]
        
        return df

    def _compute_price_action(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute price action features using vectorized operations."""
        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]
        df["body_ratio"] = (df["body"] / df["range"].replace(0, np.nan)).fillna(0)
        df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
        df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
        df["upper_wick_ratio"] = (df["upper_wick"] / df["range"].replace(0, np.nan)).fillna(0)
        df["lower_wick_ratio"] = (df["lower_wick"] / df["range"].replace(0, np.nan)).fillna(0)
        df["support"] = df["low"].rolling(window=50, min_periods=1).min()
        df["resistance"] = df["high"].rolling(window=50, min_periods=1).max()
        
        return df

    def build(self, candles: list) -> np.ndarray:
        """Build feature matrix from cleaned candle list."""
        self.logger.info(f"Building feature matrix from {len(candles)} candles")

        # Flatten and create DataFrame
        flat_candles = [self._flatten_candle(c) for c in candles]
        df = pd.DataFrame(flat_candles)
        df["time"] = pd.to_datetime(df["time"])
        
        # Compute all features (vectorized)
        self.logger.info("Computing indicators...")
        df = self._compute_indicators(df)
        
        self.logger.info("Computing price action...")
        df = self._compute_price_action(df)
        
        # Drop NaN rows
        df = df.dropna()
        self.logger.info(f"Valid rows after feature calc: {len(df)}")
        
        # Pre-compute sessions using vectorized operations
        hours = df["time"].dt.hour
        df["sydney"] = ((hours >= 21) | (hours < 6)).astype(int)
        df["tokyo"] = ((hours >= 0) & (hours < 9)).astype(int)
        df["london"] = ((hours >= 7) & (hours < 16)).astype(int)
        df["new_york"] = ((hours >= 12) & (hours < 21)).astype(int)
        
        # Extract all features into numpy array for fast access
        feature_cols = [
            "rsi", "macd", "macd_signal", "ema9", "ema21", "ema50", "ema200",
            "atr", "bb_upper", "bb_mid", "bb_lower",
            "body_ratio", "upper_wick_ratio", "lower_wick_ratio",
            "support", "resistance",
            "sydney", "tokyo", "london", "new_york"
        ]
        data = df[feature_cols].values
        closes = df["close"].values  # For normaliser price range
        
        feature_rows = []
        start_idx = self.FEATURE_LOOKBACK
        
        # Fast loop — no DataFrame slicing, just numpy array access
        for i in range(start_idx, len(data)):
            try:
                # Get window of closes for normaliser (last 200 or fewer)
                window_start = max(0, i - self.FEATURE_LOOKBACK)
                window_closes = closes[window_start:i+1]
                
                # Build raw features dict from numpy row
                row_data = data[i]
                raw_features = dict(zip(feature_cols, row_data))
                
                # Normalise (pass closes list instead of candle dicts)
                normalised = self.normaliser.normalise(raw_features, [{"close": c} for c in window_closes])
                vector = self.assembler.assemble(normalised)
                feature_rows.append(vector)

            except Exception as e:
                self.logger.warning(f"Skipping row {i}: {e}")
                continue

        matrix = np.array(feature_rows, dtype=np.float32)
        self.logger.info(f"Feature matrix shape: {matrix.shape}")
        return matrix

    def save(self, matrix: np.ndarray, path: str) -> None:
        np.save(path, matrix)
        self.logger.info(f"Feature matrix saved to {path}")

    def load(self, path: str) -> np.ndarray:
        matrix = np.load(f"{path}.npy")
        self.logger.info(f"Feature matrix loaded: shape={matrix.shape}")
        return matrix