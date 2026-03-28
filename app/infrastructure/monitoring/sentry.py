import sentry_sdk
from app.shared.config import SENTRY_DSN
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


def setup_sentry():
    """
    Initialize Sentry for error tracking and monitoring.
    
    Checks if SENTRY_DSN is configured in environment variables.
    If configured, initializes Sentry SDK to capture unhandled exceptions
    and send alerts. If not configured, logs a warning and continues
    gracefully without error tracking.
    """
    logger = setup_logger()
    
    if not SENTRY_DSN:
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            "SENTRY_DSN not configured — error tracking disabled. "
            "Set SENTRY_DSN in environment variables to enable Sentry monitoring."
        )
        return
    
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0
        )
        logger.bind(category=LogCategory.SYSTEM.value).info(
            "Sentry error tracking enabled"
        )
    
    except Exception as e:
        logger.bind(category=LogCategory.ERROR.value).error(
            f"Failed to initialize Sentry: {e} — error tracking disabled"
        )