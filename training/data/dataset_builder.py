# training/data/dataset_builder.py

import numpy as np
from app.core.feature_pipeline.indicators import Indicators
from app.core.feature_pipeline.price_action import PriceAction
from app.core.feature_pipeline.session_context import SessionContext
from app.core.feature_pipeline.normaliser import Normaliser
from app.core.feature_pipeline.vector_assembler import VectorAssembler
from app.shared.config import LOOKBACK_WINDOW
from app.infrastructure.monitoring.logger import setup_logger


class DatasetBuilder:
    """
    Pre-computes feature matrix from cleaned candles.
    Output: numpy array of shape [n_candles, 20]
    """

    def __init__(self):
        self.logger = setup_logger()
        self.indicators = Indicators()
        self.price_action = PriceAction()
        self.session_context = SessionContext()
        self.normaliser = Normaliser()
        self.assembler = VectorAssembler()

    def build(self, candles: list) -> np.ndarray:
        """
        Build feature matrix from cleaned candle list.

        Args:
            candles: Cleaned candle dicts, oldest first

        Returns:
            np.ndarray of shape [n_valid_candles, 20]
        """
        self.logger.info(f"Building feature matrix from {len(candles)} candles")

        feature_rows = []

        # Need LOOKBACK_WINDOW candles before we can compute features
        for i in range(LOOKBACK_WINDOW, len(candles)):

            # Slice the lookback window
            window = candles[i - LOOKBACK_WINDOW : i + 1]  # LOOKBACK_WINDOW candles + current

            try:
                # Run feature pipeline
                indicators = self.indicators.calculate(window)
                price_action = self.price_action.calculate(window)
                session = self.session_context.get_session(candles[i]["time"])
                raw_features = {**indicators, **price_action, **session}
                normalised = self.normaliser.normalise(raw_features, window)
                vector = self.assembler.assemble(normalised)

                feature_rows.append(vector)

            except Exception as e:
                # Skip candles where pipeline fails — log and continue
                self.logger.warning(f"Skipping candle {i}: {e}")
                continue

        matrix = np.array(feature_rows, dtype=np.float32)

        self.logger.info(f"Feature matrix shape: {matrix.shape}")
        return matrix

    def save(self, matrix: np.ndarray, path: str) -> None:
        """Save feature matrix to disk for reuse."""
        np.save(path, matrix)  # Fixed: path first, then matrix
        self.logger.info(f"Feature matrix saved to {path}")

    def load(self, path: str) -> np.ndarray:
        """Load pre-computed feature matrix from disk."""
        matrix = np.load(f"{path}.npy")
        self.logger.info(f"Feature matrix loaded: shape={matrix.shape}")
        return matrix