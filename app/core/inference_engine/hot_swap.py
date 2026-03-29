# app/core/inference_engine/hot_swap.py

import threading
import torch
from app.core.inference_engine.model_loader import ModelLoader
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class HotSwap:
    """
    Replaces the live model without restarting the bot.
    Uses a thread lock to prevent race conditions during swap.
    """

    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.logger = setup_logger()
        self._lock = threading.Lock()  # Simple mutex — sufficient for this use case

    def swap(self, new_model_path: str, new_version: str) -> bool:
        """
        Load a new model and swap it in atomically.

        Args:
            new_model_path: Path to new .pt file
            new_version:    Version string for the new model

        Returns:
            True if swap succeeded, False otherwise
        """
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"Hot swap initiated: {self.model_loader.version} → {new_version}"
        )

        try:
            # 1. Load new model BEFORE acquiring lock
            #    (loading takes time — don't block inference while loading)
            new_model = torch.load(new_model_path, map_location="cpu")
            new_model.eval()

            # 2. Acquire lock and swap atomically
            with self._lock:
                self.model_loader.model = new_model
                self.model_loader.version = new_version

            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"Hot swap complete: version={new_version}"
            )
            return True

        except Exception as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Hot swap failed for {new_model_path}: {e}"
            )
            return False