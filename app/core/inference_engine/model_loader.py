# app/core/inference_engine/model_loader.py

import torch
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class ModelLoader:
    """
    Loads and holds a PyTorch PPO model in memory.
    Call load() once at startup. Access model via .model property.
    """

    def __init__(self):
        self.logger = setup_logger()
        self.model = None
        self.version = None

    def load(self, model_path: str, model_version: str) -> bool:
        """
        Load a PyTorch model from disk into memory.

        Args:
            model_path:    Path to the .pt file
            model_version: Version string for logging and signal schema

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # 1. Load model from disk (force CPU — no GPU on free tier)
            self.model = torch.load(
                model_path,
                map_location="cpu"
            )

            # 2. Switch to evaluation mode
            self.model.eval()

            # 3. Store version
            self.version = model_version

            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"Model loaded: version={model_version} path={model_path}"
            )
            return True

        except Exception as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Failed to load model from {model_path}: {e}"
            )
            self.model = None
            self.version = None
            return False

    def is_ready(self) -> bool:
        """Return True if model is loaded and ready for inference."""
        return self.model is not None