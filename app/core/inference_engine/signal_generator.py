# app/core/inference_engine/signal_generator.py

import torch
from datetime import datetime, timezone
from app.core.inference_engine.model_loader import ModelLoader
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory

ACTION_MAP = {0: "BUY", 1: "HOLD", 2: "SELL"}


class SignalGenerator:
    """
    Runs feature vector through PPO model.
    Produces a signal dict matching SignalSchema.
    """

    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.logger = setup_logger()

    def generate(self, features: list, pair: str,
                 stop_loss: float, take_profit: float) -> dict:
        """
        Run inference on a feature vector.

        Args:
            features:    20-element list of floats
            pair:        Instrument string e.g. "EUR_USD"
            stop_loss:   Pre-calculated stop loss price
            take_profit: Pre-calculated take profit price

        Returns:
            Signal dict matching SignalSchema fields
        """
        # 1. Convert feature list to tensor with batch dimension
        tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)

        # 2. Run inference — no gradient tracking needed
        with torch.no_grad():
            logits = self.model_loader.model(tensor)
            probs = torch.softmax(logits, dim=1)

        # 3. Extract action and confidence
        action_index = torch.argmax(probs, dim=1).item()
        confidence = probs[0][action_index].item()
        action = ACTION_MAP[action_index]

        # 4. Build signal dict
        signal = {
            "pair": pair,
            "action": action,
            "confidence": round(confidence, 4),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "lot_size": 0.0,   # filled later by risk manager
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": self.model_loader.version,
        }

        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"Signal: {action} {pair} confidence={confidence:.2%}"
        )

        return signal