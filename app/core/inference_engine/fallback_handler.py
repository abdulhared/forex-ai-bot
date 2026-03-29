# app/core/inference_engine/fallback_handler.py

from datetime import datetime, timezone
from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.monitoring.telegram_bot import TelegramBot
from app.shared.constants import LogCategory


class FallbackHandler:
    """
    Handles inference failures gracefully.
    Logs error, alerts operator, returns safe HOLD signal.
    """

    def __init__(self):
        self.logger = setup_logger()
        self.telegram = TelegramBot()

    def handle(self, error: Exception, pair: str) -> dict:
        """
        Handle a signal generation failure.

        Args:
            error: The exception that was caught
            pair:  Which pair failed inference

        Returns:
            Safe HOLD signal dict
        """
        # 1. Log the error
        self.logger.bind(category=LogCategory.ERROR.value).error(
            f"Inference failed for {pair}: {error}"
        )

        # 2. Alert operator via Telegram
        self.telegram.send_alert(
            f"⚠️ Inference failure on {pair}. Bot paused for new signals. Error: {error}"
        )

        # 3. Return safe HOLD signal
        return {
            "pair": pair,
            "action": "HOLD",
            "confidence": 0.0,        # zero confidence — model failed
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "lot_size": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": "fallback",  # signal that this came from fallback
        }